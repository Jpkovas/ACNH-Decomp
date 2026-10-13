# Goal: decompilação de ACNH e build Windows

Solicitação explícita do usuário em 2026-10-13. O goal anterior concluiu o plano de pesquisa incremental. Este goal amplia o escopo para o jogo executável no Windows; está **incompleto**. A integração Elysium continua excluída. O agendador registrou `blocked` durante falhas de capacidade do modelo em tentativas anteriores; a execução técnica deste turno continuou com progresso. Esse estado do agendador não representa conclusão do projeto.

O primeiro alvo de execução é 1.0.0, com a pesquisa 3.0.3 preservada. O trabalho existente recuperou apenas rotinas delimitadas. Não existe ainda uma build jogável validada, nem código-fonte recuperado para o jogo completo.

## Critérios de conclusão

Uma build Windows x64 reproduzível deve iniciar o jogo real, permitir criar o personagem, chegar à ilha, movimentar e interagir, apresentar gráficos e áudio, aceitar controles e salvar/carregar o progresso. Cada etapa terá evidência de execução, versão dos inputs e revisão das dependências restantes. Código traduzido automaticamente, código ARM64 interpretado, serviços simulados e código reconstruído manualmente terão métricas separadas. Um executável que só inicia o runtime ou produz um quadro sintético não satisfaz o goal.

## Sequência de trabalho

1. Verificar todos os NSO do ExeFS, imports/exports, relocations e inicializadores; preparar um perfil de módulos de ACNH.
2. Compilar uma ponte de execução Windows, testar seu tradutor e obter um trace de inicialização com os módulos reais.
3. Corrigir carregamento, memória, threads, filesystem e serviços obrigatórios usando contratos observados no jogo.
4. Implementar ou adaptar gráficos, controles e áudio; validar o primeiro quadro e o avanço da inicialização.
5. Recuperar em C/C++ os sistemas de jogo, substituindo gradualmente rotinas originais com comparações e testes de comportamento.
6. Validar criação do personagem, gameplay, salvamento e reprodução da build a partir de instruções e versões fixadas.

## Referências fixadas

ScarletNX fornece um carregador genérico de NSO, tradutor AArch64 para C, serviços Horizon e backend Maxwell/Vulkan. Será avaliado como ponte diagnóstica. SSBU Recomp fornece exemplos de tradução AArch64 e adaptação NVN/serviços para Windows, mas seu pipeline contém endereços e estruturas específicos de SSBU; não será aplicado diretamente como se fosse um port de ACNH. As revisões e licenças estão em `config/windows-sources.lock.json`.

Os repositórios upstream permanecem em `vendor/`, os arquivos traduzidos e dados do jogo em `private/` ou `build/`, fora do Git. Chaves, firmware e assets não serão incluídos nos arquivos publicáveis. A dependência de cada ferramenta será registrada; nenhuma condição do plano antigo que limitava o objetivo a pilotos será usada para declarar este goal concluído.

## Áudio nativo em validação

`windows_audio/` liga o protocolo IAudioRenderer ao AudioRenderer de `Ryujinx.Audio`, revisão `fec4f4ada9f28f897457033f9954c84cc15d0b02`, sob MIT. O módulo inclui DSP, ADPCM, resampling, efeitos, mixes e splitters dessa dependência. Seu único contrato com o antigo namespace de CPU é um relógio `ElapsedSeconds`; não compila o emulador de CPU. NativeAOT gera `ACNH_audio.dll`, carregada pelo runtime Windows. A memória do jogo permanece sob controle do runtime e cada acesso do DSP passa pela verificação de mapeamento/permissão. O evento de atualização pertence a cada renderer e segue seu processamento; Start/Stop e RequestUpdate usam os estados reais do DSP.

A saída Windows usa PCM16 estéreo a 48 kHz pelo `waveOut`, com buffers copiados antes de retornar ao DSP. O teste de 90 segundos `native-20261013-054422` abriu o dispositivo e produziu 89,27 segundos de PCM, com cerca de 3,08 milhões de amostras não nulas por canal e nenhuma saturação. Isso verifica sinal e encaminhamento ao dispositivo; não equivale a uma comparação perceptual ou com hardware. A imagem parou em 652 frames durante esse teste, com headers gráficos inconsistentes. A falha gráfica já apareceu em testes anteriores e continua sob investigação.

