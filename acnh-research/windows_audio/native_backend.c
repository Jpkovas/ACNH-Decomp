/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Windows host adapter for the MIT-licensed Ryujinx AudioRenderer, compiled with NativeAOT.
   The DSP runs on its own 5 ms clock, and supplies real update statuses and the per-renderer event.
   This module executes no guest CPU instructions. */
#include "native_backend.h"
#include "hle/services_int.h"
#include "kernel/mem.h"
#include "platform/log.h"
#include "platform/plat.h"
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <mmsystem.h>

typedef int (*MemoryCheck)(void*, u64, u64, int);
typedef void (*PcmSubmit)(void*, const i16*, int, u32, u32);
typedef void (*EventNotify)(void*, int);
static u64 (*work_size)(const u8*);
static int (*create)(const u8*, u8*, u64, MemoryCheck, PcmSubmit, EventNotify, void*, u64, u64, void**);
static int (*update)(void*, const u8*, int, u8*, int, u8*, int);
static int (*control)(void*, int, u32);
static void (*destroy)(void*);
static PMutex module_lock = PMUTEX_INIT;
static int module_state;
static MMRESULT(WINAPI* wo_open)(LPHWAVEOUT, UINT, LPCWAVEFORMATEX, DWORD_PTR, DWORD_PTR, DWORD);
static MMRESULT(WINAPI* wo_prepare)(HWAVEOUT, LPWAVEHDR, UINT);
static MMRESULT(WINAPI* wo_write)(HWAVEOUT, LPWAVEHDR, UINT);
static MMRESULT(WINAPI* wo_reset)(HWAVEOUT);
static MMRESULT(WINAPI* wo_unprepare)(HWAVEOUT, LPWAVEHDR, UINT);
static MMRESULT(WINAPI* wo_close)(HWAVEOUT);

enum { QUEUE_SIZE = 64, PCM_BYTES = 4096 };
typedef struct {
    void* handle;
    KEvent* event;
    KTmem* transfer;
    HWAVEOUT device;
    WAVEHDR headers[QUEUE_SIZE];
    u8 samples[QUEUE_SIZE][PCM_BYTES];
    unsigned next;
    FILE* wav;
    u64 bytes, nonzero, frames, wav_bytes;
    int output_failed;
} NativeAudio;

static int load_module(void) {
    const char* path = getenv("SNX_AUDIO_BACKEND");
    if (!path || !*path) return 0;
    pm_lock(&module_lock);
    if (!module_state) {
        HMODULE module = LoadLibraryA(path);
        if (module) {
            work_size = (void*)GetProcAddress(module, "acnh_audio_work_size");
            create = (void*)GetProcAddress(module, "acnh_audio_create");
            update = (void*)GetProcAddress(module, "acnh_audio_update");
            control = (void*)GetProcAddress(module, "acnh_audio_control");
            destroy = (void*)GetProcAddress(module, "acnh_audio_destroy");
        }
        module_state = module && work_size && create && update && control && destroy ? 1 : -1;
        if (module_state < 0)
            WARN("audren: configured native module could not be loaded, Windows error %lu\n", GetLastError());
    }
    int state = module_state;
    pm_unlock(&module_lock);
    return state;
}

