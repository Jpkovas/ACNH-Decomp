# Execução do goal

Goal atual: **ativo e incompleto**, decompilar ACNH e produzir uma build nativa jogável para Windows. A versão 1.0.0 é o primeiro alvo executável, e a pesquisa 3.0.3 foi preservada. Integração Elysium excluída pelo usuário. Critérios em [windows_port.md](windows_port.md).

O marco Windows de 2026-10-13 chegou à ilha, permitiu caminhar do píer até a grama e sacudir uma árvore, derrubando suas frutas. A sessão `native-20261013-101631` terminou com código zero em 1.800,73 segundos. A cena do aeroporto continuou correta após permanência longa no editor de aparência: a correção reteve oito slices GPU com idade de 5.400 frames. Capturas e logs permanecem privados.

O filme de introdução ficou preto porque o job usa codec 9, VP9, ainda ignorado pela ponte. Os 11 casos próprios H.264 aprovados não validam esse filme. Movimentação e interação básica com árvore foram observadas; NPCs, inventário, save/reload e estabilidade geral ainda precisam de validação. O áudio deste run foi capturado como PCM estéreo por 1.796,665 segundos, sem saturação; modo WAV-only não comprova saída no dispositivo Windows. Um run anterior registrou falha no dispositivo após 708,88 segundos.

A execução usa uma ponte híbrida: tradução automática ARM64 para C/x64, serviços/GPU por compatibilidade e interpretação de entradas internas. A decompilação manual permanece em **três entradas completas, uma região parcial e uma entrada guardada**. O parser AccessKey passou em 1.392 casos contra ARM64 original, a região de namespace em 90 e o helper de tokenização em 3.414; namespace/helper ainda não substituem entradas do jogo.

A candidata posterior restringe o parser guardado aos 12 callers revisados e exige proveniência compilada. Sua validação ABI é separada do run acima, que usou a revisão anterior. Os resultados constam em `access-key-bridge-validation.json`; as três entradas e o predicado EventFlagInt passam em 5.170 casos. A runtime passou 13 testes, incluindo regressão física do volume 3D e dez casos de report semaphore. O diagnóstico integral do primeiro header FIFO suspeito está disponível; a causa da corrupção intermitente permanece pendente.

A publicação contém fonte própria, ferramentas, patches abertos e relatórios agregados, com auditoria da árvore e do histórico Git. Dumps, chaves, assets, bancos Ghidra, capturas e fonte levantada automaticamente ficam fora do repositório. Consulte [publication.md](publication.md) e [LICENSE_NOTES.md](../LICENSE_NOTES.md).

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

Uma revisão humana independente e uma PR externa não foram registradas. O usuário autorizou publicar marcos no repositório Jpkovas/ACNH-Decomp; auditoria e critérios estão em publication.md. A publicação de dados proprietários e a integração Elysium não fazem parte da entrega.
