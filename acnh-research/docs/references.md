# Referências e fontes fixadas

As revisões exatas e licenças ficam em [sources.lock.json](../config/sources.lock.json); as distribuições portáteis e seus SHA-256 em `config/tool-*.lock.json`.

- [CylindricalEarth](https://github.com/Treeki/CylindricalEarth): formatos ACNH, decoders históricos e investigação de receptores.
- [ACNH EventFlow decompiler](https://github.com/asteriation/acnh-eventflow-decompiler) e [compiler](https://github.com/asteriation/acnh-eventflow-compiler): piloto de round-trip.
- [Ghidra](https://github.com/NationalSecurityAgency/ghidra) e [Switch Loader](https://github.com/Adubbz/Ghidra-Switch-Loader): análise e NSO importado.
- [NSO0](https://switchbrew.org/wiki/NSO0), [AAPCS64](https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst) e [Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html): formato, convenção de chamada e RTTI.
- [objdiff](https://github.com/encounter/objdiff), [LLVM](https://github.com/llvm/llvm-project), [Capstone](https://github.com/capstone-engine/capstone) e [Unicorn](https://github.com/unicorn-engine/unicorn): compilação, diff, disassembly e emulação ARM64.
- [MurmurHash3 original](https://github.com/aappleby/smhasher/blob/master/src/MurmurHash3.cpp) e [mmh3](https://github.com/hajimes/mmh3): comparação independente do algoritmo de hash.
- [sarc](https://github.com/zeldamods/sarc) e [evfl](https://github.com/zeldamods/evfl): archives e referência de formato.
- [hactool SciresM](https://github.com/SciresM/hactool) e [hactool borntohonk](https://github.com/borntohonk/hactool): preparação local autorizada dos inputs fornecidos.
- [ac-decomp](https://github.com/ACreTeam/ac-decomp), [dtk-template](https://github.com/encounter/dtk-template), [decompedia](https://github.com/decompals/decompedia), [Switch Toolbox](https://github.com/KillzXGaming/Switch-Toolbox): referências complementares com limites descritos em [compatibility.md](compatibility.md).

A versão de jogo investigada é confirmada pelos inputs, não inferida de notas online. Referências upstream não autenticam a origem dos dumps nem nomes inferidos localmente.
