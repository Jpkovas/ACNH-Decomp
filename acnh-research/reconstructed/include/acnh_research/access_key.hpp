#pragma once

// Semantic contract recovered from main+0x216670 in ACNH 1.0.0.
// These are research interfaces; the original SafeString declarations are unknown.
// Input must be NUL-terminated below 2^19 bytes. Buffers must be distinct, have positive capacities,
// and must not overlap the input. Capacities include the terminating NUL.
// An absent ':' leaves namespace_buffer untouched and copies the entire key.
// Otherwise, the first two colon-delimited fields are copied; later fields are ignored.
extern "C" void acnh_access_key_split(const char* access_key,
                                      char* key_buffer, int key_capacity,
                                      char* namespace_buffer, int namespace_capacity) noexcept;

// Contract of the namespace selection region main+0x406564..0x406624.
// The table has 13 readable NUL-terminated strings in original order.
// The namespace is NUL-terminated within the handler's 64-byte buffer.
// An unmatched namespace selects index zero, as does the first table entry.
extern "C" unsigned acnh_access_key_namespace(const char* namespace_text,
                                             const char* const* namespace_table) noexcept;
