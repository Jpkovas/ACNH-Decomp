# Revisão local independente do addendum de memória REV2

O addendum corrige as duas divergências centrais da primeira revisão sintética:
os readers usam exclusividade e o caminho sem API consulta sem lease. Aceito o
pacote exato como modelo e revisão de contratos, com as limitações abaixo. Esta
reprodução não aprova nem altera a implementação Windows, não executa o jogo e
acrescenta **zero entradas e zero bytes** à cobertura reconstruída.

## Importação e reprodução vinculadas

O ZIP autorizado tem 38.504 bytes e SHA256
`66b84bbaf1af027d32c6c762749684b04935757e0043fc7b654ee30e5df55a44`.
Seus 17 membros foram lidos, comparados byte a byte com a extração e verificados
contra os dois manifests SHA256SUMS. Os paths não têm escapes, links ou entradas
duplicadas. O ZIP original preservado mantém SHA256
`e6c8e59ba4786330a1041a136cdc3314f866208a8ba2a8057eefb406269568ee`,
e os oito arquivos históricos permanecem idênticos à importação original.

Os quatro entrypoints model.py/test_model.py dos dois conjuntos foram lidos
integralmente antes da execução. Usam dataclasses, unittest e dados sintéticos.
Não contêm Win32, rede, subprocess ou acesso a dados guest. A licença MIT de
lease_review/LICENSE aplica às fontes próprias do addendum conforme seu README.
Os artefatos originais foram preservados, sem substituir seus logs ou reports.

Hashes dos entrypoints REV2:

| Entrada | SHA256 |
| --- | --- |
| exclusive_review/model.py | `cfc777d54b9cae2edf5bb8c0d8742aacaeeebfacabc51ccbfd6245639379a18e` |
| exclusive_review/test_model.py | `10da37ff2aec6fe0d5be5d3db63dd5ec7f24f4b9ed5c8d2ab93e02f7fba64630` |
| lease_review/model.py histórico | `7110dd3e6e2b68c41ad96721edd4f2014d3315a3eac01de21194d0f804a748fe` |
| lease_review/test_model.py histórico | `ca752fe82f00b9e357b1ee76550c9e5f28972bd13e7ade6e7ab2f77eae6788d8` |

O runner próprio checou TIMING-LOCK.json explicitamente inativo antes, na
admissão e após cada processo. A lease observada foi
`2791338b-2097-46c4-8a76-7d2f9f875d7a`, já encerrada pelo coordenador. O runner
nunca adquiriu, liberou ou modificou essa lease. Cada conjunto usa processo Python
separado, evitando colisão dos módulos homônimos model/test_model. Bytecode e
site initialization ficam desativados com `-I -S -B`.

```powershell
& private/tools/python/python.exe -I -S -B private/team/cloud-memory-review/revision2/cloud_memory_r2_reproduce.py
```

Os comandos internos registrados são:

```text
python.exe -I -S -B -m unittest discover -s <extração>/exclusive_review -p test_model.py -v
python.exe -I -S -B -m unittest discover -s <extração>/lease_review -p test_model.py -v
python.exe -I -S -B <revisão>/cloud_memory_r2_probes.py
```

A reprodução final usou Python 3.12.10, Windows/AMD64, interpretador SHA256
`4d6f5f81a4bca11191c4c7c6b43632694d0a4ce74e068619d8fdc161d469859a`.
Todos os processos retornaram 0. Passaram 13 métodos do addendum e, separadamente,
16 métodos históricos. Os probes próprios também passaram. O relatório privado
`private/team/cloud-memory-review/revision2/local-reproduction.json`, SHA256
`8bf468f8a4a294c105b74d8cd9c92b771d7bb0d2e837539585d21993a8d8ac94`,
vincula argv absoluto, cwd, início/fim, duração, stdout/stderr, interpretador,
runner e hashes dos inputs antes/depois. Todos os inputs ficaram estáveis.

