# Marco técnico da candidata integrada de 35 entradas

Coordenação: `01a13734-dae4-73f2-87e4-e4a88be7d1da`. Agregação: `memory_pin`.
Data local: 2026-10-13; horários abaixo em UTC.

A candidata com **35 corpos reconstruídos / 4.696 bytes originais** passou nos
gates do SnxModule real e, em um run Windows de 180 segundos, chegou ao diálogo
inicial de Timmy/Tommy com PCM não zerado. O processo terminou naturalmente
com exit 0; o harness também terminou com exit 0. Esse resultado sustenta a
recomendação de aceite técnico da candidata integrada e do startup observado.
O coordenador aceitou essa base no receipt separado
`metadata/windows/1.0.0/player35-coordinator-acceptance.json`.

O default continua na seleção de 14 entradas, e a métrica pública histórica
continua **14 / 2.212 bytes**. Esta entrega não edita
`config/windows-goal.json`, `decompilation-byte-coverage.json`, registry,
defaults ou provas históricas. Publicação e promoção de default não foram
executadas. O projeto completo permanece incompleto: a execução ainda é
híbrida; gameplay/tutorial, interação de input, save/reload real e build limpa
reproduzível continuam necessários.

## Par executado e provas vinculadas

| Evidência | SHA-256 |
| --- | --- |
| DLL da candidata35 | `5829252d9988715a4727ed015f216675b0b0b3ac06c8a639caac65afeb09cd9b` |
| Runtime35 e EXE empacotado | `df489bdd58d0304bd0f924cd9a753ec67d52ca0e28a47562251b2fa695083658` |
| Manifesto privado35 | `a72b4aa84de92d854e0e857cdb5417ecb50fac68c689e0482feadc9d07784983` |
| Snapshot histórico de integração | `05d8258a85d0b7a77850fa6ef60a2aa65a84f5d2ef954fb38bbdc55d4b951004` |
| Preflight do run35 | `eb4a106b6d45398da9fa62fa3bf8db97a629c8cfe3b5a837b1041f387160b2fd` |
| Medição privada regenerada pelo coordenador | `aece9af37b2236111688c32fe4dccb62375511da9ec33464aee8a3d45f54a796` |
| Verificador próprio | `bac6d62dac0e14b3bfe1630923f2c7b26d13b5e343e771ad9ac30b251ac2da3d` |
| Agregado final, público e cópia privada idênticos | `58c1ea1ecd6dd381929579018034d908f25b33f0092e54339994f738d4c3c856` |
| Default DLL preservado | `2797747f4e69977388ff27cf9d04341b2b55a631a9c739f30351b7101a9a730d` |
| Default runtime restaurado | `dfe9256e44081bdeefa30c6b87e18442c0eade390cc919ff1d401be7c96c7f94` |

O agregado é
`metadata/windows/1.0.0/startup-player35-team-validation.json`, com cópia
idêntica em `private/team/player35-startup/acceptance-validation.json`.
O registro da execução do verificador, incluindo argv, intérprete, versões,
hashes e duração, está em `private/team/player35-startup/acceptance-execution.json`.
A revisão independente fica em `private/team/player35-startup/acceptance-review.md`.
Seu SHA-256 é `5ed1344b94eeb6841d0ea45b90fad95d1cc58e18c02f9b346eaa54fbb5f385c0`;
ela conferiu 131 bindings de 128 arquivos, 80 capturas, 15 gates/logs,
38 arquivos públicos/reference preservados e os dois ajustes pós-run.
A versão agregada `b35a17cc47b81d254d9209f2ea042f85593576f163b045c1526f147cbaee166d`,
usada no aceite inicial, foi preservada em
`private/team/player35-startup/acceptance-before-final.json`. O fechamento
posterior atualizou apenas os registros de hashes/mtime atuais dos dois
arquivos de orquestração pós-run; não alterou fatos do run, gates ou numerador
histórico. O coordenador confirmou o receipt com o agregado final separado.
O campo `coordinator_acceptance_pending` do agregado descreve a recomendação
na fase de agregação; o receipt separado é a autoridade da aceitação efetiva.
Os hashes da tabela identificam os bytes locais históricos. O receipt também
registra o hash da forma LF do agregado para conferir o texto publicado após
a normalização de finais de linha pelo Git.

O manifesto contém os 14 corpos anteriores mais quatro bancos de player
(728 bytes) e dezessete corpos da árvore de resolução (1.756 bytes).
Os **21 / 2.484 bytes adicionais pertencem à candidata integrada testada**;
não são contagem de candidatas isoladas, infraestrutura ou chamadas repetidas.
Há 35 intervalos originais distintos sem sobreposição. O denominador continua
44.815.680 bytes `.text` dos quatro NSOs do ExeFS 1.0.0. A proxy da candidata é
**0,010478475390756092%**, separada da proxy do default histórico. Nenhuma
infraestrutura acrescenta bytes ao numerador.

