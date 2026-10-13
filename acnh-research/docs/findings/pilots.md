# Contratos reconstruídos

## Retorno zero — 1.0.0

Entrada 0x710000AC10, tamanho 8. O apontador na relocation 0x710301CA30 fornece a âncora. Duas instruções foram revistas e recompiladas com Clang 23.1.3 para AArch64: os oito bytes coincidem. Os 131 casos de emulação conferem o retorno zero e os registradores preservados.

A implementação escolhe a interface `unsigned(const void*) noexcept`. A declaração original, a signedness, a classe e a associação ao EventFlow continuam desconhecidas. Uma alternativa compatível com a evidência é um método de outra hierarquia ou um retorno constante com parâmetros diferentes. O matching não distingue essas hipóteses e não identifica o compilador original.

Evidência: `metadata/1.0.0/matching-pilot.json`; objetos e objdiff em `private/outputs/1.0.0/matching/`.

## Murmur3 de string C — 1.0.0

Entrada 0x7100001BF0, tamanho 300. Constantes, rotações, tratamento de cauda e avalanche foram confrontados com o assembly e com a fonte primária MurmurHash3 x86_32. A função recebe string NUL-terminated em x0, seed em w1 e retorna 32 bits em w0. Lê até NUL, inclusive bytes com bit alto; zeros internos encerram a entrada.

O contrato exige memória legível até o terminador e comprimento abaixo de 2^32. Ponteiro nulo falha tanto no original quanto no código ARM64 recompilado. A validação cobre 322 casos sintéticos, três alinhamentos, 959 identificadores do conjunto EventFlow, registradores callee-saved e stack. A comparação inclui original ARM64, ARM64 reconstruído, DLL nativa e oracle mmh3.

O código reconstruído tem 248 bytes e 19,36% de semelhança de instruções no objdiff: L2 validado no contrato, L3 medido com divergência. Não é matching. A sequência original de 300 bytes não foi encontrada no alvo 3.0.3; o endereço não foi transferido.

A busca independente de constantes no alvo encontrou uma rotina completa em 0x71005BD550–0x71005BD650, com 260 bytes. Assembly e todos os caminhos até ret foram examinados. Os mesmos 322 casos em três alinhamentos, as falhas de ponteiro nulo e 2.087 identificadores do alvo passaram contra original ARM64, reconstrução ARM64, DLL e mmh3. Seu objdiff é 22,48%, também divergente. O contrato funcional completo desta rotina foi associado entre versões; os nomes C++ originais continuam desconhecidos. A rotina do próprio alvo foi usada para verificar os hashes de seus binding names.

A inicialização perto de 0x71004645E0 chama o hash e escreve um descritor que contém o label EventFlowQueryDummy. A proximidade é uma âncora de pesquisa; não prova por si qual string foi passada à chamada nem um layout completo de objeto. Nenhum nome original foi recuperado para a função de hash.

Evidência: `metadata/1.0.0/identifier-hash-validation.json`.

## Predicado de flags inteiras — 1.0.0

O construtor 0x7100406280 registra AccessKey, Border e FlagCheckType, inicializa Border e FlagCheckType com zero e atribui a vtable 0x7103056660. A relocation independente confirma seu slot 0x30 apontando para 0x7100406390. A hipótese inicial de outro receptor com parâmetros iguais foi confrontada com a tabela de factories: o hash original de EventFlowQueryEventFlagInt é 0x1BB353CB, armazenado em 0x710305BFB0, seguido da relocation para a factory 0x7100456BB0. Essa factory aloca 0x138 bytes com alinhamento 8 e chama diretamente o construtor 0x7100406280. BindInfo liga os aliases NpcInt/SystemInt ao mesmo nome. Esta cadeia sustenta a identidade lógica da query com alta confiança; o nome da classe C++ original continua desconhecido.

