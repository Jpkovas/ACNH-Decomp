# Métricas verificadas

Geradas em 2026-10-13T03:43:38.516847+00:00 pelo pipeline local.

| Versão | Funções descobertas | Revisadas integralmente | RTTI | BCSV | EventFlow | MSBT round-trip | PBC |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1.0.0 | 60728 | 2 | 1467 | 164 | 456 | 1967 | 783 |
| 3.0.3 | 95989 | 1 | 1685 | 234 | 875 | 3086 | 1012 |

Cinco módulos compiláveis. Três funções versionadas com diff ARM64; uma com 8/8 bytes iguais. Murmur3 é funcionalmente equivalente no contrato testado em cada versão e tem 19,36% / 22,48% de semelhança de instruções no objdiff.

Comparação da região terminal da query: 3806 casos por versão. O leitor de flags e os serviços do fluxo são dependências injetadas.

RTTI representa identidades de tipos, majoritariamente middleware; não mede classes do jogo com layout recuperado. Schemas de save validam limites declarados, sem validar instâncias de saves.

Não há porcentagem de decompilação do jogo inteiro. Nomes e protótipos da autoanálise permanecem provisórios. Revisão humana independente não registrada.