Quatro testes construídos sem assets verificam amostras conhecidas PCM16/ADPCM, volumes 1 e 0,25, mute, término dos buffers e contadores de consumo. A validação não cobre todos os coeficientes ADPCM, filtros, efeitos e splitters contra hardware. `metadata/windows/1.0.0/native-audio-validation.json` registra a DLL efetivamente testada. O build ainda emite um aviso de trimming em `Ryujinx.Common`; as rotas exercitadas passaram, mas o aviso precisa de revisão para módulos adicionais. O HLE antigo permanece silencioso quando o módulo não é selecionado.

Preparação e reprodução, a partir da raiz `D:/ACNH_Decomp`:

```powershell
& acnh-research/scripts/prepare_windows_audio.ps1
& acnh-research/scripts/build_windows_audio.ps1
& acnh-research/scripts/build_windows_bridge.ps1 -Backend vulkan -Jobs 4 -GpuTest
& acnh-research/private/tools/python/python.exe acnh-research/scripts/validate_windows_audio.py
& acnh-research/scripts/run_windows_bridge.ps1 -Mode native -Seconds 90 -Headless -NativeAudio -CaptureAudioInputs
```

O SDK .NET privado é fixado por SHA-512. Fontes, licenças e dependências NuGet ficam locais. As capturas PCM e os pacotes/coeficientes extraídos do jogo ficam exclusivamente em `private/`. `-AudioWavOnly` valida a geração sem abrir o dispositivo sonoro e não conta como saída sonora do Windows. Para adaptar comandos à tela observada, `-LiveInput` fornece um CSV privado recarregado a cada 100 ms; alterações do `.ini` não substituem os argumentos explícitos do teste.

O teste seguinte `native-20261013-061039` terminou após 900,68 segundos, mantendo imagens e PCM ativos, com 897,67 segundos capturados e nenhuma saturação ou falha registrada no dispositivo. Os prefixes de FIFO amostrados não mudaram entre enqueue e execução; isso não cobre o conteúdo integral dos buffers. O cadastro mostrou a regra real de no máximo cinco números no nome. Dois comandos adaptativos foram agendados tarde demais e não executaram, como registrado nos arquivos privados; não contam como validação de entrada. Para evitar isso e repetição de caracteres, `send_windows_input.ps1` calcula o tempo do processo, verifica seu prazo e produz `ms:hex:duração`. Uma execução estável com diagnóstico não resolve a causa das paradas anteriores.

## Predicado EventFlagInt integrado

A região `main+0x40685c..0x406a2c` agora chama `acnh_flag_int_predicate` no handler ligado a EventFlagInt. O handler completo continua parcialmente traduzido: parsing de AccessKey, seleção dos backends SaveIO e entradas internas distintas continuam originais. O epílogo original restaura os registradores e a pilha. A DLL candidata de 292.553.216 bytes passou em 5.170 casos pela ABI: 1.088 de hash, quatro do retorno zero, 272 de FullKey e 3.806 do predicado/epílogo. São três entradas completas delimitadas e **uma região parcial**, sem declarar o handler completo recuperado. Evidência em `replacements-validation.json` e `reconstructed-replacements.json`. A DLL em teste real usa SHA-256 `4e9d96da793ef1e2d056cb187aea79d8b16aaf06880b00b081d308336d21123a`.

O teste dessa DLL `native-20261013-063158` encerrou com código zero após 1.801,31 segundos. Os controles recarregados confirmaram nome, aniversário e aparência, passaram pela escolha de hemisfério e alcançaram a confirmação da ilha. A captura PCM contém 1.797,14 segundos em estéreo, sem amostras saturadas ou erro registrado no dispositivo. O cenário 3D do aeroporto desaparece depois da aparência e a prévia da ilha não mostra terreno. A interface continua ativa, mas esses problemas, o gameplay na ilha, save/reload e a recuperação restante do código impedem validar uma build jogável. O teste terminou; não ficou um processo de jogo em execução.