Os dois processos player atuais passaram em 246 comparações cada: 186 retornos
terminais e 60 prefixos prescritos. Os processos SaveIO, com e sem API2,
passaram em 150 casos nativos, 15 sentinelas de guard, cinco sentinelas de
interior e seis fallbacks originais definidos cada. As provas core/context/
flag/AccessKey/Npad também vinculam a mesma DLL e o manifesto final.
Os 13 CTests e quatro cenários de loader do runtime são **provas históricas
do snapshot**, conferidas novamente por hashes/logs pelo agregador; nenhum
compiler, loader fixture, CTest ou jogo novo foi executado nesta agregação.

As distinções anteriores continuam válidas: SaveIO e Npad têm dependências
declaradas como modelos nos seus fixtures; a prova player executa corpos
nativos das dependências originais e compara apenas as fronteiras de dispatch
observáveis como subsequências ordenadas. Interiores passados ao wrapper,
observer handoffs de NULL, kernel primitives e prefixos não viram novas
entradas completas. O run real não instrumentou chamadas individuais de todas
as 35 entradas nem hits/leases da API epoch, portanto não estabelece cobertura
dinâmica integral dessas rotinas.

## Terminal, imagem e áudio

O run privado é `player35-team-20261013-203659`, PID 13736. O processo iniciou
em 23:39:36.6360452Z e o terminal foi observado em 23:42:42.0083810Z.
O processo durou **180,984 s**; o harness, com pós-processamento, **186,212 s**.
O relatório confirma handle capturado, processo ausente, filho de análise
ausente, ambiente restaurado e liberação da mesma lease. Não houve kill,
timeout forçado ou erros registrados no harness/pós-processamento. A saída
normal corresponde à janela configurada de 180 segundos, não ao término do jogo.

O stderr termina em **1.980 frames**, hash de frame do runtime
`86027761510aba45`; o stdout está vazio. Os hashes dos três logs e do CSV vazio
ficam no agregado. As 80 capturas PPM são estruturalmente completas e têm
hashes individuais; pixels, PCM e logs completos permanecem privados.

O coordenador e o revisor `memory_pin`, ambos agentes AI, inspecionaram
visualmente a conversão PNG privada da captura `_0072.ppm`. Viram Timmy,
os dois personagens da recepção, o diálogo inicial, o overlay completo e a
seta de continuação. A atribuição é uma observação visual explícita dos
agentes; o verificador não infere diálogo de RGB não zerado ou de frames.
Também conferiu que o RGB do PNG é idêntico byte a byte ao PPM. Essa imagem
não comprova avião/terrain, tutorial concluído ou gameplay.

| Arquivo privado | SHA-256 |
| --- | --- |
| PPM `_0072` inspecionado | `e895652c2f6368980b198ce09025a6385b961a88e0823f1a1f55b73492810ff9` |
| PNG lossless correspondente | `f0774b51c12c7f5c388d45393a7db1764857f980ded9e11a6b57a863c1de7a86` |
| WAV cru | `b0d33abe536c9ffa9044e27088a542edbf6d0ff894a8131f2678457453f9cf51` |
| WAV final | `ec93a779d592489d4eb11cbcfdb3a2750647d29084b1076e051ecd82c0c0359c` |

O WAV contém **8.516.880 frames PCM / 177,435 s**, estéreo 48 kHz / 16 bits.
O verificador recalculou as métricas a partir do PCM final e confirmou o
relatório de análise. São 6.293.723 amostras não zeradas no canal esquerdo e
6.290.810 no direito, total **12.584.533**, com zero clipping detectado.
Os picos são 13.000/11.993; RMS 532,9383567065554/526,6479372366158.
O WAV cru e final têm o mesmo payload PCM e diferem apenas nos dois tamanhos
RIFF/data do cabeçalho, finalizados depois da saída do produtor. Hash de análise,
script/executável do analisador e layout completo estão no agregado.
PCM não zerado e ausência de clipping não provam precisão perceptual do áudio.

## Comparação controlada

| Run | Seleção | Duração registrada | Frames | PCM não zerado | Observação visual atribuída |
| --- | --- | ---: | ---: | ---: | --- |
| `native-20261013-182810` | 9 | 180,980 s | 2.056 | 13.562.254 | Diálogo, registro anterior do coordenador/handoff |
| `native-20261013-183257` | 14 default | 180,740 s | 204 | 0 | Carregamento, comparação anterior do coordenador |
| `epoch-team-20261013-194828` | 14 epoch | 181,019 s | 1.945 | 12.528.054 | Diálogo, capturas vinculadas ao agregado epoch congelado |
| `player35-team-20261013-203659` | 35 integrada | 180,984 s | 1.980 | 12.584.533 | Diálogo inicial, inspeção atual dos dois agentes |

