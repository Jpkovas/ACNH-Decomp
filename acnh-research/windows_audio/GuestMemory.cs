// SPDX-License-Identifier: GPL-3.0-or-later
using Ryujinx.Memory;
using Ryujinx.Memory.Range;
using System;
using System.Buffers;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace AcnhAudio;

// The native host owns these pages and validates their mapping and permission.
internal sealed unsafe class GuestMemory : IVirtualMemoryManager
{
    private readonly byte* _base;
    private readonly ulong _size;
    private readonly delegate* unmanaged[Cdecl]<void*, ulong, ulong, int, int> _check;
    private readonly void* _user;
    public GuestMemory(byte* address, ulong size,
        delegate* unmanaged[Cdecl]<void*, ulong, ulong, int, int> check, void* user)
    { _base = address; _size = size; _check = check; _user = user; }

    private byte* Pointer(ulong address, ulong size, bool write = false)
    {
        if (address > _size || size > _size - address ||
            (size != 0 && _check(_user, address, size, write ? 1 : 0) == 0))
            throw new InvalidMemoryRegionException($"Unmapped audio memory {address:x}+{size:x}");
        return _base + address;
    }
    public bool UsesPrivateAllocations => false;
    public T Read<T>(ulong address) where T : unmanaged => Unsafe.ReadUnaligned<T>(Pointer(address, (ulong)sizeof(T)));
    public void Read(ulong address, Span<byte> data) => GetSpan(address, data.Length).CopyTo(data);
    public void Write<T>(ulong address, T value) where T : unmanaged => Unsafe.WriteUnaligned(Pointer(address, (ulong)sizeof(T), true), value);
    public void Write(ulong address, ReadOnlySpan<byte> data) => data.CopyTo(new Span<byte>(Pointer(address, (ulong)data.Length, true), data.Length));
    public bool WriteWithRedundancyCheck(ulong address, ReadOnlySpan<byte> data)
    {
        var span = new Span<byte>(Pointer(address, (ulong)data.Length, true), data.Length);
        if (data.SequenceEqual(span)) return false;
        data.CopyTo(span); return true;
    }
    public ReadOnlySpan<byte> GetSpan(ulong address, int size, bool tracked = false) => new(Pointer(address, checked((ulong)size)), size);
    public ReadOnlySequence<byte> GetReadOnlySequence(ulong address, int size, bool tracked = false) =>
        new(new NativeMemoryManager<byte>(Pointer(address, checked((ulong)size)), size).Memory);
    public WritableRegion GetWritableRegion(ulong address, int size, bool tracked = false) =>
        new(null, address, new NativeMemoryManager<byte>(Pointer(address, checked((ulong)size), true), size).Memory);
    public ref T GetRef<T>(ulong address) where T : unmanaged => ref Unsafe.AsRef<T>(Pointer(address, (ulong)sizeof(T), true));
    public IEnumerable<HostMemoryRange> GetHostRegions(ulong address, ulong size) =>
        new[] { new HostMemoryRange((nuint)Pointer(address, size), size) };
    public IEnumerable<MemoryRange> GetPhysicalRegions(ulong address, ulong size) =>
        new[] { new MemoryRange(address, size) };
    public bool IsMapped(ulong address) => IsRangeMapped(address, 1);
    public bool IsRangeMapped(ulong address, ulong size) => address <= _size && size <= _size - address &&
        (size == 0 || _check(_user, address, size, 0) != 0);
    public void SignalMemoryTracking(ulong address, ulong size, bool write, bool precise = false, int? exemptId = null) { }
    public void Map(ulong va, ulong pa, ulong size, MemoryMapFlags flags) => throw new NotSupportedException();
    public void MapForeign(ulong va, nuint pointer, ulong size) => throw new NotSupportedException();
    public void Unmap(ulong va, ulong size) => throw new NotSupportedException();
    public void Reprotect(ulong va, ulong size, MemoryPermission permission) => throw new NotSupportedException();
    public void TrackingReprotect(ulong va, ulong size, MemoryPermission permission, bool guest) => throw new NotSupportedException();
}
