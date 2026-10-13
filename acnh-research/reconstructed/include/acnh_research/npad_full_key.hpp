#pragma once
#include <cstdint>

namespace acnh_research {
// SDK 1.0.0 FullKey state payload: the guest uses this byte layout.
struct NpadFullKeyState {
    std::uint64_t sampling_number;
    std::uint64_t buttons;
    std::int32_t left_x, left_y, right_x, right_y;
    std::uint32_t attributes, reserved;
};
static_assert(sizeof(NpadFullKeyState) == 0x28);
// Optional observation hook for deterministic producer-race replay in tests.
using NpadReadHook = void (*)(void* context, std::uintptr_t address);
}

// entry points to the SDK's selected Npad entry. Initialization and device
// selection are performed by the caller. Missing entry leaves outputs intact.
extern "C" std::uint32_t acnh_npad_full_key_states(
    std::int32_t* written, acnh_research::NpadFullKeyState* states,
    std::int32_t capacity, const void* entry, const volatile std::uint32_t* filter_mode,
    const volatile std::uint8_t* filter_enabled, acnh_research::NpadReadHook before_read,
    void* read_context) noexcept;