Runner SHA256:
`0b50681ed2eedfc57fc47ef86f9ab3d2fc8350d6556b42b12f1801fd35f1366f`.
Probes SHA256:
`d1837c6ebe7c1eaad996fa6c3284d82bb5d77d1d7c34145859447930ad5a7fb5`.
A primeira execução também passou. Apenas o label de timestamp do runner próprio
foi corrigido, e a reprodução foi repetida. O runner/report/logs dessa primeira
execução permanecem em history/first-run-timestamp-label. Não foi falha dos
testes importados e nenhum histórico foi descartado.

## Contagem correta das ordens

As 140 ordens preservam begin/read/end por reader em sete eventos abstratos.
Esse conjunto fica dentro de um dos métodos de cada suíte, não acrescenta 140
testes nativos e não enumera interleavings de instruções C ou Windows.

| Modelo | Resultado das140ordens |
| --- | --- |
| Addendum exclusivo | **6 completas e 134 prefixos bloqueados**, sem retry |
| Histórico compartilhado | 42 admissões imediatas do writer e 98 retries após readers terminarem |

Os probes próprios enumeraram novamente o addendum: 102 prefixos bloqueiam uma
admissão de reader e 32 bloqueiam o writer. Nas seis ordens completas, os dois
intervalos begin/read/end e o writer se comportam como três blocos indivisíveis.
Nos 134 prefixos, a fixture interrompe a simulação no primeiro Blocked e descarta
aquele estado. Não retoma o dono nem executa o restante da ordem. Isso não prova
deadlock: um lock real pode esperar enquanto o scheduler executa o dono. Também
não permite afirmar que o addendum completou 140 execuções concorrentes.

## Contratos exercitados e diferenças atuais

O modelo exclusivo demonstra recusa de reader/writer concorrente, nested begin
antes de recursão, liberação antes de callback, novo token na reentrada, miss do
sufixo após A->B->A, instalação serial única e epoch zero persistente. Os probes
confirmam essas transições e os contraexemplos, sempre como máquina de estados
Python.

| Tema | Resultado sintético | Correspondência e limite do fonte atual |
| --- | --- | --- |
| Exclusividade | Um holder bloqueia outro reader e writer | PMutex usa AcquireSRWLockExclusive. O modelo não executa essa primitive. |
| Writer bloqueado | Blocked antes de marcar gpu/owner | O writer real toma vk_lock e o retém enquanto espera g_memlock. O modelo não reproduz esse wait graph. |
| Callback e nested contexto | End do pai, novo begin/end interno, mutação, begin do sufixo | SaveIO e contexto de jogador liberam antes de resolução/interpreter e readquirem depois. Reentrada suportada exige essa fronteira. Chamar diretamente um contexto enquanto o pai retém lease é fora do contrato e não foi testado aqui. |
| Nested begin recusado | Exceção Terminal de admissão, sem gravar terminal persistente | Runtime begin retorna 0 antes do SRW recursivo. O teste pode encerrar o holder externo. Não equivale a recuperação de erro de ownership. |
| API ausente | compat_query uncached, sem lock/lease/TLS positivo | Acquire sem api.begin mantém o baseline unleased. Este teste expõe o risco query->decommit->uso e não o elimina. |
| API presente, não instalada | Begin e compat_query recusados | Não representa literalmente qualquer módulo ainda não configurado: o módulo opcional tem tabela zero e baseline uncached até negociação. Setter encontrado e recusado faz o loader abortar. |
| Epoch zero | Fresh query ainda sob lease | O runtime também desliga apenas reutilização. Ausência de API sem lease continua um estado diferente. |
| Identity | Binding completo inclui base/span/domain/instance/runtime/functions/user | Cache atual compara base/span/epoch/domain/begin/end/user. Instalação valida ABI 2/tamanho 40. Não há instance/generation explícito no runtime. |
| Foreign ownership | Apenas o chamador entra em terminal; dono inocente continua no modelo | API.end raw rejeita ownership sem liberar o dono. Provider com scope held incorreto termina o processo inteiro. A continuação inocente do modelo não é comportamento nativo após TerminateProcess. |
| End failure/cópia no dono | Terminal persistente e lock retido; boundary recusada | Provider termina com primitiva host e não retorna à dispatch. O modelo só cobre falha com lock retido, não resultado de unlock incerto. |

