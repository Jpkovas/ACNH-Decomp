#include "acnh_research/bcsv.hpp"
#include "acnh_research/pilot_flow.hpp"
#include "acnh_research/constant_zero.hpp"
#include "acnh_research/identifier_hash.hpp"
#include "acnh_research/flag_int.hpp"
#include <iostream>
#include <stdexcept>
#include <string>
static void check(bool yes){if(!yes)throw std::runtime_error("contract assertion failed");}
template<typename F>static void rejects(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}check(caught);}
struct Services:acnh_research::FlowServices {
    std::int32_t result{};int queries{},changes{};std::string state;
    std::int32_t access_flag(std::string_view key)override{check(key=="cLandTemp:DocReturnFromIsland");++queries;return result;}
    void change_state(std::string_view s,bool same,bool previous)override{check(!same&&previous);++changes;state=s;}
};
int main(){
    using namespace acnh_research;
    int object=17;
    check(acnh_constant_zero(nullptr)==0);check(acnh_constant_zero(&object)==0);
    check(acnh_constant_zero(reinterpret_cast<void*>(std::uintptr_t(1)))==0);
    check(acnh_murmur3_cstr("",0)==0);
    check(acnh_murmur3_cstr("hello",0)==613153351u);
    check(acnh_murmur3_cstr("foo\0ignored",0)==acnh_murmur3_cstr("foo",0));
    check(acnh_flag_int_predicate(3,3,0)==0);
    check(acnh_flag_int_predicate(3,3,1)==1);
    check(acnh_flag_int_predicate(0xffffffffu,-1,1)==1);
    check(acnh_flag_int_predicate(0, -1,3)==1); // unsigned border in modes 0..5
    check(acnh_flag_int_predicate(0xffffffffu,33,6)==1);
    check(acnh_flag_int_predicate(0xffffffffu,32,6)==0);
    check(acnh_flag_int_predicate(0,-1,6)==0); // signed border in population-count mode
    check(acnh_flag_int_predicate(0,1,7)==0);
    unsigned reads=0;
    auto reader=[](void* context,const char* key)->unsigned {check(std::string(key)=="synthetic:key");++*static_cast<unsigned*>(context);return 3;};
    check(flag_int_query("synthetic:key",3,1,reader,&reads)==1&&reads==1);
    check(flag_int_query("synthetic:key",3,0xffffffffu,reader,&reads)==0&&reads==2);
    std::vector<std::uint8_t> valid={1,0,0,0,4,0,0,0,1,0,0,1,0x44,0x33,0x22,0x11,0,0,0,0,0xff,0xff,0xff,0xff};
    BcsvView table(valid);check(table.rows()==1&&table.stride()==4&&table.unsigned32(0,0x11223344)==0xffffffffu);
    rejects([&]{table.field(1,0x11223344);});rejects([&]{table.field(0,5);});
    for(std::size_t n=0;n<valid.size();++n)rejects([&]{BcsvView bad(std::span(valid).first(n));});
    auto corrupt=valid;corrupt[10]=2;rejects([&]{BcsvView bad(corrupt);});
    corrupt=valid;corrupt[16]=4;rejects([&]{BcsvView bad(corrupt);});
    corrupt=valid;corrupt[0]=0xff;corrupt[1]=0xff;corrupt[2]=0xff;corrupt[3]=0xff;rejects([&]{BcsvView bad(corrupt);});
    std::vector<std::uint8_t> empty(12);BcsvView empty_table(empty);check(empty_table.rows()==0);
    std::vector<std::uint8_t> v1={1,0,0,0,4,0,0,0,1,0,1,1,'V','S','C','B',0,0,0,0,0,0,0,0,0,0,0,0};
    v1.insert(v1.end(),valid.begin()+12,valid.end());BcsvView newer(v1);check(newer.unsigned32(0,0x11223344)==0xffffffffu);
    const std::string known="123456789";check(crc32(std::span(reinterpret_cast<const std::uint8_t*>(known.data()),known.size()))==0xcbf43926u);
    for(int result:{0,1,-1,2}){Services service;service.result=result;const bool ok=airport_flow(service);
        check(service.queries==1);check(ok==(result==0||result==1));check(service.changes==(ok?1:0));
        if(ok)check(service.state==(result==0?"cDocReturn":"cWait"));}
    std::cout<<"BCSV normal, truncated, invalid, empty, VSCB, CRC and EventFlow branch contracts passed\n";
}