## Evidência de execução inicial

Os quatro NSO de cada versão passaram na verificação de segmentos. O perfil 1.0.0 contém 1.592 imports; o perfil 3.0.3 contém 1.688. Nenhum import forte ficou sem candidato de export. Isso verifica interfaces estáticas, sem provar o comportamento dos serviços.

A tradução automática 1.0.0 produziu 358 unidades C, 10.879.367 instruções incluídas e 197.118 regiões chamadas de funções pelo tradutor. Essa contagem inclui suas decisões de particionamento e não corresponde a funções recuperadas manualmente. A primeira DLL sem otimização teve 2.427.037.184 bytes e foi rejeitada pelo carregador Windows com erro 193. A DLL `-O1` teve 292.099.584 bytes, carregou e passou em 1.092 casos pela ABI do módulo. Duas entradas usam o C++ previamente reconstruído: Murmur3 e retorno constante zero. Entradas internas continuam com fallback interpretado.

O runtime SDL3/Vulkan passou nos onze testes upstream. O teste adicional `vulkan_headless` passou na GPU AMD Radeon RX 9070 XT. Os 68 shaders capturados compilaram offline em GLSL/SPIR-V; não foi usado um validador SPIR-V externo nesse teste. O RomFS em arquivo único tem header e extents válidos e SHA-256 registrado.

As execuções x64 de 45 e 90 segundos terminaram sem falha fatal. Elas submeteram frames e milhares de draws, mas as capturas apresentadas ficaram completamente pretas. Botões Plus/A foram injetados no teste de 90 segundos sem estabelecer gameplay. O contador de frames sozinho não valida boot visual. Criação do personagem, ilha, áudio, input funcional e save/reload continuam pendentes. Nenhuma build jogável foi declarada.

O patch do runtime em `patches/scarletnx-data-root.patch` permite selecionar os dados privados por `SNX_DATA_DIR`, contém traces opcionais e corrige limpezas e draws condicionais do Maxwell. A falha que apagava a composição inicial foi localizada e corrigida; isso ainda não valida gameplay.

No teste anterior com captura de targets, 8 de 24 imagens tinham pixels diferentes de preto. A inspeção visual confirmou uma miniatura de terreno com grama e penhascos e um ícone de carregamento com palmeira. Outros targets eram cores uniformes, sem provar conteúdo útil. O trace do framebuffer aos 600 presents encontrou um único target correspondente ao endereço de memória, 1920×1080, escrito naquele frame. A hipótese de escolher um alias antigo apenas pela dimensão não foi confirmada nesse ponto.

## Correção da composição inicial

A captura privada RenderDoc mostrou o ícone de carregamento no target de composição após o draw 1342, seguido de quatro `vkCmdClearAttachments` que zeravam esse mesmo target antes do draw de cópia 1381. Os vértices transformados e as texturas tinham conteúdo válido. O rastreamento dos métodos revelou `SET_RENDER_ENABLE_C=4` (comparar registros e renderizar se diferentes), ignorado pelo runtime. Ambos os pares sequência/contador estavam zerados; portanto essas limpezas deveriam ser omitidas. O front end agora avalia o predicado antes de limpezas e draws, incluindo o override por registrador, e inicializa o modo padrão como sempre renderizar.