Os controles gravados coincidem: native/headless, docked 1, input script vazio,
live input habilitado com CSV vazio, press length 1.500 ms, shot every 25,
native audio/VP9, WAV-only false e capturas de filesystem/FIFO/gráficos.
Audio/VP9 têm os mesmos hashes em todos; RenderDoc também coincide entre
os dois runs com harness novo. Os relatórios legados de 9/14 não registram
RenderDoc SHA ou requested-seconds diretamente, nem os handles/ausência/cleanup
do harness novo. Suas durações são `elapsed_seconds` legadas, enquanto epoch/35
usam `process_elapsed_seconds`. Essa diferença é preservada no agregado.

O avanço ao diálogo, com o par de 35 entradas, demonstra progresso de startup
comparado ao default14 que ficou carregando. Epoch14 já havia recuperado esse
startup; player35 preserva o progresso com a seleção ampliada. Não é uma
repetição de estabilidade, teste de velocidade ou isolamento causal: runtime,
provider e seleção de módulos mudaram entre pares. Contagem de frames também
não certifica a precisão dos gráficos; avisos do backend continuam presentes.

O digest ROMFS foi reaproveitado do preflight epoch após conferir o mesmo
tamanho e mtime, inclusive novamente pelo agregador. A referência e o digest
estão vinculados no relatório; os 6,6 GB não foram rehashados neste run.
Essa limitação não é apresentada como verificação criptográfica nova do ROMFS.

## Fontes históricas e mudanças de build posteriores

A prova de startup35 permanece vinculada às **33 fontes do snapshot05d8 e ao
preflight**, com as fontes reconstruídas, API/epoch, core/main/mem, generated
TUs, manifestos, relatórios ABI e DLL/runtime exatos. A build histórica
reutilizou 376 objetos donor verificados e compilou 13 unidades novas. Não é
uma build limpa completa nem uma prova de reprodução entre máquinas.

Depois do terminal, o coordenador autorizou `pin_review` a alterar apenas
`scripts/build_windows_game.ps1` e `windows_bridge/CMakeLists.txt` para a rota
Clean/CPU explícita. As cópias anteriores estão em
`private/team/publication35-review/pre-change/`; snapshot criado em
**2026-10-14T00:03:58.5801878Z**. Os before-hashes são exatamente os históricos:
gamebuild `521189a61dfa4d209b5fae8a889d09f8404b12e9a533d9bdb5143cd37bb11b61`
e CMake `57adf28144793105ca274698f48156f3cfd58b8c675ad85d31229ba188a63864`.

O verificador usa essas before-copies para os dois bindings históricos,
registra os hashes atuais separadamente como mudanças pós-run autorizadas,
e exige integridade estrita das outras 31 fontes e das provas/binaries.
mtime é uma observação de arquivo, não prova forense independente de tempo.
Essa autorização vem da mensagem do coordenador e é restrita aos dois arquivos.
A revisão atual registra gamebuild
`32e3382fe1a36812205a4dc44c99f928cdcf5b5ae5838a53fab50ae748c9f38e`
e CMake `18df28b8e1cc03753d26a5a7591840dbc092ae27f4db0106b31e8bfcfc6aa0b6`.
A rota nova não foi utilizada para produzir a DLL5829/runtime df48 nem recebe
prova de clean build, portabilidade de CPU ou novo runtime por este run.
As versões históricas de script/relatórios14 permanecem congeladas.

## Reexecutar o verificador

Foi usado o Python do bundle Codex **3.12.14**, com **Pillow 12.3.0 já disponível**.
O `private/tools/python/python.exe` do projeto não tinha PIL e não foi alterado.
O hash do intérprete e argv exatos da execução bem-sucedida estão no registro
privado `acceptance-execution.json`. Essa ferramenta é só de verificação offline,
não integra a build/runtime do jogo.

```powershell
$verificationPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $verificationPython -B scripts/report_team_player35_startup.py `
  --observer 'Root coordinator and memory_pin reviewer (AI agents)' `
  --visual-observation 'Both AI observers inspected the private PNG: Timmy initial dialogue, two reception characters, complete dialogue overlay and continuation arrow are visible. No plane, terrain, tutorial completion or gameplay is established.'
```

Executar a partir de `D:/ACNH_Decomp/acnh-research`, com os arquivos privados
correspondentes presentes. O verificador não inicia jogo, build ou gate novo;
ele rehasha evidência, confere PCM/PNG/PPM/terminal e gera apenas seu agregado.
Os defaults devem estar restaurados antes da execução; não rodar enquanto
outra build modifica o runtime no cache compartilhado. Falha gera registro
privado `acceptance-failure-*` e não é aceite. A aceitação e eventual publicação
do marco pelo coordenador são decisões/documentos separados.

Assets, dumps, instruções/lifted code, firmware, chaves, capturas e áudio crus
ficam privados. Elysium permanece excluído. Nenhuma afirmação deste marco
substitui a validação de uma build Windows jogável com boot, gameplay/input,
áudio e salvamento reais, código reconstruído suficiente e build reproduzível.
