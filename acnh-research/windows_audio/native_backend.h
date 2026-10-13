/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef ACNH_NATIVE_AUDIO_H
#define ACNH_NATIVE_AUDIO_H
#include "kernel/ipc.h"
int audren_native_work_size(IpcCtx* c, u64* size);
int audren_native_open(SvcObj* o, IpcCtx* c);
int audren_native_enabled(SvcObj* o);
int audren_native_update(SvcObj* o, IpcCtx* c);
int audren_native_control(SvcObj* o, int command, u32 argument);
KEvent* audren_native_event(SvcObj* o);
#endif
