#include "acnh_research/identifier_hash.hpp"
static_assert(sizeof(unsigned)==4);
static unsigned rotate_left(unsigned value,unsigned shift) noexcept {
    return (value<<shift)|(value>>(32-shift));
}
extern "C" unsigned acnh_murmur3_cstr(const char* input,unsigned seed) noexcept {
    const auto* bytes=reinterpret_cast<const unsigned char*>(input);
    unsigned length=0;
    while(bytes[length]!=0)++length;
    unsigned position=0;
    unsigned hash=seed;
    while(length-position>=4) {
        unsigned word=unsigned(bytes[position])|(unsigned(bytes[position+1])<<8)|
                      (unsigned(bytes[position+2])<<16)|(unsigned(bytes[position+3])<<24);
        word=rotate_left(word*0xcc9e2d51u,15)*0x1b873593u;
        hash=rotate_left(hash^word,13)*5u+0xe6546b64u;
        position+=4;
    }
    unsigned tail=0;
    for(unsigned i=0;i<length-position;++i)tail|=unsigned(bytes[position+i])<<(8*i);
    if(length!=position)hash^=rotate_left(tail*0xcc9e2d51u,15)*0x1b873593u;
    hash^=length;
    hash^=hash>>16;hash*=0x85ebca6bu;
    hash^=hash>>13;hash*=0xc2b2ae35u;
    return hash^(hash>>16);
}
