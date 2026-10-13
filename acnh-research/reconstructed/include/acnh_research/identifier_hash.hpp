#pragma once
// Observed ABI: NUL-terminated readable byte string in x0, seed in w1, result in w0.
// Precondition: input points to a readable terminated string shorter than 2^32 bytes.
extern "C" unsigned acnh_murmur3_cstr(const char* input, unsigned seed) noexcept;
