# Formatos e limites observados

| Resultado | 1.0.0 | 3.0.3 |
|---|---:|---:|
| BCSV estruturais | 164 | 234 |
| Células comparadas entre C++ e parser upstream | 1.116.909 | 2.300.008 |
| EventFlow lidos sem erro | 456 | 875 |
| Actions / queries observadas | 542 / 417 | 1.201 / 886 |
| MSBT USen com round-trip estrutural | 1.967 | 3.086 |
| Mensagens indexadas | 68.959 | 120.498 |
| Grids PBC comparados | 783 | 1.012 |
| SMMH/BYML com round-trip | 0 presentes | 80 |

BCSV: o parser próprio e o leitor C++ verificam limites, offsets, versões, rows e field hashes. O oracle CylindricalEarth foi usado com `bcsv.Row`, sem atribuir tipos. Todos os bytes de todos os campos de todas as linhas coincidiram por CRC32. Isso não valida nomes ou significado de campos.

Os 2.048 decoders de `specs_100.py` foram confrontados apenas com 1.0.0. Duas incompatibilidades ficaram registradas: ItemParam.ItemName tem nove valores que não decodificam como UTF-8; NpcLife.SpotType tem 47 falhas do decoder histórico. Há 28.212 células de enum com CRC não conhecido entre 429.505 examinadas. Não foram forçadas conversões nem usados nomes fictícios. Em 3.0.3 os campos permanecem bytes desconhecidos até verificação específica.

EventFlow: todos os arquivos presentes no diretório EventFlow foram catalogados com atores, nós, edges, chamadas, branches e variáveis. `evfl` genérico falhou em 29 fluxos da base por diferenças de vardefs; o parser ACNH específico conseguiu ler o conjunto inteiro. Os CSVs versionados descrevem assinaturas observadas; há 10 conflitos na base e 26 no alvo. Cases usados não provam o domínio completo de retorno das queries. Somente o fluxo-piloto passou por recompilação.

MSBT: foi selecionado o conjunto USen para cobertura linguística explícita. Parse → pack → parse conserva textos e atributos no conjunto catalogado. As referências MessageID exatas dos grafos resolvem 8.030 usos na base e 15.438 no alvo; 63 e 78 ficam sem resolução, respectivamente. Valores vazios e duas referências dinâmicas do alvo estão separados. Algumas diferenças de capitalização e seleção de mensagens podem explicar pendências, sem promover essa hipótese a resolução comprovada. Os textos continuam privados.

PBC: signature, dimensões, offsets e limites das células de 52 bytes foram verificados. Os quatro bytes finais de cada célula formam as quatro posições do grid de colisão e coincidiram com `pbc.PBC`. Os 12 words anteriores permanecem não interpretados; altura não foi reconstruída. Interpretação completa do terreno não é um resultado do piloto.

SaveIO: os 80 schemas SMMH presentes em 3.0.3 contêm 6.688 ocorrências de layouts e 23.644 de campos, incluindo versões históricas declaradas nos próprios nomes. Conferidos limites, alignments, nested sizes e 11.543 referências aninhadas; zero overlaps; 2.712 gaps de padding. Todos fizeram round-trip BYML. Hashes de tipos/campos permanecem identificadores numéricos. Estes são layouts declarados em schemas, não classes do executável nem saves reais decodificados. A base não contém System/Smmh. Nenhum save real foi editado.

RTTI: 1.467 / 1.685 identidades Itanium e 1.372 / 1.641 relações de herança; majoritariamente nn::nex e runtime. Vtables candidatas usam relocations e ponteiros de métodos. São diferentes do sistema customizado de type_info dos receptores EventFlow. Nenhum layout completo de objeto foi validado a partir dessas identidades.

Relocations: comparação ao Ghidra em reimportações limpas confirmou 298.521 relativas na base e 373.225 no alvo, com zero diferenças. O loader não nomeia o GOT do alvo separadamente; a região é preservada como `.data.1`. Não foi aplicada uma fronteira conjectural. Warnings de autoanálise e funções falsas/omitidas permanecem nos logs privados e exigem revisão localizada.
