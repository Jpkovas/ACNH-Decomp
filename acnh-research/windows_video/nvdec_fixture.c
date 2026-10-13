/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright 2026 the ACNH research contributors.
   Independent H.264 I_PCM fixture: no encoder, game bytes or guest CPU
   execution. Runs the actual NVDEC/VIC and block-linear routines against
   bounded test IOVAs. */
#include "video/host1x_int.h"
#include <stdarg.h>
#include <stdio.h>

enum {
  PS = 0x1000,
  BS = 0x2000,
  STATUS = 0x3000,
  Y0 = 0x4000,
  C0 = 0x5000,
  Y1 = 0x6000,
  C1 = 0x7000,
  VIC_CFG = 0x8000,
  RGBA = 0x9000,
  MEM_SIZE = 0xC000
};
static u8 memory[MEM_SIZE];
static int failures, cases;
static struct {
  u8 *bytes;
  size_t capacity;
} packets[2];
static u32 packet_count;

void *fixture_realloc(void *previous, size_t size);
void *fixture_realloc(void *previous, size_t size) {
  u32 index = 0;
  if (previous) {
    while (index < packet_count && packets[index].bytes != previous)
      index++;
  } else
    index = packet_count++;
  if (index >= 2)
    return NULL;
  void *result = realloc(previous, size);
  if (result && !previous)
    memset(result, 0xA5, size);
  if (result) {
    packets[index].bytes = result;
    packets[index].capacity = size;
  }
  return result;
}

