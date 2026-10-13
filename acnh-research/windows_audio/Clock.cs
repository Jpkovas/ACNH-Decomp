// SPDX-License-Identifier: GPL-3.0-or-later
// The renderer uses only this clock property; no CPU emulator is included.
namespace Ryujinx.Cpu
{
    public interface ITickSource { double ElapsedSeconds { get; } }
}

namespace AcnhAudio
{
    internal sealed class Clock : Ryujinx.Cpu.ITickSource
    {
        private readonly System.Diagnostics.Stopwatch _clock = System.Diagnostics.Stopwatch.StartNew();
        public double ElapsedSeconds => _clock.Elapsed.TotalSeconds;
    }
}
