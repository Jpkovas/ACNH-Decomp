#pragma once
// Terminal predicate checked independently in 1.0.0 (0x7100406390)
// and 3.0.3 (0x7100f183d0).
// The original parameter declaration and backend are not recovered.
extern "C" unsigned acnh_flag_int_predicate(unsigned value, int border, unsigned check_type) noexcept;
namespace acnh_research {
using FlagReader = unsigned (*)(void* context, const char* access_key);
// Injected reader replaces parsing the access-key namespace and Switch SaveIO.
// Preconditions: readable access_key and valid reader/context for that reader.
unsigned flag_int_query(const char* access_key, int border, unsigned check_type,
                        FlagReader reader, void* context);
}