u8 *iova_ptr(u64 address, u64 length) {
  if (address >= MEM_SIZE || length > MEM_SIZE - address)
    return NULL;
  return memory + address;
}
void logf_(int level, const char *format, ...) {
  (void)level;
  va_list args;
  va_start(args, format);
  vfprintf(stderr, format, args);
  va_end(args);
}
static void check(int valid, const char *label) {
  if (!valid) {
    fprintf(stderr, "FAIL: %s\n", label);
    failures++;
  }
}
static void put32(u32 address, u32 value) {
  memcpy(memory + address, &value, 4);
}
static void put64(u32 address, u64 value) {
  memcpy(memory + address, &value, 8);
}
typedef struct {
  u8 bytes[1024];
  u32 bits;
} Bits;
static void bit(Bits *out, u32 value) {
  if (value)
    out->bytes[out->bits / 8] |= (u8)(1u << (7 - out->bits % 8));
  out->bits++;
}
static void fixed(Bits *out, u32 value, u32 count) {
  while (count)
    bit(out, (value >> --count) & 1);
}
static void ue(Bits *out, u32 value) {
  u32 width = 0, code = value + 1;
  for (u32 v = code; v; v >>= 1)
    width++;
  for (u32 i = 1; i < width; i++)
    bit(out, 0);
  fixed(out, code, width);
}
static u8 luma(u32 pattern, u32 sample) {
  return pattern == 0 ? 81 : pattern == 1 ? 41 : (u8)(16 + sample % 220);
}
static u8 cb(u32 pattern) {
  return pattern == 0 ? 90 : pattern == 1 ? 240 : 128;
}
static u8 cr(u32 pattern) {
  return pattern == 0 ? 240 : pattern == 1 ? 110 : 128;
}
static u32 make_slice(u8 *output, u32 pattern, u32 framing) {
  Bits out = {{0}, 0};
  ue(&out, 0);       /* first_mb_in_slice */
  ue(&out, 2);       /* I slice */
  ue(&out, 0);       /* PPS id */
  fixed(&out, 0, 4); /* frame_num */
  ue(&out, 0);       /* idr_pic_id, POC type 2 has no POC fields */
  bit(&out, 0);
  bit(&out, 0); /* IDR reference marking */
  ue(&out, 0);  /* signed slice_qp_delta = 0 */
  ue(&out, 1);  /* disable_deblocking_filter_idc */
  ue(&out, 25); /* I_PCM macroblock */
  while (out.bits % 8)
    bit(&out, 0);
  for (u32 i = 0; i < 256; i++)
    fixed(&out, luma(pattern, i), 8);
  for (u32 i = 0; i < 64; i++)
    fixed(&out, cb(pattern), 8);
  for (u32 i = 0; i < 64; i++)
    fixed(&out, cr(pattern), 8);
  bit(&out, 1);
  while (out.bits % 8)
    bit(&out, 0);
  u8 nal[1024];
  u32 n = 0, zeros = 0;
  nal[n++] = 0x65;
  for (u32 i = 0; i < out.bits / 8; i++) {
    u8 b = out.bytes[i];
    if (zeros == 2 && b <= 3) {
      nal[n++] = 3;
      zeros = 0;
    }
    nal[n++] = b;
    zeros = b == 0 ? zeros + 1 : 0;
  }
  u32 prefix = framing == 2 ? 0 : 4;
  if (framing == 0) {
    output[0] = 0;
    output[1] = 0;
    output[2] = 0;
    output[3] = 1;
  }
  if (framing == 1) {
    output[0] = (u8)(n >> 24);
    output[1] = (u8)(n >> 16);
    output[2] = (u8)(n >> 8);
    output[3] = (u8)n;
  }
  memcpy(output + prefix, nal, n);
  return prefix + n;
}
static void picture_setup(u32 size, u32 index) {
  memset(memory + PS, 0, 0x300);
  put32(PS + 0x48, size);
  put32(PS + 0x64, 1);
  put32(PS + 0x68, 1); /* 16x16 */
  put32(PS + 0x60, 1); /* frame_mbs_only */
  put32(PS + 0x80, 1); /* deblock syntax present */
  put32(PS + 0x8C, 64);
  put32(PS + 0x90, 64);
  put32(PS + 0xB0, (1u << 1) | (1u << 12) | (2u << 14));
  put32(PS + 0xB4, index << 2);
  memset(memory + PS + 0x1C0, 16, 6 * 16 + 2 * 64);
}
static u32 reference_offset(u32 x, u32 y) {
  /* Independent bit permutation for one 64-byte-wide, two-GOB block. */
  return (x & 15) | ((y & 1) << 4) | ((x & 16) << 1) | ((y & 6) << 5) |
         ((x & 32) << 3) | ((y & 8) << 6);
}
static void verify_planes(u32 pattern, u32 yp, u32 cp) {
  for (u32 y = 0; y < 16; y++)
    for (u32 x = 0; x < 16; x++)
      check(memory[yp + reference_offset(x, y)] == luma(pattern, y * 16 + x),
            "exact decoded luma");
  for (u32 y = 0; y < 8; y++)
    for (u32 x = 0; x < 16; x++)
      check(memory[cp + reference_offset(x, y)] ==
                (x & 1 ? cr(pattern) : cb(pattern)),
            "exact decoded NV12 chroma");
}
static void verify_packet_padding(u32 channel, u32 nal_size) {
  u8 *packet_allocation = packets[channel].bytes;
  size_t packet_capacity = packets[channel].capacity;
  size_t nal_start = 0;
  for (size_t i = 0; i + 3 < packet_capacity; i++)
    if (packet_allocation[i] == 0 && packet_allocation[i + 1] == 0 &&
        packet_allocation[i + 2] == 1 && packet_allocation[i + 3] == 0x65)
      nal_start = i + 3;
  check(nal_start != 0, "submitted IDR NAL found");
  size_t end = nal_start + nal_size;
  check(end <= packet_capacity && packet_capacity - end >= 64,
        "FFmpeg 64-byte padding allocation");
  if (end <= packet_capacity && packet_capacity - end >= 64)
    for (size_t i = 0; i < 64; i++)
      check(packet_allocation[end + i] == 0, "FFmpeg padding is zero");
}
static void compose(u32 pattern, u32 yp, u32 cp, u32 format) {
  u32 regs[0x1000] = {0};
  memset(memory + VIC_CFG, 0, 0x610);
  memset(memory + RGBA, 0xA5, 0x1000);
  put64(VIC_CFG + 0x20, format | ((u64)15 << 32) | ((u64)15 << 46));
  put64(VIC_CFG + 0x90, 1);
  put64(VIC_CFG + 0x90 + 0x20, (u64)(15u << 16) << 32);
  put64(VIC_CFG + 0x90 + 0x28, (u64)(15u << 16) << 32);
  put64(VIC_CFG + 0x90 + 0x30, ((u64)15 << 16) | ((u64)15 << 48));
  put64(VIC_CFG + 0x90 + 0x40,
        0x44 | (1u << 11) | (1u << 15) | ((u64)15 << 32) | ((u64)15 << 46));
  regs[0x708 / 4] = VIC_CFG >> 8;
  regs[0x720 / 4] = RGBA >> 8;
  regs[0x400 / 4] = yp >> 8;
  regs[0x404 / 4] = cp >> 8;
  vic_execute(regs);
  for (u32 y = 0; y < 16; y++)
    for (u32 x = 0; x < 16; x++) {
      u8 *pixel = memory + RGBA + y * 256 + x * 4;
      u8 gray = (u8)(((luma(pattern, y * 16 + x) - 16) * 298 + 128) >> 8);
      u8 r = pattern == 0 ? 255 : pattern == 1 ? 0 : gray;
      u8 b = pattern == 0 ? 0 : pattern == 1 ? 255 : gray;
      check(pixel[0] == (format == 0x1F ? r : b) &&
                pixel[1] == (pattern < 2 ? 0 : gray) &&
                pixel[2] == (format == 0x1F ? b : r) && pixel[3] == 255,
            "VIC exact RGBA/BGRA pixels");
    }
  cases++;
}
int main(void) {
  NvdecCtx *channels[2] = {nvdec_new(), nvdec_new()};
  check(channels[0] && channels[1], "decoder allocation");
  if (!channels[0] || !channels[1])
    return 1;
  for (u32 framing = 0; framing < 3; framing++) {
    u32 index = framing & 1, yp = index ? Y1 : Y0, cp = index ? C1 : C0;
    u32 regs[0x1000] = {0};
    memset(memory + yp, 0xA5, 0x1000);
    memset(memory + cp, 0xA5, 0x1000);
    u32 size = make_slice(memory + BS, framing, framing);
    picture_setup(size, index);
    regs[0x200 / 4] = 3;
    regs[0x404 / 4] = PS >> 8;
    regs[0x408 / 4] = BS >> 8;
    regs[0x424 / 4] = STATUS >> 8;
    regs[0x430 / 4 + index] = yp >> 8;
    regs[0x474 / 4 + index] = cp >> 8;
    nvdec_execute(channels[index], regs);
    verify_packet_padding(index, size - (framing == 2 ? 0 : 4));
    check(rd32(memory + STATUS, 0) == 1 && rd32(memory + STATUS, 4) == 0 &&
              rd32(memory + STATUS, 12) == 0,
          "NVDEC success status");
    verify_planes(framing, yp, cp);
    cases++;
    compose(framing, yp, cp, 0x1F);
    compose(framing, yp, cp, 0x20);
  }
  u32 regs[0x1000] = {0};
  regs[0x424 / 4] = STATUS >> 8;
  regs[0x200 / 4] = 7;
  nvdec_execute(channels[0], regs);
  check(rd32(memory + STATUS, 0) == 0 && rd32(memory + STATUS, 12) == 1,
        "unsupported codec failure status");
  cases++;
  regs[0x200 / 4] = 3;
  regs[0x404 / 4] = MEM_SIZE >> 8;
  nvdec_execute(channels[0], regs);
  check(rd32(memory + STATUS, 0) == 0 && rd32(memory + STATUS, 12) == 1,
        "unmapped setup failure status");
  cases++;
  nvdec_free(channels[0]);
  nvdec_free(channels[1]);
  printf("{\"cases\":%d,\"failures\":%d,\"h264_frames\":3,\"vic_surfaces\":6,"
         "\"guest_cpu\":false}\n",
         cases, failures);
  return failures ? 1 : 0;
}
