# Publicação de marcos

O usuário autorizou publicar o progresso em [Jpkovas/ACNH-Decomp](https://github.com/Jpkovas/ACNH-Decomp). O primeiro marco documenta a chegada à ilha, movimentação e interação com uma árvore observadas em uma execução Windows da versão 1.0.0. A decompilação integral permanece incompleta, assim como a validação de NPCs, inventário e save/reload.

A arquitetura executável atual é híbrida: tradução automática ARM64 para C/x64, serviços Horizon e GPU por compatibilidade, fallback de interpretação ARM64 e poucas rotinas reconstruídas manualmente. Chegar à ilha por essa ponte não demonstra recuperação do código-fonte completo. O modo denominado `native` pelo harness identifica a DLL x64 e precisa ser interpretado com esse limite.

O conteúdo público inclui fontes funcionais escritas no projeto, parsers e ferramentas de pesquisa, patches de dependências abertas, instruções e relatórios agregados. Não inclui dumps, chaves, firmware, RomFS, bancos Ghidra, assets, diálogos extraídos, capturas, áudio do jogo, executáveis/DLLs nem as unidades C levantadas automaticamente do ARM64. Os testes contra o jogo requerem inputs locais e geram resultados privados.

Antes de cada publicação, executar `scripts/audit_research.py` e `scripts/audit_public_history.py`. A primeira verifica a superfície pretendida e padrões de chaves; a segunda verifica todos os objetos Git locais, inclusive blobs sem referência. Ambas complementam a revisão de fonte e licenças, sem constituir garantia jurídica ou prova de clean-room.

O material próprio sem outra licença usa Apache-2.0. Patches e fixtures derivados do ScarletNX têm exceções GPL-3.0-or-later; componentes abertos associados mantêm seus avisos Apache/MIT/LGPL. Consultar [LICENSE_NOTES.md](../LICENSE_NOTES.md) e [licenses](../../licenses/). Crédito da ponte: **SwitchRecomp by MZ Labs**.

A publicação conserva o commit inicial do repositório GitHub e o histórico local do projeto. Marcos seguintes devem acrescentar evidências e atualizar os limites, sem incluir resultados proprietários ou declarar decompilação concluída por avanço da ponte de execução.
