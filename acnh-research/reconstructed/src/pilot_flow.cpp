#include "acnh_research/pilot_flow.hpp"
namespace acnh_research {
bool airport_flow(FlowServices& services) {
    const auto value=services.access_flag("cLandTemp:DocReturnFromIsland");
    if(value==0)services.change_state("cDocReturn",false,true);
    else if(value==1)services.change_state("cWait",false,true);
    else return false;
    return true;
}
}
