#include "acnh_research/access_key.hpp"

#include <cstring>

namespace {
void copy_field(char* destination, int capacity, const char* source,
                std::size_t length) noexcept {
    const auto maximum = static_cast<std::size_t>(capacity - 1);
    const auto count = length < maximum ? length : maximum;
    std::memcpy(destination, source, count);
    destination[count] = '\0';
}
}

extern "C" void acnh_access_key_split(const char* access_key,
                                      char* key_buffer, int key_capacity,
                                      char* namespace_buffer, int namespace_capacity) noexcept {
    const char* separator = std::strchr(access_key, ':');
    if (separator == nullptr) {
        copy_field(key_buffer, key_capacity, access_key, std::strlen(access_key));
        return;
    }
    copy_field(namespace_buffer, namespace_capacity, access_key,
               static_cast<std::size_t>(separator - access_key));
    const char* key = separator + 1;
    const char* end = std::strchr(key, ':');
    const auto length = end == nullptr ? std::strlen(key) : static_cast<std::size_t>(end - key);
    copy_field(key_buffer, key_capacity, key, length);
}

extern "C" unsigned acnh_access_key_namespace(const char* namespace_text,
                                             const char* const* namespace_table) noexcept {
    for (unsigned index = 0; index < 13; ++index) {
        if (std::strcmp(namespace_text, namespace_table[index]) == 0) {
            return index;
        }
    }
    return 0;
}