Também havia uma leitura incorreta de `SET_CLEAR_SURFACE_CONTROL`: os seletores de clear rectangle, scissor e viewport clip são independentes. A correção usa os registradores correspondentes e intersecta as regiões com o attachment. A referência de bits é o [header Maxwell B publicado pela NVIDIA](https://github.com/NVIDIA/open-gpu-doc/blob/master/classes/3d/clb197.h). O layout dos pares de comparação foi conferido no [driver Nouveau](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/gallium/drivers/nouveau/nvc0/nvc0_query_hw.c) e na implementação original de [condições Maxwell](https://ni.4a.si/anonymous/yuzu/commit/src/video_core/engines/maxwell_3d.cpp?follow=1&id=a78372110ceedf5e3ad71a4b72bb1fd8b3b5f628). Essas referências orientam a compatibilidade da ponte e não representam código do jogo reconstruído.

O teste `vulkan_headless` agora lê pixels RGBA da GPU e verifica retângulo próprio, scissor, interseção com viewport, região vazia e condições que preservam ou substituem o attachment. Na execução do jogo de 90 segundos após a correção, a captura apresentada em 1920×1080 tinha 785.280 pixels não pretos e mostrava a placa Nook Inc. da introdução. Um teste de 180 segundos com dez entradas A terminou em 193,56 segundos e apresentou Timmy e Tommy no balcão do aeroporto, com 2.073.598 pixels não pretos. Isso comprova avanço visual da introdução; não confirma que as entradas avançaram um diálogo. O módulo x64 do jogo permaneceu com o mesmo hash; a alteração foi no runtime. Novos avisos de headers de comandos inesperados surgiram durante o avanço e precisam de diagnóstico. Criação de personagem, ilha, áudio e salvamento continuam sem validação.

RenderDoc 1.46 foi instalado de fonte oficial com SHA-256 e assinatura GPG verificados, registrados em `config/tool-renderdoc.lock.json`. Capturas, imagens e arquivos de replay ficam em `private/windows/`. A camada Vulkan é habilitada somente no processo de diagnóstico. O SDK opcional é detectado pelo script de build. Para o replay sem interface, a configuração recém-criada do RenderDoc recebeu somente o opt-out de analytics, com backup privado, pois o diálogo inicial interrompia `qrenderdoc --py`.

## Controles reconstruídos e cadastro

O SDK 1.0.0 exporta `nn::hid::detail::GetNpadStates(NpadFullKeyState...)`, localizado no offset `0x341a00`. Seu corpo de 504 bytes foi reconstruído em `reconstructed/src/npad_full_key.cpp`: seleção cronológica de snapshots no ring de 17 entradas, verificação dos carimbos de leitura, retry quando o produtor altera uma entrada, limite de capacidade e filtro dos botões de direção opostos. Os controles do filtro são relidos em cada estado, como no original. A rotina coincidiu com ARM64 não modificado em 3.147 casos, incluindo todos os tails, 17 alterações do produtor e 17 mudanças do filtro durante a leitura. A inicialização do SDK foi isolada nesse teste e continua delegada ao código original pela ponte; não se afirma reconstrução do SDK completo.

A DLL agora substitui três entradas: duas de `main` e esse leitor do SDK. A validação da ABI passou em 1.364 casos, dos quais 272 verificam a adaptação do leitor, a seleção dos IDs de controle e a preservação dos registradores. O módulo atualizado tem 292.552.704 bytes. O link estático inclui o suporte C++ necessário para não exigir `libc++.dll` ao carregar o módulo na máquina de destino.

Pressões A de um segundo avançaram os diálogos e selecionaram caracteres no teclado desenhado pelo jogo. A confirmação por Plus abortava com `0x202` dentro de `nn::ngc::ProfanityFilter`: o runtime fornecia um RomFS vazio para o arquivo de sistema `0100000000000823`. O script `prepare_system_archive.py` localiza esse NCA nos 238 cabeçalhos da firmware fornecida, usa hactool 1.5.4 com saída sanitizada e instala seu RomFS de 98.324 bytes em `private/windows/bridge/ACNH_1_0_0_data/system/archives/`. Chaves, NCA e RomFS ficam fora do Git. A sessão subsequente com a rotina reconstruída passou pela validação do nome e chegou à seleção de aniversário; `metadata/windows/1.0.0/intro-input-validation.json` registra os runs.

Outra sessão com o arquivo real parou antes do cadastro. Uma amostra de backtrace do processo confirmou o thread da GPU executando `dma_method`/`bl_offset`, enquanto o principal esperava o evento nvhost. Esse atraso e os headers inesperados ainda precisam de diagnóstico; `SNX_DMA_TRACE=1` registra os parâmetros de cada cópia sem omiti-la. O áudio ainda é uma implementação de timing que não produz som, conforme `runtime/hle/audren.c` e `audio.c`; será necessário implementar o processamento e a saída de áudio. Aniversário confirmado, criação completa do personagem, gameplay na ilha e save/reload ainda não foram demonstrados.

## Reprodução local

Usar os commits e o LLVM MinGW fixados em `config/windows-sources.lock.json`, além dos inputs e ferramentas do goal anterior. Executar de `D:/ACNH_Decomp`:

```powershell
& acnh-research/scripts/build_windows_bridge.ps1 -Backend tools
& acnh-research/scripts/build_windows_bridge.ps1 -Backend vulkan -GpuTest
& acnh-research/scripts/generate_windows_game.ps1
& acnh-research/private/tools/python/python.exe acnh-research/scripts/prepare_windows_inputs.py --keys gamedump/prod.keys
& acnh-research/private/tools/python/python.exe acnh-research/scripts/prepare_system_archive.py --keys gamedump/prod.keys --firmware gamedump/Firmware_22.1.0.zip --title-id 0100000000000823
& acnh-research/scripts/build_native.ps1 -Compiler clang
& acnh-research/private/tools/python/python.exe acnh-research/scripts/validate_npad_full_key.py --library acnh-research/build/clang/npad_full_key.dll
& acnh-research/scripts/build_windows_game.ps1 -Jobs 8
& acnh-research/private/tools/python/python.exe acnh-research/scripts/validate_bridge_replacements.py
& acnh-research/scripts/run_windows_bridge.ps1 -Mode native -Seconds 45 -Headless
```

Os testes de filesystem usam o temporário NTFS do Windows, pois o disco D: é exFAT e não suporta hard links. Execução dos drivers dentro do sandbox também pode falhar na canonicalização de caminhos; o resultado registrado foi obtido fora dessa restrição. A build conserva os objetos intermediários para retomar compilações. A opção `-Regenerate` refaz C privado a partir dos módulos e hints observados. O primeiro estágio H.264/Opus está desabilitado; não foi validado como desnecessário para todos os cenários do jogo. As flags `-march=native` exigem reproduzir ou ajustar o alvo de CPU antes de distribuir executáveis para outra máquina.

Para repetir o teste de cadastro, usar `run_windows_bridge.ps1 -PressLength 1000 -ShotEvery 250` com a sequência A/Plus de `intro-input-validation.json` e dos logs privados referidos. O limite do harness é 1.800 segundos; o teste pode terminar antes com erro do jogo. `build_windows_game.ps1 -OutputDirectory <pasta em private/windows>` permite preparar outro módulo sem relinkar a DLL de uma sessão em execução. A emissão do módulo para outra pasta não altera os dados privados selecionados por `SNX_DATA_DIR`.

Para capturar dois frames consecutivos de GPU, instalar o arquivo portátil RenderDoc fixado no lock em `private/tools/renderdoc/`, recompilar a ponte e executar:

```powershell
& acnh-research/scripts/capture_windows_gpu.ps1 -Frame 500 -Seconds 90
$env:ACNH_RESEARCH_ROOT='D:/ACNH_Decomp/acnh-research'
$env:ACNH_RENDERDOC_CAPTURE='caminho absoluto da captura .rdc privada'
& acnh-research/private/tools/renderdoc/RenderDoc_1.46_64/qrenderdoc.exe --py acnh-research/scripts/renderdoc_inspect_capture.py
```

O replay fornece actions, recursos, vértices transformados, histórico de pixels e imagens privadas. Por padrão escolhe o primeiro target de pelo menos 1280×720 e até 24 draws para inspeção. Para repetir a primeira análise causal, selecionar `ACNH_RENDERDOC_TARGET='ResourceId::131'` e `ACNH_RENDERDOC_EVENTS='1173,1342,1346,1381'`. Capturas de outros trechos podem exigir outros IDs e coordenadas. Desativar o diálogo de analytics na primeira inicialização do RenderDoc antes de usar `--py` sem interface. Para traces de predicados e limpezas, usar `SNX_CONDITION_TRACE=1` e `SNX_CLEAR_TRACE=1` somente no processo de diagnóstico.
