# ACNH-Decomp

Pesquisa de decompilação de Animal Crossing: New Horizons e desenvolvimento de um port para Windows. **A decompilação integral e a build jogável completa continuam incompletas.** O primeiro alvo executável é 1.0.0; a pesquisa 3.0.3 foi preservada. A integração Elysium Crossing está excluída.

O marco de 2026-10-13 chegou à ilha em uma sessão Windows de 30 minutos, permitiu caminhar e sacudir uma árvore, derrubando suas frutas. NPCs, inventário, save/reload e o filme VP9 ainda precisam de validação. Capturas do jogo permanecem privadas.

A execução atual usa uma ponte híbrida: recompilação automática ARM64 para C/x64, serviços/GPU por compatibilidade e fallback de interpretação ARM64. A recuperação manual substitui **três entradas completas, uma região parcial e uma entrada guardada**. Esse avanço não representa o código-fonte completo recuperado.

- [Progresso e evidências](acnh-research/docs/progress.md)
- [Objetivo Windows e reprodução local](acnh-research/docs/windows_port.md)
- [Pesquisa, ferramentas e parsers](acnh-research/README.md)
- [Publicação e auditoria](acnh-research/docs/publication.md)

Este repositório contém fontes funcionais escritas no projeto, ferramentas, patches de dependências abertas e relatórios agregados. Dumps, chaves, firmware, assets, diálogos, bancos Ghidra, capturas, executáveis/DLLs e código levantado automaticamente do jogo ficam fora do Git. A reprodução dos testes do jogo depende de inputs locais fornecidos pelo usuário.

O material próprio sem outra licença usa [Apache-2.0](LICENSE). Há exceções GPL/MIT/LGPL descritas em [LICENSE_NOTES.md](acnh-research/LICENSE_NOTES.md), com os textos em [licenses](licenses/). Essas licenças não cobrem o jogo ou seus dados. Não se afirma obtenção do código-fonte original nem processo de clean-room.

Crédito da ponte de pesquisa: **SwitchRecomp by MZ Labs**, através do fork ScarletNX.
