#pragma once
#include <cstdint>
#include <string_view>
namespace acnh_research {
// Observed graph contract; the AccessKey query implementation is an injected service.
struct FlowServices {
    virtual ~FlowServices() = default;
    virtual std::int32_t access_flag(std::string_view key) = 0;
    virtual void change_state(std::string_view state, bool change_same, bool change_previous) = 0;
};
bool airport_flow(FlowServices& services);
}
