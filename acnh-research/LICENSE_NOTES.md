# Licenças e proveniência

Os arquivos Nintendo fornecidos pelo usuário são entradas locais de pesquisa e não recebem licença de redistribuição deste projeto. Chaves, tickets, firmware, dumps, bancos Ghidra, strings extraídas e fluxos do jogo devem permanecer ignorados.

O repositório público usa Apache-2.0 para o material próprio sem uma licença específica diferente, conforme a `LICENSE` da raiz. Essa licença não cobre arquivos Nintendo nem os inputs e resultados proprietários da pesquisa. As reconstruções funcionais foram escritas no projeto após análise e testes; não se afirma obtenção do código-fonte original ou um processo de clean-room.

Há exceções explícitas: `patches/scarletnx-data-root.patch`, `windows_audio/native_backend.c/.h` e a fixture em `windows_video/` contêm código GPL-3.0-or-later, identificado nos arquivos e derivado do runtime ScarletNX. O código original SwitchRecomp mantém Apache-2.0, copyright e NOTICE. O backend DSP referenciado do Ryujinx usa MIT. O FFmpeg compilado localmente neste perfil usa LGPL-2.1-or-later, sem habilitar componentes GPL ou nonfree. Os textos e avisos públicos ficam em `../licenses/`; os checkouts completos continuam privados, com seus commits e licenças fixados nos locks de `config/`.

Crédito: **SwitchRecomp by MZ Labs**. A licença de uma ferramenta ou dependência aberta não licencia dados proprietários processados por ela. Nenhuma DLL, executável, captura, fluxo extraído ou código ARM64 levantado automaticamente será publicado neste repositório.

A origem dos dumps ainda não foi documentada pelo usuário. Registrar `user_supplied_origin_unverified`, sem presumir comprovação jurídica. O usuário forneceu chaves e autorizou a preparação local dos arquivos em 2026-10-12. Não publicar esses materiais nem chaves. Em 2026-10-13, autorizou publicar marcos de progresso no repositório Jpkovas/ACNH-Decomp, com documentação e ausência de código/assets proprietários extraídos. A auditoria de publicação cobre o histórico Git além da árvore atual; ela não constitui uma conclusão jurídica sobre engenharia reversa.
