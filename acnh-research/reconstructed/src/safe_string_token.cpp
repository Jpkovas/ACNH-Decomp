#include "acnh_research/safe_string_token.hpp"

#include <cstddef>
#include <cstring>

namespace {
constexpr std::size_t scan_last_offset = 0x80000;

// The original scans triples of bytes. Its final triple includes offset 0x80000; exhausting the scan returns zero.
std::int32_t bounded_length(const char* text) noexcept {
    for (std::size_t offset = 0; offset <= scan_last_offset; ++offset) {
        if (text[offset] == '\0') return static_cast<std::int32_t>(offset);
    }
    return 0;
}

bool contains_delimiter(const char* delimiters, char value) noexcept {
    for (std::size_t offset = 0; offset <= scan_last_offset; ++offset) {
        if (delimiters[offset] == '\0') return false;
        if (delimiters[offset] == value) return true;
    }
    return false;
}
}

extern "C" std::int32_t acnh_safe_string_copy_token(const char* source, std::int32_t index,
                                                  const char* delimiters, char* output,
                                                  std::int32_t capacity, const char* empty_string) noexcept {
    const auto first_length = bounded_length(source);
    std::int32_t token_length = -1;
    if (index >= 0 && index <= first_length) {
        std::int32_t end = index;
        while (source[end] != '\0' && !contains_delimiter(delimiters, source[end])) ++end;
        token_length = end - index;
    }

    // The original obtains the source length a second time after scanning the token.
    const auto second_length = bounded_length(source);
    const char* selected_source = index < 0 || index > second_length ? empty_string : source + index;
    if (output == selected_source) return 0;
    if (token_length < 0) token_length = bounded_length(selected_source);

    const auto copied = token_length < capacity ? token_length : capacity - 1;
    std::memcpy(output, selected_source, static_cast<std::size_t>(copied));
    output[copied] = '\0';
    return copied;
}
