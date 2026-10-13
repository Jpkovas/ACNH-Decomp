/* Research adapter for the manually recovered ACNH 1.0.0 AccessKey parser.
 * Headers and buffers must be mapped as required by the original routine.
 * CPU.mem has no size or page-validation API; these guards check arithmetic,
 * callback identity and overlap, not guest page permissions.
 */
#include "cpu.h"

extern void acnh_access_key_split(const char*, char*, int, char*, int);

typedef struct AcnhRange {
    u64 start;
    u64 end;
} AcnhRange;

static int acnh_range(const CPU* c, u64 start, u64 length, AcnhRange* range) {
    const uintptr_t host = (uintptr_t)c->mem;
    if (!length || start > UINT64_MAX - length || start > UINTPTR_MAX - host ||
        length > UINTPTR_MAX - host - start) {
        return 0;
    }
    range->start = start;
    range->end = start + length;
    return 1;
}

static int acnh_overlap(AcnhRange left, AcnhRange right) {
    return left.start < right.end && right.start < left.end;
}

static u64 acnh_read64(const u8* memory, u64 address) {
    u64 value;
    memcpy(&value, memory + address, sizeof(value));
    return value;
}

static i32 acnh_read32(const u8* memory, u64 address) {
    i32 value;
    memcpy(&value, memory + address, sizeof(value));
    return value;
}

static int acnh_access_key_reviewed_return(u64 return_address) {
    /* Only the twelve reviewed direct callers discard the incidental x0.
     * Original C++ return type and indirect caller contracts are not proved.
     */
    switch (return_address) {
    case 0x830EB64ull:
    case 0x830FD54ull:
    case 0x8310BA4ull:
    case 0x8311A24ull:
    case 0x8311C30ull:
    case 0x8312DD4ull:
    case 0x8321774ull:
    case 0x8321A34ull:
    case 0x83458F0ull:
    case 0x840A5E4ull:
    case 0x840B564ull:
    case 0x840C5F4ull:
        return 1;
    default:
        return 0;
    }
}

SNX_EXPORT int acnh_bridge_access_key_try(CPU* c, u64 entry) {
    if (entry != 0x821B670ull || c->x[31] < 0xF0 ||
        !acnh_access_key_reviewed_return(c->x[30])) {
        return 0;
    }
    const u8* const memory = c->mem;
    AcnhRange ranges[8];
    if (!acnh_range(c, c->x[0], 16, &ranges[0]) ||
        !acnh_range(c, c->x[1], 20, &ranges[1]) ||
        !acnh_range(c, c->x[2], 20, &ranges[2])) {
        return 0;
    }
    const u64 input_vptr = acnh_read64(memory, c->x[0]);
    if (!acnh_range(c, input_vptr, 32, &ranges[7]) ||
        acnh_read64(memory, input_vptr + 24) != 0x80069C0ull) {
        return 0;
    }
    const u64 input = acnh_read64(memory, c->x[0] + 8);
    const u64 key = acnh_read64(memory, c->x[1] + 8);
    const u64 namespace_text = acnh_read64(memory, c->x[2] + 8);
    const i32 key_capacity = acnh_read32(memory, c->x[1] + 16);
    const i32 namespace_capacity = acnh_read32(memory, c->x[2] + 16);
    if (key_capacity <= 0 || namespace_capacity <= 0 ||
        !acnh_range(c, input, 0x80000, &ranges[3]) ||
        !acnh_range(c, key, (u32)key_capacity, &ranges[4]) ||
        !acnh_range(c, namespace_text, (u32)namespace_capacity, &ranges[5]) ||
        !acnh_range(c, c->x[31] - 0xF0, 0xF0, &ranges[6])) {
        return 0;
    }
    u64 length = 0, separator = UINT64_MAX;
    while (length < 0x80000) {
        const u8 byte = memory[input + length];
        if (!byte) {
            break;
        }
        if (byte == ':' && separator == UINT64_MAX) {
            separator = length;
        }
        ++length;
    }
    if (length == 0x80000) {
        return 0;
    }
    ranges[3].end = input + length + 1;
    for (unsigned left = 0; left < 8; ++left) {
        for (unsigned right = left + 1; right < 8; ++right) {
            if (acnh_overlap(ranges[left], ranges[right])) {
                return 0;
            }
        }
    }
    acnh_access_key_split((const char*)(memory + input), (char*)(memory + key), key_capacity,
                         (char*)(memory + namespace_text), namespace_capacity);
    /* Preserve observed x0, including the pointer into inactive guest stack.
     * No recovered caller reads that temporary object after return. The fast
     * path does not reproduce writes to the original 0xf0 bytes of dead stack.
     */
    c->x[0] = separator == UINT64_MAX ? key :
        separator + 1 == length ? c->x[0] : c->x[31] - 0x70;
    c->pc = c->x[30];
    return 1;
}