A distinção de identity é uma comparação de chave pura, não uma execução de
unload/reinstall nem prova de lifetime. O singleton atual pressupõe runtime,
domain, callbacks, lock e epoch com vida de processo. Troca de mapping no mesmo
base exige epoch novo, mas reciclagem de runtime/IDs/endereços após unload exige
outro contrato e drain de leases/TLS. O modelo não possui unload.

O addendum instala uma vez em uma transição serial. Não testa instalação
concorrente, publicação de memória ou proteção atômica do setter. O loader atual
executa antes das guest threads e configura **dois contextos independentes**,
SaveIO e jogador, com a mesma tabela/domain de runtime. Os setters normais
recusam segunda configuração em cada contexto. Isso não é uma única chamada de
setter global por processo como no modelo.

Há uma diferença adicional no fonte atual de 35 entradas:
`acnh_bridge_player_connected_validation_set_policy_hooks(NULL)` pode limpar
hooks e API para alternar modos de fixture. Seu contrato exige validação sem
threads, antes/depois das guest calls. O modelo não tem esse reset. Portanto,
"consumed nunca pode voltar" é premissa do modelo, não propriedade absoluta de
todos os exports do módulo atual. Este addendum não comprova isolamento dos
helpers, não permite reset ao vivo e não recomenda alterá-los como parte desta
revisão. O setter genérico SaveIO continua sem reset nesse fonte.

## Fonte atual de 35 entradas e histórico delimitados

Foram apenas lidos/hasheados 24 inputs locais de comparação, sem compilar ou executar
qualquer DLL. Dos 16 paths vinculados ao review histórico, 15 mantêm o hash; main.c
mudou de
`70115814f028f94a538df6019132c4517cc2e0da4c796398a43909e43fb4f530`
para
`bd4b24e7e19f0377b72aacc598c9130bcffa2f02cf681b94003fe7353d0955f7`,
incluindo a negociação independente da API de jogador. O mem.c atual conserva
o hash histórico `d5b5e4a736a159a958b3c212fe30ec190b4bbd8fcc44212e26432235b2e68710`.

Oito inputs adicionais amarram o contexto de jogador, seu header, fixture de
memória, validadores atuais e registros de integração 35. Esses inputs não
estavam no vínculo histórico; não são declarados retroativamente validados por
ele. A lista exata e todos os hashes antes/depois estão em local-reproduction.json.
Esta revisão não reexecutou os gates 35, os testes Win32/SRW ou a fixture histórica
da DLL 12ee06. Os resultados nativos anteriores pertencem aos seus respectivos
reports e fontes, não ao ZIP cloud ou às suítes 13/16 deste trabalho.

## Contraexemplos e lacunas preservados

O caminho sem API retorna um descritor atomizado por simplicidade. Writer pode
executar A->B->A ou decommit antes de uso; compat_dereference retorna falso por
mapping_version. Essa oracle detecta o perigo sintético e não fixa um mapping
nativo. Fresh VirtualQuery sozinho não elimina TOCTOU.

Epoch de 2 bits força max->zero; tentativa com erro e rollback têm increments
separados, e zero persiste. Isso testa o contrato do modelo, sem provar 64 bits C,
todos os hooks reais, parcialidade do OS ou barriers. Bloqueio antes de admissão
do writer não representa tentativa host nem incrementa epoch.

O cache modelado tem uma faixa homogênea readable. Faltam segmentos heterogêneos,
committed/guard/NOACCESS/RW reais, sucesso parcial de query, bounds de ponteiro
nativo, data races guest, executable targets, fairness e progresso do scheduler.
Thread ID/serial/endereço reciclados, fibers migradas, forced termination,
SEH/longjmp e unlock ambíguo também não são modelados. Cleanup cooperativo com
finally é um traço Python, não prova de unwind C/C++.

Nenhuma mudança em epoch, GPU, CMake, generator, defaults, Git index ou publicação
foi feita. O aceite é restrito ao addendum exato e à reprodução sintética. A meta
de reconstrução completa, gameplay/tutorial e save/reload real permanece fora
desta entrega.