static int memory_check(void* user, u64 address, u64 size, int write) {
    (void)user;
    if (address > AS_SIZE || size > AS_SIZE - address) return 0;
    while (size) {
        MemBlock block;
        mem_query(address, &block);
        u32 permission = write ? PERM_W : PERM_R;
        if (!(block.perm & permission) || address < block.addr || address - block.addr >= block.size) return 0;
        u64 chunk = block.size - (address - block.addr);
        if (chunk > size) chunk = size;
        address += chunk;
        size -= chunk;
    }
    return 1;
}
static void event_notify(void* user, int signaled) {
    NativeAudio* state = user;
    if (signaled)
        kevent_signal(state->event);
    else
        kevent_clear(state->event);
}
static void wav_header(NativeAudio* state) {
    if (!state->wav) return;
    u32 header[11] = {0x46464952, 36, 0x45564157, 0x20746d66, 16, 0x00020001, 48000, 192000, 0x00100004, 0x61746164, 0};
    header[1] += (u32)state->wav_bytes;
    header[10] = (u32)state->wav_bytes;
    long position = ftell(state->wav);
    fseek(state->wav, 0, SEEK_SET);
    fwrite(header, 1, sizeof header, state->wav);
    fseek(state->wav, position < 44 ? 44 : position, SEEK_SET);
    fflush(state->wav);
}
static void pcm_submit(void* user, const i16* pcm, int count, u32 rate, u32 channels) {
    NativeAudio* state = user;
    if (count <= 0 || count > PCM_BYTES / 2 || rate != 48000 || channels != 2) {
        WARN_LIMIT(2, "audren: unexpected native PCM format %u Hz, %u channels, %d samples\n", rate, channels, count);
        state->output_failed = 1;
        return;
    }
    unsigned bytes = (unsigned)count * 2;
    for (int i = 0; i < count; i++) state->nonzero += pcm[i] != 0;
    state->bytes += bytes;
    state->frames += (u32)count / channels;
    if (state->wav && state->bytes <= 512ull * 1024 * 1024) {
        state->wav_bytes += fwrite(pcm, 1, bytes, state->wav);
        if (!(state->frames % 48000)) wav_header(state);
    }
    if (!(state->frames % 480000))
        LOG("audren: PCM frames=%llu, nonzero samples=%llu, output_failed=%d\n", (unsigned long long)state->frames,
            (unsigned long long)state->nonzero, state->output_failed);
    if (!state->device || state->output_failed) return;
    WAVEHDR* header = &state->headers[state->next];
    u64 end = plat_ns() + 2000000000ull;
    while ((header->dwFlags & WHDR_INQUEUE) && !(header->dwFlags & WHDR_DONE) && plat_ns() < end)
        plat_sleep_ns(1000000);
    if ((header->dwFlags & WHDR_INQUEUE) && !(header->dwFlags & WHDR_DONE)) {
        WARN("audren: Windows audio device stopped consuming queued samples\n");
        state->output_failed = 1;
        return;
    }
    memcpy(header->lpData, pcm, bytes);
    header->dwBufferLength = bytes;
    MMRESULT result = wo_write(state->device, header, sizeof *header);
    if (result != MMSYSERR_NOERROR) {
        WARN("audren: waveOutWrite failed: %u\n", result);
        state->output_failed = 1;
    }
    state->next = (state->next + 1) % QUEUE_SIZE;
}
static int output_open(NativeAudio* state) {
    const char* capture = getenv("SNX_AUDIO_WAV");
    if (capture && *capture) {
        state->wav = fopen(capture, "wb");
        if (!state->wav) return 0;
        wav_header(state);
    }
    const char* wav_only = getenv("SNX_AUDIO_WAV_ONLY");
    if (wav_only && atoi(wav_only)) return 1;
    HMODULE winmm = LoadLibraryA("winmm.dll");
    if (!winmm) return 0;
    wo_open = (void*)GetProcAddress(winmm, "waveOutOpen");
    wo_prepare = (void*)GetProcAddress(winmm, "waveOutPrepareHeader");
    wo_write = (void*)GetProcAddress(winmm, "waveOutWrite");
    wo_reset = (void*)GetProcAddress(winmm, "waveOutReset");
    wo_unprepare = (void*)GetProcAddress(winmm, "waveOutUnprepareHeader");
    wo_close = (void*)GetProcAddress(winmm, "waveOutClose");
    if (!wo_open || !wo_prepare || !wo_write || !wo_reset || !wo_unprepare || !wo_close) return 0;
    WAVEFORMATEX format = {WAVE_FORMAT_PCM, 2, 48000, 192000, 4, 16, 0};
    MMRESULT result = wo_open(&state->device, WAVE_MAPPER, &format, 0, 0, CALLBACK_NULL);
    if (result) {
        WARN("audren: waveOutOpen failed: %u\n", result);
        return 0;
    }
    for (unsigned i = 0; i < QUEUE_SIZE; i++) {
        state->headers[i].lpData = (LPSTR)state->samples[i];
        state->headers[i].dwBufferLength = PCM_BYTES;
        if (wo_prepare(state->device, &state->headers[i], sizeof(WAVEHDR))) return 0;
    }
    LOG("audren: Windows PCM output opened at 48000 Hz, stereo\n");
    return 1;
}
static void native_destroy(SvcObj* object) {
    NativeAudio* state = (void*)(size_t)object->u[7];
    if (!state) return;
    if (state->handle) destroy(state->handle);
    if (state->device) {
        wo_reset(state->device);
        for (unsigned i = 0; i < QUEUE_SIZE; i++) wo_unprepare(state->device, &state->headers[i], sizeof(WAVEHDR));
        wo_close(state->device);
    }
    if (state->wav) {
        wav_header(state);
        fclose(state->wav);
    }
    LOG("audren: native output: %llu frames, %llu nonzero samples, output_failed=%d\n",
        (unsigned long long)state->frames, (unsigned long long)state->nonzero, state->output_failed);
    if (state->event) kobj_unref(&state->event->o);
    if (state->transfer) kobj_unref(&state->transfer->o);
    free(state);
    object->u[7] = 0;
}
int audren_native_work_size(IpcCtx* context, u64* size) {
    int loaded = load_module();
    if (loaded <= 0) return loaded;
    if (context->raw_size < 0x34) return -1;
    *size = work_size(context->raw);
    return *size ? 1 : -1;
}
int audren_native_open(SvcObj* object, IpcCtx* context) {
    int loaded = load_module();
    if (loaded <= 0) return loaded;
    if (context->raw_size < 0x48 || context->ncopy < 1) return -1;
    NativeAudio* state = calloc(1, sizeof *state);
    if (!state) return -1;
    object->u[7] = (u64)(size_t)state;
    object->destroy = native_destroy;
    state->event = kevent_new("native audio renderer");
    kobj_ref(&state->event->o);
    state->transfer = (KTmem*)h_get_ref(context->copy_h[0], KO_TMEM);
    if (!state->transfer || !output_open(state)) {
        native_destroy(object);
        return -1;
    }
    u64 size = in64(context, 0x38);
    if (size > state->transfer->size) {
        native_destroy(object);
        return -1;
    }
    int result = create(context->raw, g_mem, AS_SIZE, memory_check, pcm_submit, event_notify, state,
                        state->transfer->addr, size, &state->handle);
    if (result) {
        WARN("audren: native renderer initialization failed: %x\n", result);
        native_destroy(object);
        return -1;
    }
    LOG("audren: native renderer initialized, revision=%08x, work buffer=%llu\n", in32(context, 0x30),
        (unsigned long long)size);
    return 1;
}
int audren_native_enabled(SvcObj* object) { return object->u[7] != 0; }
int audren_native_update(SvcObj* object, IpcCtx* context) {
    NativeAudio* state = (void*)(size_t)object->u[7];
    u64 input, insize, output, outsize, performance = 0, perfsize = 0;
    buf_in(context, 0, &input, &insize);
    buf_out(context, 0, &output, &outsize);
    buf_out(context, 1, &performance, &perfsize);
    if (!input || !output || insize > INT_MAX || outsize > INT_MAX || perfsize > INT_MAX ||
        !memory_check(state, input, insize, 0) || !memory_check(state, output, outsize, 1) ||
        (perfsize && !memory_check(state, performance, perfsize, 1)))
        return RC(153, 41);
    int result = update(state->handle, GP(input), (int)insize, GP(output), (int)outsize,
                        perfsize ? GP(performance) : NULL, (int)perfsize);
    if (result) WARN_LIMIT(8, "audren: native RequestUpdate failed: %x\n", result);
    return result;
}
int audren_native_control(SvcObj* object, int command, u32 argument) {
    NativeAudio* state = (void*)(size_t)object->u[7];
    return control(state->handle, command, argument);
}
KEvent* audren_native_event(SvcObj* object) { return ((NativeAudio*)(size_t)object->u[7])->event; }
