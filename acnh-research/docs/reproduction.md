# Reprodução local

Executar em PowerShell a partir de `D:\ACNH_Decomp`. Nenhum serviço externo precisa receber arquivos do jogo.

## Ferramentas preparadas

Python embutido 3.12.10, Ghidra 12.1.4, JDK 21.0.12.1+1, Clang/LLVM 23.1.3, objdiff-cli 3.8.2 e hactool 1.5.4 estão sob `private/tools`. O build nativo usa CMake/Ninja, MSVC SDK e BuildTools 2022 já instalados neste computador. Checkouts ficam em `vendor`, fixados pelos commits do lock.

O ambiente Python embutido requer `import site` no `python312._pth`, `Lib/site-packages` e dependências de `config/python-runtime.lock.txt`. O wrapper dos executáveis upstream adiciona os diretórios corretos ao sys.path. Pip deve usar `--no-build-isolation` se instalar dependências legadas nesse runtime.

```powershell
$py = '.\acnh-research\private\tools\python\python.exe'
& $py -m pip install --no-build-isolation -r .\acnh-research\config\python-runtime.lock.txt
& .\acnh-research\scripts\bootstrap_sources.ps1
```

As distribuições nos locks podem ser reobtidas por `download_tools.ps1 -Tool ghidra|jdk|llvm|objdiff|hactoolmodern`, uma por comando. O script confere tamanho/digest upstream quando disponível e o hash já fixado. LLVM `.tar.zst` requer extração Zstandard/tar; não é tratado como ZIP. Não se usa a última versão automaticamente.

Switch Loader foi compilado com JDK21, Gradle8.10.2 e `-PGHIDRA_INSTALL_DIR=<private/tools/ghidra/ghidra_12.1.4_PUBLIC>` seguindo o build.gradle upstream; a extensão fica em `Ghidra/Extensions/SwitchLoader`. O runtime Ghidra recebe JAVA_HOME e settings/cache/temp locais de cada projeto pelo wrapper. APIs Java substituem scripts Jython antigos.

## Entradas e importação

Os NSP e chaves continuam em `gamedump`. A origem é registrada como fornecida pelo usuário e não verificada. O audit faz hash dos containers e confere bounds do PFS0. Chaves nunca aparecem nos relatórios. Firmware não é usada.

```powershell
& $py .\acnh-research\scripts\audit_inputs.py --help
& $py .\acnh-research\scripts\prepare_inputs.py --keys .\gamedump\prod.keys --package both --extract --tool .\acnh-research\private\tools\hactoolmodern\hactool.exe
& .\acnh-research\scripts\run_ghidra.ps1 -Package base -Mode baseline
& .\acnh-research\scripts\run_ghidra.ps1 -Package update -Mode baseline
& .\acnh-research\scripts\run_ghidra.ps1 -Package base -Mode reimport
& .\acnh-research\scripts\run_ghidra.ps1 -Package update -Mode reimport
& .\acnh-research\scripts\run_ghidra.ps1 -Package base -Mode verify
& .\acnh-research\scripts\run_ghidra.ps1 -Package update -Mode verify
& .\acnh-research\scripts\run_ghidra.ps1 -Package base -Mode curated
& .\acnh-research\scripts\run_ghidra.ps1 -Package update -Mode curated
```

`inspect_nso.py` gera os segmentos canônicos e `nxo_metadata.py` gera as referências de relocations usadas por `verify`; consultar `--help` para os inputs/out dirs. O hactool antigo foi suficiente para base, mas não para BKTR do update. Logs de extração são sanitizados. Uma extração completa é demorada e não é requisito para repetir a validação se os inputs já estiverem preparados.

## Pipeline consolidado

```powershell
& .\acnh-research\scripts\run_all.ps1
& .\acnh-research\scripts\run_all.ps1 -RegenerateData
```

A execução padrão compila os cinco módulos, roda CTest e os testes Python, revalida hashes dos seis segmentos e a aplicação dos golden reports, verifica proveniência/segmentação, normaliza índices, gera candidatos multiversão e atualiza métricas. Ela exige os resultados privados da análise já executada. Falha se há artefato obrigatório ausente, resultado divergente ou endereço órfão no grafo de chamadas.

`-RegenerateData` repete catálogos, round-trips, comparação BCSV e emulação dos pilotos. `-AnalyzeBinaries` reimporta e reanalisa os NSO; pode levar dezenas de minutos por versão. Preserve os logs antes de substituir projetos de pesquisa anotados. Os bancos baseline são derivados; anotações revisadas estão no JSON versionado e podem ser reaplicadas.

`metadata/pipeline-verification.json`, `golden-verification.json`, `metrics.json` e `docs/metrics.md` são as saídas consolidadas. Os transcripts estão em `private/outputs/pipeline`. O manifesto golden fixa o input de cada build e não deve ser atualizado para encobrir divergências.
