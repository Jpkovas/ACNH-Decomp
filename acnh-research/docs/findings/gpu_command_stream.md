# Diagnóstico do fluxo de comandos GPU

O run local `native-20261013-083657` apresentou cabeçalhos incomuns por volta de 32 segundos. As primeiras palavras observadas parecem pares de índices de 16 bits. Em seguida, o fluxo interpretou `0x3f800000` como parte de uma espera de syncpoint e de um batch com 8.064 palavras. As fences incompletas apareceram depois desses eventos. Isso demonstra perda de integridade ou de alinhamento do fluxo, mas ainda não identifica quem a causou. Esse run não produziu snapshots completos do FIFO.

O parser conserva batches que atravessam entradas GPFIFO. A documentação pública NVIDIA também permite que os dados de um método estejam em um segmento diferente do cabeçalho. Não se deve eliminar essa continuidade para ocultar a falha. A referência consultada descreve uma geração posterior de GPU e serve como confirmação do formato público, sem substituir a validação do GM20B: [NVIDIA Host Pushbuffer Format](https://github.com/NVIDIA/open-gpu-doc/blob/master/manuals/volta/gv100/dev_ram.ref.txt).

## Evidência acrescentada

Com `SNX_FIFO_TRACE_DIR` definido, o runtime mantém o trace circular `SNXFIFO3` de 8.192 entradas e prefixos de até 128 palavras. Compara os bytes no enqueue, antes de solicitar a memória ao renderer e depois de aterrar suas escritas pendentes. A execução continua lendo os comandos originais.

A captura adicional `first-suspect-full.bin` registra a entrada que contém o primeiro cabeçalho incomum, com quatro snapshots:

1. Bytes no enqueue.
2. Bytes antes de aterrar escritas GPU pendentes.
3. Bytes depois desse aterramento.
4. Bytes quando o parser observa o cabeçalho incomum.

O arquivo inclui o estado do parser antes da entrada e no evento, o valor exato do cabeçalho observado e os endereços CPU iniciais. Cada snapshot tem até 16.384 palavras. O armazenamento de snapshots do enqueue tem limite de 4 MiB por job. Páginas ilegíveis são registradas, e sufixos ausentes permanecem explicitamente incompletos. Uma escrita concorrente pode ocorrer durante qualquer cópia, portanto os snapshots não constituem uma visão atômica de toda a entrada.

O inspector `scripts/inspect_gpu_fifo_failure.py` verifica o formato e produz seu JSON ao lado do arquivo privado. Ele compara as transições e decodifica limites de cabeçalhos sem executar métodos ou escrever na memória do jogo. Exemplo, com caminho obtido de um run local:

```powershell
private/tools/python/python.exe scripts/inspect_gpu_fifo_failure.py private/windows/logs/RUN-fifo/first-suspect-full.bin
```

As capturas, relatórios com bytes do fluxo e fixtures de execução ficam em `private/`. O parser não ganhou filtros, retries, tolerâncias novas ou exceções para ACNH.

## Divergência independente do report semaphore

`SET_REPORT_SEMAPHORE_D` usa o bit 4 para escolher a ordenação do release e o bit 28 para escolher uma estrutura de uma ou quatro palavras. O handler tratava qualquer um desses bits como pedido de uma palavra. Foi corrigido para consultar somente o bit 28. A fonte primária é o [header NVIDIA Maxwell B](https://github.com/NVIDIA/open-gpu-doc/blob/master/classes/3d/clb197.h).

O fixture independente `vendor/ScarletNX/tests/report_semaphore.c` liga o handler de produção a memória e clock sintéticos. Verifica as quatro combinações dos dois bits, dois payloads, o tamanho exato da escrita, timestamp e bytes vizinhos. São 10 casos e 605 verificações. A condição antiga falha no tamanho da escrita; a condição corrigida passa.

Essa divergência não foi demonstrada como causa da corrupção FIFO. Nos prefixos examinados dos runs `084323`, `085514` e `091843`, os argumentos de report semaphore observados foram release `0x1000f010`, que já seleciona uma palavra, e report-only `0x0000f002`, com selector `NONE`. A correção preserva esses casos. Esses prefixos também não demonstram uso dos contadores de geometria simulados pelo handler.

## Pendência

É necessário reproduzir a falha com a captura completa habilitada e localizar a primeira transição que modifica os bytes ou o estado do parser. Runs sem cabeçalhos incomuns não bastam para declarar corrigida uma falha intermitente. `SNX_WW` acompanha páginas escritas para a coerência dos caches de buffers, mas o parser FIFO lê diretamente a memória guest. Ativar esse recurso, sem uma transição observada que o justifique, não comprova uma correção.
