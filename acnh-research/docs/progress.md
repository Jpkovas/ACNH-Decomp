# Execução do goal

Checkpoint de áudio e fonte: saída PCM Windows observada em testes de 90, 240 e 900 segundos; quatro casos sintéticos passaram. O predicado terminal EventFlagInt foi integrado à DLL candidata e sua ABI passou em 3.806 casos, além dos 1.364 das três entradas anteriores. O restante do handler e a decompilação integral continuam incompletos.

Goal atual: **incompleto**, decompilação de ACNH e build jogável para Windows, solicitado em 2026-10-13. O agendador registrou `blocked` após falhas de capacidade do modelo nas tentativas anteriores; o turno atual retomou o trabalho técnico. Não há build jogável validada. Escopo e critérios em [windows_port.md](windows_port.md), com estado em `config/windows-goal.json`.

Avanço Windows: a DLL x64 carrega e três entradas usam C++ reconstruído, duas em `main` e uma no SDK de controles. A tela preta da composição inicial foi corrigida com predicados e retângulos de limpeza Maxwell. As capturas mostram cadastro de nome/aniversário, aparência com modelo 3D e diálogo após sua confirmação. Um módulo de áudio NativeAOT, usando o AudioRenderer do Ryujinx com saída PCM Windows, produziu sinal estéreo no teste real; quatro casos sintéticos verificaram PCM16/ADPCM, volumes, silêncio e consumo. Onze testes upstream e a regressão Vulkan com leitura de pixels passaram; a rotina de controles coincidiu com o ARM64 em 3.147 casos. A fila gráfica ainda apresenta comandos inconsistentes e longas paradas em DMA. Ilha, áudio completo, save/reload e decompilação integral permanecem incompletos.

Histórico do goal anterior: entregas técnicas concluídas no escopo incremental acordado, em 2026-10-13. M0–M4 e M6 passaram nos critérios registrados; M5 foi excluído pelo usuário. Esse resultado é pesquisa e reconstrução incremental com contratos delimitados, conforme a definição de sucesso do plano; não representa decompilação integral.

| Marco | Status | Evidência pendente |
|---|---|---|
| M0 | Concluído | `inputs.lock.json`; `metadata/<versão>/import-verification.json`; importações limpas idênticas e 671.746 relocations relativas verificadas |
| M1 | Concluído | 60.728 / 95.989 funções descobertas; 7 anotações revisadas; RTTI; catálogos por versão; zero endpoints órfãos |
| M2 | Concluído | `roundtrip.json`: AI_NPC_Doc_Airport, 3 e 11 nós alcançáveis, grafos equivalentes |
| M3 | Concluído | CMake/Clang/CTest; BCSV comparado em 3.416.917 células; hash e comparador contra ARM64 original |
| M4 | Concluído | Uma função de 8 bytes com correspondência exata; Murmur3 com diff 19,36% / 22,48% nas duas versões |
| M5 | Excluído | Solicitação explícita do usuário; `docs/scope.md` |
| M6 | Concluído | Pipeline completo `-RegenerateData` aprovado, 66 regressões, métricas e revisão técnica local |

## Entradas verificadas em 2026-10-12

Cinco NSP em `gamedump/` são containers PFS0 auditados por SHA-256. Base e update foram preparados localmente com as chaves fornecidas. As versões 1.0.0 e 3.0.3 foram confirmadas no NACP, independentemente dos nomes de arquivos. Firmware não foi necessária. DLCs foram auditados como entradas e não receberam decompilação independente.

## Limites preservados

Os nomes C++ originais das rotinas reconstruídas continuam desconhecidos. A identidade lógica EventFlagInt foi ligada por hash/factory/vtable nas duas versões; seu backend não foi reconstruído. A região terminal passou em 3.806 casos por build e o leitor C++ é injetado. RTTI é majoritariamente de middleware; nenhum layout completo de classe do executável foi declarado recuperado. Tipos BCSV conflitantes, enums desconhecidos, mensagens não resolvidas e altura PBC permanecem identificados. Consulte `findings/pilots.md` e `findings/formats.md`.

## Resultado consolidado

Cinco módulos C++ compiláveis passaram no Clang e no MSVC. Os 398 BCSV tiveram todos os campos comparados em 3.416.917 células. Os 1.331 EventFlow presentes foram catalogados; o fluxo-piloto fez round-trip nas duas versões. Os 5.053 MSBT do conjunto USen e os 80 schemas SMMH do alvo passaram no round-trip estrutural. Os 1.795 grids PBC foram comparados ao parser de referência.

O mapa multiversão contém 9.100 grupos candidatos de funções e 1.451 identidades RTTI associadas. Três vínculos receberam revisão individual: Murmur3 pelo contrato completo; construtor incorporado à factory e região terminal da query com escopo parcial. Nenhum nome foi transferido automaticamente.

Evidências finais: [metrics.md](metrics.md), [technical_review.md](technical_review.md), [version_delta.md](version_delta.md), [pipeline-verification.json](../metadata/pipeline-verification.json). Reprodução: [reproduction.md](reproduction.md). Os bancos Ghidra, inventários integrais e objetos de diff permanecem em `private/outputs` e `private/ghidra`.

Uma revisão humana independente e uma PR externa não foram registradas. Não há remote Git configurado; o trabalho permanece local para revisão. A publicação de dados proprietários e a integração Elysium não fazem parte da entrega.
