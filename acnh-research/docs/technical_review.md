# Revisão técnica local

Revisão executada pelo Codex sobre scripts, módulos, fronteiras de formato e evidências dos pilotos. Não é revisão humana independente, nem revisão de uma PR publicada. Não há remote Git configurado para abrir PR; o resultado permanece local e revisável. As saídas proprietárias ficam ignoradas.

## Correções verificadas

| Problema encontrado | Correção | Verificação |
|---|---|---|
| Reusar extração PFS existente por tamanho permitia corrupção de mesmo comprimento | Hash do arquivo confrontado com a região correspondente do container | Teste sintético altera payload sem alterar tamanho e exige rejeição |
| Nomes PFS podiam colidir por case ou usar nomes de dispositivo Windows | Rejeição de caminhos, caracteres inseguros, case duplicates, reserved names e trailing dot/space | Parser, teste de traversal e extração do conjunto real |
| Exportação Ghidra podia falhar com exit code zero | Wrapper verifica erros de script/cache/import no log e exige artefatos | Falha de âncora observada; importador revisado executou e produziu relatório |
| Índice vazio/incompleto podia parecer sucesso | Normalização exige inventário, contagem consistente, versão e ausência de timeout | Índice real e gate do pipeline |
| Extração NSO gravava segmentos antes da validação final de overlap | Escrita após todas as validações, via arquivo temporário | Hash/bounds tests e seis hashes reais |
| Query parecia usar comparação signed em todos os modos | Assembly confirmou unsigned em 0–5 e signed apenas no limite de popcount | 3.806 casos ARM64/oracle/DLL |
| Assinaturas inferidas globalmente pareciam prova | Perfil baseline desliga Parameter ID; símbolos revisados têm evidência explícita e limites de assinatura | Perfil exportado e quatro anotações aplicadas sem overrides de assinatura |
| CMake probe MSVC Debug falhou no PDB desta instalação/sandbox | Probe compilado em Release, consistente com o build | Configure, build e CTest MSVC aprovados; Clang aprovado |
| Scripts de pipeline usavam argumentos incompletos | Inputs RomFS e fluxo-piloto passados explicitamente | Inspeção das interfaces CLI e execução consolidada registrada |

O leitor BCSV usa storage emprestado imutável com lifetime documentado, aritmética de tamanho verificada em 64 bits, lookup de field hash e rejeição de truncamentos. O hash usa aritmética unsigned de 32 bits; shifts internos são constantes válidas e a precondição de terminação é explícita. O predicado de flags preserva comparação de bits unsigned e fetch anterior ao dispatch. Os serviços externos são injetados e não são confundidos com backend reconstruído.

## Pendências de pesquisa preservadas

Schemas e assinaturas históricos conflitantes permanecem desconhecidos. Não há layout completo de classe do executável, original compiler/flags identificados, backend SaveIO reconstruído ou altura PBC interpretada. A identidade lógica EventFlagInt foi sustentada pela cadeia hash → factory → construtor → vtable → handler; isso não recupera a declaração C++ original. Estas limitações não impedem os contratos delimitados já testados, e não são marcadas como descobertas realizadas.

O mapa multiversão compara instruções/CFG, constantes, strings diretas, contexto e RTTI; produz candidatos incertos. Dois vínculos EventFlagInt receberam revisão técnica individual: construtor incorporado à factory do alvo e comparação terminal validada em 3.806 casos por versão. A equivalência do backend completo continua incerta. As anotações do alvo exigiram sua própria cadeia de factory/labels/vtable/assembly. Nenhum símbolo de função foi migrado automaticamente. A revisão humana de candidatos continua necessária para uma migração futura ampla. Nenhuma implementação está sendo integrada ao Elysium.

## Evidência reexecutável

`run_all.ps1` compila, testa, confere provenance e golden reports, verifica grafo sem endpoints órfãos, gera o mapa e coleta métricas. `metadata/pipeline-verification.json` indica os modos usados; `private/outputs/pipeline` preserva os logs. Os gates de versão e hashes falham em divergência. `audit_research.py` verifica os caminhos destinados ao Git e padrões de atribuição de chaves sem ler inputs ignorados.
