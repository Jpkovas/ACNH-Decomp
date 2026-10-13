# ACNH Research

Goal atual: **decompilar ACNH e produzir uma build nativa jogável para Windows**. Continua incompleto. Uma execução privada chegou à ilha, apresentou o cenário 3D, permitiu caminhar e sacudir uma árvore. NPCs, inventário e save/reload ainda precisam de validação; o filme VP9 permanece pendente. Critérios e evidências em [windows_port.md](docs/windows_port.md).

A execução atual usa recompilação estática para x64, serviços/GPU emulados e fallback ARM64. Essa ponte auxilia a pesquisa e não equivale a uma decompilação concluída. A cobertura reconstruída e as dependências remanescentes são registradas separadamente.

O [plano técnico](../docs/plano_tecnico_decompilacao_acnh_elysium_crossing.md) originou a pesquisa incremental M0–M4 e M6. O pedido posterior ampliou o objetivo para a decompilação e a build Windows. M5 e a integração com Elysium Crossing continuam excluídos por solicitação do usuário, registrada em [scope.md](docs/scope.md).

As versões efetivamente verificadas são 1.0.0 e 3.0.3. Já existem parsers e catálogos, round-trip EventFlow e implementações C++ delimitadas com comparação contra ARM64 original. Consulte [progresso](docs/progress.md), [métricas](docs/metrics.md), [resultados e limites](docs/findings/pilots.md) e [reprodução](docs/reproduction.md).

`private/` contém ferramentas portáteis, ambientes, inputs derivados, bancos Ghidra e resultados proprietários. `vendor/` contém checkouts upstream com suas licenças, ignorados pelo Git. Dumps e chaves permanecem em `../gamedump/`, também ignorado.

As implementações escritas no projeto ficam em `reconstructed/`. Elysium Crossing permanece excluído. Marcos públicos contêm ferramentas, fonte revisável e relatórios agregados; os inputs e resultados proprietários permanecem locais. O usuário autorizou publicação de progresso em [Jpkovas/ACNH-Decomp](https://github.com/Jpkovas/ACNH-Decomp).

A ponte usa **SwitchRecomp by MZ Labs**, através do fork ScarletNX. As licenças e exceções Apache/GPL/MIT/LGPL estão em [LICENSE_NOTES.md](LICENSE_NOTES.md) e [licenses](../licenses/).

Verificação local, com os inputs e ferramentas preparados:

```powershell
& .\acnh-research\scripts\run_all.ps1
```

`-RegenerateData` repete experimentos de formatos e pilotos; `-AnalyzeBinaries` repete a análise Ghidra, que é demorada. A execução padrão valida os hashes atuais, relatórios, regressões, build, testes, índice e métricas.
