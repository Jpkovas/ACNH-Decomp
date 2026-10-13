#pragma once

#include <cstdint>

// Semantic contract recovered from ACNH 1.0.0 main+0x6b6c0..0x6b984.
// The original iterator and BufferString object layouts remain a separate ABI concern.
// SafeString callbacks must leave the source and delimiter data unchanged. Capacity is positive and includes NUL.
// Source and delimiters must remain readable through their terminating NUL, or through offset 0x80000 when their
// bounded length/membership scans exhaust. The token walk itself continues to a delimiter or NUL without that cap.
// The source's token walk must fit signed 32-bit length arithmetic. empty_string points to a readable zero byte.
// Output must be writable for capacity bytes and must not overlap the selected source, except exact pointer alias.
// Exact output/selected-source alias returns zero without writing. Invalid indices select empty_string.
// The iterator position is not advanced. Returns the number of bytes copied, excluding the terminating NUL.
extern "C" std::int32_t acnh_safe_string_copy_token(const char* source, std::int32_t index,
                                                  const char* delimiters, char* output,
                                                  std::int32_t capacity, const char* empty_string) noexcept;
