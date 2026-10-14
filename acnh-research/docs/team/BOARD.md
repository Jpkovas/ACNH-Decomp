# Frentes e critérios de entrega

Coordenação: Retomar decompilação do ACNH. Todas as frentes preservam a meta integral. Cada uma prepara uma entrega revisável; a coordenação aceita integração, executa o jogo e publica marcos.

| Frente local | Resultado esperado | Limite da tarefa |
| --- | --- | --- |
| Journal e commit | Transações e recuperação entre processos com falhas injetadas | Dados próprios; sem afirmar save ACNH |
| GPU e prévias de ilha | Patch causal, fixtures e replay das quatro prévias | Cópia privada do runtime; sem editar produção |
| Escrita de flags | Grupo conectado com fonte própria e ABI contra ARM64 | Sem modificar os bancos/árvore existentes |
| Schema e lookup | Contratos e rotinas de resolução de keys reconstruídos | Sem alterar parser e tabela já integrados |
| Áudio | Rotinas originais de áudio/DSP reconstruídas e comparadas | Backend de produção preservado |
| Tutorial e save reload | Inputs normais, checkpoints e critérios de restauração | Root lança e controla o jogo |
| Revisão de entregas | Manifestos, hashes, proveniência e matriz de pendências | Sem editar os relatórios dos produtores |
| Memória e startup | Runtime/módulo candidato epoch v2 com gates completos | Janela exclusiva de integração; sem jogo/default/push |

As três tarefas de nuvem foram confirmadas por conversas persistentes e workers `durable`, com prompts idênticos e execução inicial concluída: “Protótipo transacional C11”, “Revisão do protocolo de memória” e “Implementar verificador reprodutibilidade”. Os pacotes de fontes, testes sintéticos e documentação aguardam importação e revisão local. Testes reportados na nuvem não são validação Windows nem cobertura ACNH integrada.

As tarefas locais podem adicionar até três subagentes, se houver trabalho independente e espaço real. Cada subagente precisa de ownership e documentação. Nenhum agente adiciona bytes isolados à cobertura integrada.

Antes de trabalho pesado, confira `private/team/TIMING-LOCK.json`. A lease ativa suspende builds, benchmarks e novos lotes de oracle. Mantenha os registros de entrega exigidos em [DELIVERY-TEMPLATE.md](DELIVERY-TEMPLATE.md).

O mapa de IDs, títulos e ownership é mantido em `private/team/registry.json`. A coordenação acompanha status, lê relatórios, exige reparos, compara hashes e testa as candidatas antes de promoção.

A coordenação ativou acompanhamento periódico nesta thread. A frente “ACNH | Local — integração de memória e startup” recebeu a janela exclusiva para aplicar a candidata epoch v2 e renovar os gates das mesmas 14 entradas; nenhum outro worker pode editar esses arquivos compartilhados durante a janela. Defaults, execução real do jogo e publicação continuam sob controle do coordenador.

A primeira execução controlada da candidata epoch v2 chegou ao diálogo com áudio PCM não zerado e terminou normalmente. A cobertura permanece em 14 entradas / 2.212 bytes; repetição, gameplay e save/reload continuam pendentes. Veja [a observação do coordenador](COORDINATOR-STARTUP-2026-10-13.md). As três entregas originais de nuvem foram importadas com hash exato; revisões locais identificaram diferenças do modelo de memória e falhas no verificador e no protótipo C11. Foram solicitadas correções com fatos agregados e dados próprios.

Depois desse marco histórico, a candidata de 35 entradas passou pelos gates do módulo real, pelo loader e por uma execução Windows de startup com diálogo e áudio, encerrada naturalmente. A coordenação aceitou **35 corpos / 4.696 bytes** como cobertura da candidata integrada; o default de **14 / 2.212** permanece separado e preservado. O grupo seguinte de 18 rotinas, DSP isolado e infraestrutura continuam fora desse numerador. Veja [a aceitação e seus limites](../../metadata/windows/1.0.0/player35-coordinator-acceptance.json).

Há duas janelas de edição com escopos distintos: o integrador prepara um runtime privado com GPU v2 e diagnóstico de input; a revisão de publicação prepara o caminho opcional de build completo e CPU explícita. O registro privado identifica cada owner e os arquivos permitidos. A composição de 53 entradas ainda aguarda uma janela própria e gates do módulo final, incluindo a supressão de todos os wrappers no fallback original completo.

As três revisões de nuvem foram importadas em diretórios novos, conservando os pacotes originais. Cada pacote exige nova revisão local: a licença e os outputs do protótipo C11 foram corrigidos, mas a revisão Windows encontrou um erro de compilação estrita e perda de dados ao selecionar uma geração anterior após falha transitória. A infraestrutura de nuvem acrescenta zero bytes de cobertura e permanece separada do backend integrado.

