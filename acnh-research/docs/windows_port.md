# Goal: decompilação de ACNH e build Windows

Solicitação explícita do usuário em 2026-10-13. O goal anterior concluiu o plano de pesquisa incremental. Este goal amplia o escopo para o jogo executável no Windows; está **ativo e incompleto**. A integração Elysium continua excluída.

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

## Evidência de execução inicial

Os quatro NSO de cada versão passaram na verificação de segmentos. O perfil 1.0.0 contém 1.592 imports; o perfil 3.0.3 contém 1.688. Nenhum import forte ficou sem candidato de export. Isso verifica interfaces estáticas, sem provar o comportamento dos serviços.

A tradução automática 1.0.0 produziu 358 unidades C, 10.879.367 instruções incluídas e 197.118 regiões chamadas de funções pelo tradutor. Essa contagem inclui suas decisões de particionamento e não corresponde a funções recuperadas manualmente. A primeira DLL sem otimização teve 2.427.037.184 bytes e foi rejeitada pelo carregador Windows com erro 193. A DLL `-O1` teve 292.099.584 bytes, carregou e passou em 1.092 casos pela ABI do módulo. Duas entradas usam o C++ previamente reconstruído: Murmur3 e retorno constante zero. Entradas internas continuam com fallback interpretado.

O runtime SDL3/Vulkan passou nos onze testes upstream. O teste adicional `vulkan_headless` passou na GPU AMD Radeon RX 9070 XT. Os 68 shaders capturados compilaram offline em GLSL/SPIR-V; não foi usado um validador SPIR-V externo nesse teste. O RomFS em arquivo único tem header e extents válidos e SHA-256 registrado.

As execuções x64 de 45 e 90 segundos terminaram sem falha fatal. Elas submeteram frames e milhares de draws, mas as capturas apresentadas ficaram completamente pretas. Botões Plus/A foram injetados no teste de 90 segundos sem estabelecer gameplay. O contador de frames sozinho não valida boot visual. Criação do personagem, ilha, áudio, input funcional e save/reload continuam pendentes. Nenhuma build jogável foi declarada.

O patch do runtime em `patches/scarletnx-data-root.patch` permite selecionar os dados privados por `SNX_DATA_DIR` e contém traces condicionais de apresentação/readback. Os traces ajudam a distinguir targets intermediários do buffer exibido. O loader x64 já funciona; o problema de imagem preta continua em investigação.

No teste com captura de targets, 8 de 24 imagens tinham pixels diferentes de preto. A inspeção visual confirmou uma miniatura de terreno com grama e penhascos e um ícone de carregamento com palmeira. Outros targets eram cores uniformes, sem provar conteúdo útil. O trace do framebuffer aos 600 presents encontrou um único target correspondente ao endereço de memória, 1920×1080, escrito naquele frame. A hipótese de escolher um alias antigo apenas pela dimensão não foi confirmada nesse ponto. A investigação deve seguir o shader de composição, os recursos vinculados e a sincronização do frame final.

## Reprodução local

Usar os commits e o LLVM MinGW fixados em `config/windows-sources.lock.json`, além dos inputs e ferramentas do goal anterior. Executar de `D:/ACNH_Decomp`:

```powershell
& acnh-research/scripts/build_windows_bridge.ps1 -Backend tools
& acnh-research/scripts/build_windows_bridge.ps1 -Backend vulkan -GpuTest
& acnh-research/scripts/generate_windows_game.ps1
& acnh-research/private/tools/python/python.exe acnh-research/scripts/prepare_windows_inputs.py --keys gamedump/prod.keys
& acnh-research/scripts/build_windows_game.ps1 -Jobs 8
& acnh-research/private/tools/python/python.exe acnh-research/scripts/validate_bridge_replacements.py
& acnh-research/scripts/run_windows_bridge.ps1 -Mode native -Seconds 45 -Headless
```

Os testes de filesystem usam o temporário NTFS do Windows, pois o disco D: é exFAT e não suporta hard links. Execução dos drivers dentro do sandbox também pode falhar na canonicalização de caminhos; o resultado registrado foi obtido fora dessa restrição. A build conserva os objetos intermediários para retomar compilações. A opção `-Regenerate` refaz C privado a partir dos módulos e hints observados. O primeiro estágio H.264/Opus está desabilitado; não foi validado como desnecessário para todos os cenários do jogo. As flags `-march=native` exigem reproduzir ou ajustar o alvo de CPU antes de distribuir executáveis para outra máquina.