A tabela contígua ordenada da base possui 463 pares candidatos, dos quais 391 têm correspondência com nomes/aliases do conjunto da mesma versão. Os 444 nomes candidatos foram confrontados com o hash ARM64 original, sem colisões entre os nomes testados. O alvo possui 959 pares candidatos, com 846 bindings associados usando sua própria rotina de hash. A fronteira por continuidade/ordenação ainda não é prova do count usado pelo consumidor. Somente a cadeia deste piloto recebeu revisão individual até o handler; as outras correspondências permanecem anotadas como evidência de hash/factory.

A região terminal 0x710040685C–0x71004069EC foi examinada em assembly e executada em Unicorn com a tabela original de branches, sem substituir instruções. Border em self+0x100 e FlagCheckType em self+0x128 foram conferidos também pelos stores do construtor. O nome original e a estrutura completa não foram afirmados.

| FlagCheckType | Resultado verdadeiro |
|---:|---|
| 0 | valor diferente de Border, interpretado como bits de 32 bits |
| 1 | valor igual a Border |
| 2 | valor ≤ Border, sem sinal |
| 3 | valor < Border, sem sinal |
| 4 | valor ≥ Border, sem sinal |
| 5 | valor > Border, sem sinal |
| 6 | população de bits do valor < Border com sinal |
| Outros | falso |

Todos os 3.806 casos passaram contra ARM64 original, DLL nativa e oracle independente. Incluem igualdade, zero, bit 31, máximo unsigned, extremos signed e modos inválidos. Não houve escrita no objeto pelo predicado. O fetch acontece antes do dispatch no wrapper, inclusive para modo inválido.

O backend completo faz parsing do namespace da AccessKey e despacha diversos serviços de SaveIO; ele não foi reconstruído. A interface C++ injeta um leitor de valores, explicitamente. A evidência valida o predicado e o wrapper com dependência substituída, não efeitos de saves ou gameplay completo. O corpo inicial do Ghidra da base omitia blocos de switch indireto; por isso o assembly e a emulação delimitam a prova.

No alvo 3.0.3, a busca independente do par hash/relocation encontrou 0x710487FE70 → factory 0x7101049734. O construtor foi incorporado à factory: os labels AccessKey/Border/FlagCheckType, defaults e a atribuição da vtable 0x71048718F0 estão no próprio corpo. O handler no slot 0x30 é 0x7100F183D0; a região terminal 0x7100F188D4–0x7100F18A6C passou nos mesmos 3.806 casos contra seu ARM64 original. Os offsets 0x100 e 0x128 foram conferidos independentemente, não copiados por suposição. O backend do alvo tem dispatch distinto; somente o contrato terminal foi associado entre versões. Este é o exemplo revisado de inlining/mapeamento parcial do plano.

Evidência: `metadata/1.0.0/flag-int-validation.json`, `factory-bindings-summary.json`, `reviewed-annotations.json`; decompilação privada em `private/outputs/1.0.0/query-anchors/`.

## Fluxo do aeroporto

AI_NPC_Doc_Airport foi decodificado e recompilado independentemente nas duas versões: 3 nós alcançáveis em 1.0.0, 11 em 3.0.3. Bytes diferem, mas o grafo enraizado, parâmetros, condições, variáveis e entrypoints do piloto coincidem após a leitura do resultado.

O módulo C++ implementa apenas a versão 1.0.0: uma query com AccessKey `cLandTemp:DocReturnFromIsland`; retorno 0 chama a mudança para cDocReturn, retorno 1 chama cWait, com IsSameState=false e IsResumePreviousState=true. Outros retornos não produzem action. Tests verificam 0, 1, -1 e 2. Query e mudança de estado são dependências injetadas; o grafo não prova as implementações originais dessas operações.

## Decisão de matching extensivo

As fontes de bibliotecas e convenções ABI são indícios de família de toolchain, não sua versão/flags. A busca por markers explícitos de versão Clang/GCC/LLVM nos segmentos não encontrou nenhum. O campo SDK dos NCA é provenance do SDK, não identificação do compilador. O bom resultado de oito bytes e a divergência da rotina de hash não justificam matching extensivo. Este plano entrega o estudo piloto e mantém os demais módulos em L1/L2.
