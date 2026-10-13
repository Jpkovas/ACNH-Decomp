// SPDX-License-Identifier: GPL-3.0-or-later
using Ryujinx.Audio.Common;
using Ryujinx.Audio.Integration;
using Ryujinx.Memory;
using System;
using System.Runtime.InteropServices;
using System.Threading;

namespace AcnhAudio;

internal sealed unsafe class PcmDriver : IHardwareDeviceDriver
{
    private readonly delegate* unmanaged[Cdecl]<void*, short*, int, uint, uint, void> _submit;
    private readonly void* _user;
    private readonly ManualResetEvent _updated = new(false);
    private readonly ManualResetEvent _running = new(true);
    public float Volume { get; set; } = 1;
    public static bool IsSupported => true;
    public PcmDriver(delegate* unmanaged[Cdecl]<void*, short*, int, uint, uint, void> submit, void* user)
    { _submit = submit; _user = user; }
    public ManualResetEvent GetUpdateRequiredEvent() => _updated;
    public ManualResetEvent GetPauseEvent() => _running;
    public bool SupportsDirection(IHardwareDeviceDriver.Direction direction) => direction == IHardwareDeviceDriver.Direction.Output;
    public bool SupportsSampleRate(uint rate) => rate == 48000;
    public bool SupportsSampleFormat(SampleFormat format) => format == SampleFormat.PcmInt16;
    public bool SupportsChannelCount(uint channels) => channels == 2;
    public IHardwareDeviceSession OpenDeviceSession(IHardwareDeviceDriver.Direction direction,
        IVirtualMemoryManager memory, SampleFormat format, uint rate, uint channels)
    {
        if (!SupportsDirection(direction) || !SupportsSampleRate(rate) ||
            !SupportsSampleFormat(format) || !SupportsChannelCount(channels)) throw new NotSupportedException();
        return new Session(this, rate, channels);
    }
    public void Dispose() { _updated.Dispose(); _running.Dispose(); }

    private sealed class Session : IHardwareDeviceSession
    {
        private readonly PcmDriver _driver;
        private readonly uint _rate, _channels;
        private ulong _samples;
        private float _volume = 1;
        public Session(PcmDriver driver, uint rate, uint channels) { _driver = driver; _rate = rate; _channels = channels; }
        public bool RegisterBuffer(AudioBuffer buffer) => buffer.Data != null;
        public void UnregisterBuffer(AudioBuffer buffer) { }
        public void QueueBuffer(AudioBuffer buffer)
        {
            if (buffer.Data == null || buffer.DataSize > (ulong)buffer.Data.Length) throw new ArgumentException("Invalid PCM buffer");
            Span<short> pcm = MemoryMarshal.Cast<byte, short>(buffer.Data.AsSpan(0, checked((int)buffer.DataSize)));
            float volume = _volume * _driver.Volume;
            // HardwareDeviceImpl copies its output for this queue; scaling doesn't alter the DSP mix buffers.
            if (volume != 1) for (int i = 0; i < pcm.Length; i++) pcm[i] = (short)Math.Clamp(pcm[i] * volume, short.MinValue, short.MaxValue);
            fixed (short* samples = pcm) _driver._submit(_driver._user, samples, pcm.Length, _rate, _channels);
            Interlocked.Add(ref _samples, (ulong)pcm.Length / _channels);
            _driver._updated.Set();
        }
        public bool WasBufferFullyConsumed(AudioBuffer buffer) => true; // Native host copies each submitted buffer synchronously.
        public void SetVolume(float volume) => _volume = volume;
        public float GetVolume() => _volume;
        public ulong GetPlayedSampleCount() => Interlocked.Read(ref _samples);
        public void Start() { }
        public void Stop() { }
        public void PrepareToClose() { }
        public void Dispose() { }
    }
}
