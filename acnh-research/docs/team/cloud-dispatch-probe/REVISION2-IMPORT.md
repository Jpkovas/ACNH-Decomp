# Importação das revisões 2 de nuvem

As três revisões de infraestrutura própria foram importadas em novos caminhos
privados `private/team/cloud-imports/<task_id>/revision2/`, sem sobrescrever as
entregas anteriores. Inventário, privacidade declarada, licença e proveniência
foram conferidos antes da solicitação de bytes. A importação validou caminhos,
formatos, links/reparse, tamanhos, CRCs e SHA256 antes de extrair.

| Frente | Pacote | Bytes | Membros | Licença | SHA256 confirmado |
| --- | --- | ---: | ---: | --- | --- |
| C11 transacional | host_save_tx_c11_review_r2.zip | 103363 | 28 | Apache-2.0 | `eb9e0b04bac14d74be9ea430d59246f3d70bbf81a214beb28283f2b746b40725` |
| Modelo exclusivo de memória | acnh_memory_exclusive_addendum.zip | 38504 | 17 | MIT | `66b84bbaf1af027d32c6c762749684b04935757e0043fc7b654ee30e5df55a44` |
| Verificador de reprodução | acnh-repro-verifier-r2.zip | 50661 | 28 | MIT | `b66506c3e22f6c19b2fd0c033acc29eb8297f934a244e0eacab706fc2b71d2cd` |

Total: **192.528 bytes e 73 membros**. Os hashes foram calculados pelo helper e
confirmados por Get-FileHash. Os ZIPs continuam ignorados pelo Git. Todos os
manifests SHA256SUMS atuais e históricos incluídos foram conferidos (cinco
manifests, 88 registros). Inventários extraídos coincidem com o preflight.

Histórico: ZIP/report/checksum C11 v1 permanecem byte-idênticos; memória conserva
o ZIP v1 e seus oito arquivos; reprodução preserva os doze arquivos anteriores
em previous/. Os três ZIPs v1 locais mantêm seus hashes originais.

As raízes de revisão são:

- `cloud_save_transactions/revision2/extracted/host-save-tx-r2/`.
- `cloud_memory_review/revision2/extracted/exclusive_review/`.
- `cloud_repro_verifier/revision2/extracted/acnh-repro-verifier-r2/`.

Esses caminhos são relativos a `private/team/cloud-imports/`. Cada frente possui
preflight-inventory.json, preflight-receipt.json, receipts de exportação,
chunks.json bruto, download.json, import.json com hashes individuais,
inventory-audit.json, entrypoint-inspection.json e receipt.json. IDs de origem,
links de recurso e mensagens/outputs de cada chunk permanecem nos receipts
privados. Nenhum código importado foi executado; nenhum patch foi aplicado.

## Conteúdo e limites para os revisores

C11 r2 fornece licença Apache-2.0 explícita e proveniência das próprias fontes,
inclusive histórico. A leitura observou buffers publicados somente após read e
close, outputs limpos antes de validar argumentos e distinção de autoridade
ausente versus erro de leitura/alocação. Novos fixtures usam somente OWN!/LIFE.
Baseline negativo deliberadamente espera ASan double-free na fonte própria v1.
O relatório cloud declara 1.892 casos repetidos com ASan/UBSan; isso não conta
saves recuperados nem foi reproduzido por este importador. LeakSanitizer não
concluiu no cloud; Windows/NTFS/exFAT e perda de energia permanecem pendentes.

O adendo de memória usa exclusividade, instalação única e ownership terminal.
Sem API, query uncached fica explicitamente sem lease/pin. É um modelo, não
implementação ou certificação da runtime. As 140 ordens exclusivas classificam
seis completas e 134 prefixos bloqueados, e não 140 execuções concluídas.
O cloud declara 13 testes novos; os 16/140 da primeira revisão são histórico
do modelo compartilhado. Nenhum Win32/SRW/PMutex real foi executado ali.

Reprodução r2 restringe seleção de CPU, rejeita relatos real_call contraditórios
para entradas completas integradas e verifica ancestrais/reparse por lstat.
O cloud declara 76 métodos passando e um Windows-only pulado. O teste real de
junction existe para reprodução local; atributos Windows no cloud são modelos.
compare_revisions usa o verificador próprio anterior e fixtures temporários;
isso não comprova chamadas de DLL ou determinismo da build. O patch histórico
não deve ser aplicado à árvore local atual por pressuposição.

## Processo, proveniência e próximo portão

Pré-verificação e exportação ocorreram nas conversas/workers confirmados
existentes. Os chunks vieram de outputs de terminal separados de até 12.000
caracteres Base64, recuperados por read_thread durable. Somente o ZIP próprio
existente foi lido para transferência; nenhum arquivo/ambiente/histórico
privado local, dump, chave, firmware, asset ou captura foi enviado.
Não houve downloader alternativo, publicação, push ou PR.

Duas chamadas retornaram limite temporário Too many requests. Receipts preservam
esses resultados; depois de confirmar que os pedidos não entraram e espaçar as
chamadas, as solicitações foram aceitas. Não houve rejeição de risco na revisão 2
nem contorno de aprovação. Artefatos e documentos originais ficaram intactos;
registry compartilhado não foi editado.

HEAD local observado ao entregar:
`72da3e52ed78b344bff74c991a418df4c649f53d`. A origem de cada fonte entregue é ligada ao hash de seu ZIP,
não a uma alegação de reconstrução ACNH ou correspondência com a árvore local.

As três entregas estão prontas para revisão e reprodução Windows independentes.
Fontes e resultados corrigidos devem usar diretórios separados de revisor,
preservando ZIPs e hashes. Critérios de pin/ownership, serviço filesystem e
manifest/argv efetivo precisam de evidência da implementação real antes de
integração. **Cobertura acrescentada: 0 entradas / 0 bytes.** Não há validação
de gameplay, input/áudio/save/reload ou build Windows jogável por esta importação.
