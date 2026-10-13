#include "acnh_research/bcsv.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    try {
        std::ifstream in(argv[1],std::ios::binary);
        if(!in)throw std::runtime_error("cannot read input");
        std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(in)),{});
        acnh_research::BcsvView table(bytes);
        std::cout<<table.rows()<<" "<<table.stride()<<" "<<table.fields().size()<<"\n";
        for(auto f:table.fields()) {
            std::vector<std::uint8_t> joined;
            for(std::uint32_t row=0;row<table.rows();++row){auto cell=table.field(row,f.key);joined.insert(joined.end(),cell.begin(),cell.end());}
            std::cout<<f.key<<" "<<f.offset<<" "<<f.size<<" "<<acnh_research::crc32(joined)<<"\n";
        }
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
