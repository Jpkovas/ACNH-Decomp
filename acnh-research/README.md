# ACNH Research

Goal atual: **decompilar ACNH e produzir uma build nativa jogável para Windows**. Continua incompleto; ainda não há gameplay na ilha nem save/reload validados. Critérios, evidências e estado do agendador em [windows_port.md](docs/windows_port.md).

O [plano técnico](../docs/plano_tecnico_decompilacao_acnh_elysium_crossing.md) originou a pesquisa incremental M0–M4 e M6. O pedido posterior ampliou o objetivo para a decompilação e a build Windows. M5 e a integração com Elysium Crossing continuam excluídos por solicitação do usuário, registrada em [scope.md](docs/scope.md).

As versões efetivamente verificadas são 1.0.0 e 3.0.3. Já existem parsers e catálogos reais, round-trip EventFlow nas duas versões, cinco módulos C++ e três funções versionadas com diff ARM64. Consulte [progresso](docs/progress.md), [métricas](docs/metrics.md), [resultados e limites](docs/findings/pilots.md) e [reprodução](docs/reproduction.md).

`private/` contém ferramentas portáteis, ambientes, inputs derivados, bancos Ghidra e resultados proprietários. `vendor/` contém checkouts upstream com suas licenças, ignorados pelo Git. Dumps e chaves permanecem em `../gamedump/`, também ignorado.

As implementações próprias ficam em `reconstructed/`. Elysium Crossing permanece separado. Não há publicação automática nem envio dos arquivos locais para serviços externos.

Verificação local, com os inputs e ferramentas preparados:

```powershell
& .\acnh-research\scripts\run_all.ps1
```

`-RegenerateData` repete experimentos de formatos e pilotos; `-AnalyzeBinaries` repete a análise Ghidra, que é demorada. A execução padrão valida os hashes atuais, relatórios, regressões, build, testes, índice e métricas.
