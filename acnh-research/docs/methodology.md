# Metodologia

1. Ler este arquivo e `config/versions.yaml` antes de cada experimento.
2. Identificar versão, módulo, SHA-256, BuildId, ferramentas e comandos usados.
3. Trabalhar sobre inputs locais; manter originais intactos. Chaves nunca são exibidas nos logs.
4. Verificar assinatura e limites de cada formato antes de interpretá-lo. Falhas são resultados, não evidência de sucesso.
5. Guardar output proprietário em `private/outputs/<version_id>/`; metadados não proprietários podem ser versionados.
6. Nomes inferidos/provisórios exigem evidência e hipótese alternativa. Endereços sempre são versionados e usam base explícita.
7. Não executar scripts legados com endereços v1.1.4 em outra versão. Revisar API, pressupostos e efeitos antes da execução.
8. Separar L1 (análise), L2 (equivalência funcional delimitada) e L3 (diff de máquina). Teste sintético não conclui marco dependente de dados reais.
9. Validar casos normal, erro e limite; registrar comandos, contagens e divergências.
10. Atualizar `docs/progress.md` e métricas apenas a partir de artefatos existentes. Não alterar Elysium automaticamente.
