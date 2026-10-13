// SPDX-License-Identifier: GPL-3.0-or-later
using Ryujinx.Audio.Integration;
using Ryujinx.Audio.Renderer.Parameter;
using Ryujinx.Audio.Renderer.Server;
using Ryujinx.Common.Logging;
using Ryujinx.Memory;
using System;
using System.Buffers;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace AcnhAudio;

public static unsafe class Exports
{
    private const int Failed = (2 << 9) | 153;
    static Exports()
    {
        Logger.RemoveTarget("console");
        Logger.Updated += (_, args) => Console.Error.WriteLine(args.Message);
    }
    private sealed class Event : IWritableEvent
    {
        private readonly delegate* unmanaged[Cdecl]<void*, int, void> _notify;
        private readonly void* _user;
        public Event(delegate* unmanaged[Cdecl]<void*, int, void> notify, void* user) { _notify = notify; _user = user; }
        public void Signal() => _notify(_user, 1);
        public void Clear() => _notify(_user, 0);
    }
    private sealed class Session : IDisposable
    {
        public AudioRendererManager Manager;
        public AudioRenderSystem Renderer;
        public PcmDriver Driver;
        public void Dispose() { Manager?.Dispose(); Driver?.Dispose(); }
    }
    private static Session Get(nint handle) => (Session)GCHandle.FromIntPtr(handle).Target;
    private static int Error(Exception error) { Console.Error.WriteLine($"ACNH audio: {error}"); return Failed; }

    [UnmanagedCallersOnly(EntryPoint = "acnh_audio_work_size", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static ulong WorkSize(byte* configuration)
    {
        try { var config = Unsafe.ReadUnaligned<AudioRendererConfiguration>(configuration); return AudioRendererManager.GetWorkBufferSize(ref config); }
        catch (Exception error) { Error(error); return 0; }
    }

    [UnmanagedCallersOnly(EntryPoint = "acnh_audio_create", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static int Create(byte* configuration, byte* memory, ulong memorySize,
        delegate* unmanaged[Cdecl]<void*, ulong, ulong, int, int> check,
        delegate* unmanaged[Cdecl]<void*, short*, int, uint, uint, void> submit,
        delegate* unmanaged[Cdecl]<void*, int, void> notify, void* user,
        ulong workAddress, ulong workSize, nint* handle)
    {
        Session session = null;
        try
        {
            *handle = 0;
            if (memory == null || configuration == null || check == null || submit == null || notify == null) return Failed;
            var config = Unsafe.ReadUnaligned<AudioRendererConfiguration>(configuration);
            session = new Session { Manager = new AudioRendererManager(new Clock()), Driver = new PcmDriver(submit, user) };
            var events = new IWritableEvent[Ryujinx.Audio.Constants.AudioRendererSessionCountMax];
            for (int i = 0; i < events.Length; i++) events[i] = new Event(notify, user);
            session.Manager.Initialize(events, session.Driver);
            var result = session.Manager.OpenAudioRenderer(out session.Renderer,
                new GuestMemory(memory, memorySize, check, user), ref config, 0, workAddress, workSize, 0xffff8001);
            if ((int)result != 0) { session.Dispose(); return (int)result; }
            *handle = GCHandle.ToIntPtr(GCHandle.Alloc(session));
            return 0;
        }
        catch (Exception error) { session?.Dispose(); return Error(error); }
    }

    [UnmanagedCallersOnly(EntryPoint = "acnh_audio_update", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static int Update(nint handle, byte* input, int inputSize, byte* output, int outputSize, byte* performance, int performanceSize)
    {
        try
        {
            var incoming = new NativeMemoryManager<byte>(input, inputSize).Memory;
            var outgoing = new NativeMemoryManager<byte>(output, outputSize).Memory;
            var metrics = performanceSize > 0 ? new NativeMemoryManager<byte>(performance, performanceSize).Memory : Memory<byte>.Empty;
            return (int)Get(handle).Renderer.Update(outgoing, metrics, new ReadOnlySequence<byte>(incoming));
        }
        catch (Exception error) { return Error(error); }
    }
    [UnmanagedCallersOnly(EntryPoint = "acnh_audio_control", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static int Control(nint handle, int command, uint argument)
    {
        try
        {
            var renderer = Get(handle).Renderer;
            switch (command)
            {
                case 0: renderer.Start(); return 0;
                case 1: renderer.Stop(); return 0;
                case 2: renderer.SetRenderingTimeLimitPercent(argument); return 0;
                case 3: return (int)renderer.ExecuteAudioRendererRendering();
                default: return Failed;
            }
        }
        catch (Exception error) { return Error(error); }
    }
    [UnmanagedCallersOnly(EntryPoint = "acnh_audio_destroy", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static void Destroy(nint handle)
    {
        try { Get(handle).Dispose(); GCHandle.FromIntPtr(handle).Free(); }
        catch (Exception error) { Error(error); }
    }
}
