#include "acnh_research/npad_full_key.hpp"
#include <algorithm>
#include <atomic>
#include <cstring>

extern "C" std::uint32_t acnh_npad_full_key_states(
    std::int32_t* written, acnh_research::NpadFullKeyState* states,
    std::int32_t capacity, const void* entry, const volatile std::uint32_t* filter_mode,
    const volatile std::uint8_t* filter_enabled, acnh_research::NpadReadHook before_read,
    void* read_context) noexcept {
    if (!entry) return 0x58ccau;
    const auto* bytes = static_cast<const unsigned char*>(entry);
    auto acquire = [&](std::size_t offset) {
        auto* address = reinterpret_cast<std::uint64_t*>(const_cast<unsigned char*>(bytes + offset));
        if (before_read) before_read(read_context, reinterpret_cast<std::uintptr_t>(address));
        return std::atomic_ref<std::uint64_t>(*address).load(std::memory_order_acquire);
    };
    auto count = static_cast<std::int32_t>(acquire(0x40));
    count = std::min(std::max(count, 0), capacity);
    auto tail = static_cast<std::int32_t>(acquire(0x38));
    if (count < 1) { *written = count; return 0; }
    for (;;) {
        bool consistent = true;
        auto slot = (tail + 18 - count) % 17;
        for (auto destination = count - 1; destination >= 0; --destination) {
            const auto offset = std::size_t(slot) * 0x30 + 0x48;
            const auto stamp = acquire(offset);
            std::memcpy(&states[destination], bytes + offset + 8, sizeof states[destination]);
            if (stamp != acquire(offset) || (destination + 1 < count &&
                states[destination].sampling_number - states[destination + 1].sampling_number != 1)) {
                consistent = false;
                break;
            }
            slot = (slot + 1) % 17;
        }
        if (consistent) break;
        // Original retry policy retains the requested snapshot size when the
        // producer's count shrinks, and grows it only up to caller capacity.
        count = std::min(std::max(count, static_cast<std::int32_t>(acquire(0x40))), capacity);
        tail = static_cast<std::int32_t>(acquire(0x38));
    }
    *written = count;
    for (std::int32_t i = 0; i < count; ++i) {
        if (before_read) before_read(read_context, reinterpret_cast<std::uintptr_t>(filter_mode));
        const auto mode = *filter_mode;
        if (before_read) before_read(read_context, reinterpret_cast<std::uintptr_t>(filter_enabled));
        const auto enabled = *filter_enabled;
        if (mode == 0 && enabled != 0) {
            auto& buttons = states[i].buttons;
            if (buttons & 0x2000) buttons &= ~std::uint64_t(0x8000);
            if (buttons & 0x1000) buttons &= ~std::uint64_t(0x4000);
        }
    }
    return 0;
}
