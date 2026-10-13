# Diferenças verificadas entre versões

Referência: 1.0.0. Alvo: 3.0.3.

As identidades de tipos RTTI são associadas pelo nome codificado e espécie de type_info. Isso não transfere layouts nem equivalência comportamental.
Correspondências de funções são candidatos para revisão; não há transferência automática de nomes. O filtro usa mnemônicos/CFG e o score adiciona constantes, strings diretas e fingerprints de callers/callees. Relocations, indireções e mudanças de inlining podem alterar esses indícios.

| Formato | Novos | Removidos | Hash alterado | Hash igual |
|---|---:|---:|---:|---:|
| bcsv | 74 | 4 | 153 | 7 |
| eventflow | 421 | 2 | 376 | 78 |

O fluxo-piloto AI_NPC_Doc_Airport tem 3 nós alcançáveis em 1.0.0 e 11 em 3.0.3. Ambos passaram no round-trip estrutural. A implementação C++ do fluxo cobre somente o contrato 1.0.0.

Candidatos de funções: 9100. Três vínculos receberam revisão técnica individual; dois têm escopo parcial. Identidades RTTI associadas: 1451.

EventFlagInt: a factory do alvo incorpora o construtor separado da base. A região terminal passou em 3.806 casos por versão. A equivalência do backend completo permanece incerta. As duas anotações do alvo foram aplicadas após conferir seus endereços/labels/relocations independentemente.

Murmur3 C-string: função completa associada pelo contrato de entrada/saída após conferir assembly e repetir o diferencial nos dois originais. Código gerado e original diferem. A descoberta no alvo foi independente; o endereço de referência não foi reutilizado.

Evidência versionada: [manual-version-review.json](../metadata/manual-version-review.json). Nenhum nome foi migrado automaticamente.
