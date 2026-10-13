#include "acnh_research/bcsv.hpp"
#include <algorithm>
#include <stdexcept>
namespace acnh_research {
static std::uint32_t little32(std::span<const std::uint8_t> bytes, std::size_t at) {
    if(at > bytes.size() || bytes.size()-at < 4) throw std::invalid_argument("truncated integer");
    return std::uint32_t(bytes[at]) | (std::uint32_t(bytes[at+1])<<8) |
           (std::uint32_t(bytes[at+2])<<16) | (std::uint32_t(bytes[at+3])<<24);
}
BcsvView::BcsvView(std::span<const std::uint8_t> bytes): bytes_(bytes) {
    if(bytes.size()<12) throw std::invalid_argument("truncated BCSV header");
    rows_=little32(bytes,0); stride_=little32(bytes,4);
    auto count=std::uint32_t(bytes[8]) | (std::uint32_t(bytes[9])<<8);
    std::size_t header=12;
    if(bytes[10]==1) {
        header=28;
        if(bytes.size()<header || little32(bytes,12)!=0x42435356u) throw std::invalid_argument("invalid VSCB header");
    } else if(bytes[10]!=0) throw std::invalid_argument("unsupported BCSV version");
    data_offset_=header+std::size_t(count)*8;
    if(data_offset_>bytes.size() || std::uint64_t(rows_)*stride_>bytes.size()-data_offset_)
        throw std::invalid_argument("truncated BCSV data");
    for(std::uint32_t i=0;i<count;++i) {
        auto key=little32(bytes,header+std::size_t(i)*8);
        auto offset=little32(bytes,header+std::size_t(i)*8+4);
        if(offset>=stride_ || (!fields_.empty() && offset<=fields_.back().offset))
            throw std::invalid_argument("invalid field offsets");
        if(std::any_of(fields_.begin(),fields_.end(),[key](const Field& f){return f.key==key;}))
            throw std::invalid_argument("duplicate field hash");
        fields_.push_back({key,offset,0});
    }
    for(std::size_t i=0;i<fields_.size();++i)
        fields_[i].size=(i+1<fields_.size()?fields_[i+1].offset:stride_)-fields_[i].offset;
}
std::span<const std::uint8_t> BcsvView::field(std::uint32_t row,std::uint32_t key) const {
    if(row>=rows_) throw std::out_of_range("BCSV row out of bounds");
    auto it=std::find_if(fields_.begin(),fields_.end(),[key](const Field& f){return f.key==key;});
    if(it==fields_.end()) throw std::out_of_range("BCSV field absent");
    auto at=data_offset_+std::size_t(row)*stride_+it->offset;
    return bytes_.subspan(at,it->size);
}
std::uint32_t BcsvView::unsigned32(std::uint32_t row,std::uint32_t key) const {return little32(field(row,key),0);}
std::uint32_t crc32(std::span<const std::uint8_t> bytes) {
    std::uint32_t crc=0xffffffffu;
    for(auto byte:bytes){crc^=byte;for(int i=0;i<8;++i)crc=(crc>>1)^(0xedb88320u & (0u-(crc&1u)));}
    return ~crc;
}
}
