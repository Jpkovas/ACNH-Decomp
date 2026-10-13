#include "acnh_research/flag_int.hpp"
static_assert(sizeof(unsigned)==4 && sizeof(int)==4);
extern "C" unsigned acnh_flag_int_predicate(unsigned value, int border, unsigned type) noexcept {
    const unsigned limit=static_cast<unsigned>(border);
    switch(type) {
    case 0: return value!=limit;
    case 1: return value==limit;
    case 2: return value<=limit;
    case 3: return value<limit;
    case 4: return value>=limit;
    case 5: return value>limit;
    case 6: {
        int count=0;
        for(unsigned bits=value;bits;bits>>=1)count+=static_cast<int>(bits&1u);
        return count<border;
    }
    default: return 0;
    }
}
namespace acnh_research {
unsigned flag_int_query(const char* key, int border, unsigned type, FlagReader reader, void* context) {
    // Preserve the order of the observed handler: fetch precedes type dispatch.
    return acnh_flag_int_predicate(reader(context,key),border,type);
}
}
