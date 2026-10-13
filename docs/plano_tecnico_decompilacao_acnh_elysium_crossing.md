# Plano técnico de engenharia reversa e decompilação de Animal Crossing: New Horizons

**Projeto relacionado:** Elysium Crossing  
**Data de pesquisa:** 12 de outubro de 2026  
**Propósito:** reconstrução incremental, auditável e tecnicamente verificável de subsistemas de ACNH, com uma eventual rota para *matching decompilation*. O Elysium Crossing, baseado em AC de GameCube, permanece um projeto separado.

> **Escopo e limites.** Este documento trata de análise de executáveis e dados obtidos legitimamente, não de obtenção de cópias pirateadas, chaves, quebra de DRM, desbloqueio de consoles ou distribuição de arquivos proprietários. A análise jurídica deve ser feita para a jurisdição e o método de obtenção aplicável; possuir o jogo não concede automaticamente todos os direitos de extração, redistribuição ou criação de derivados.

## 0. Definição de sucesso

Trabalhar com três níveis independentes de resultado:

- **L1 — Recuperação analítica:** disassembly, pseudocódigo, mapa de funções, hierarquia de classes, layouts de memória, tabelas e fluxos de eventos. Nada aqui implica que haja um programa recompilável.
- **L2 — Reconstrução funcional:** código-fonte novo, organizado, compilável, com testes que reproduzem o comportamento observado para uma especificação delimitada.
- **L3 — Reconstrução binária (*matching*):** comparação de código gerado para funções individuais, com condições de compilador, otimização e linkedição reproduzidas ou aproximadas, evoluindo para correspondência binária mensurada. Uma função funcionalmente equivalente não é necessariamente matching.

**Marcos:** M0 = binário reproduzivelmente importado; M1 = esquema de símbolos e classes versionado; M2 = um EventFlow decodificado e validado; M3 = primeiro módulo C++ funcional; M4 = primeira função com diff ARM64 mensurável; M5 = catálogo de sistemas reaproveitável pelo Elysium Crossing.

**Não prometer:** compilar ACNH inteiro, portar o Switch para celular, obter todos os nomes originais, nem correspondência integral. São projetos de outra magnitude.

## 1. Levantamento técnico e bibliográfico

| Referência | Valor comprovado | Limitações e observações |
|---|---|---|
| [R1] CylindricalEarth | Pesquisa específica de ACNH; BCSV, MSBT, PBC, saves, EventFlow e scripts Ghidra | Scripts e endereços historicamente concentrados em versões antigas; `BuildRTTIHierarchy.py` é especializado em EventFlow |
| [R2] ACNH EventFlow Decompiler | `.bfevfl` → formato semelhante a código, exige `functions.csv` coerente com a versão | Não descompila o `main` ARM64 |
| [R3] ACNH EventFlow Compiler | Formato legível → `.bfevfl`; autor relata compilação de 562/562 fluxos na v1.11.0 | Compilar com sucesso não implica byte matching |
| [R4] Ghidra + Switch Loader | Carregamento de NSO/NRO, análise AArch64 | Compatibilidade da versão instalada deve ser verificada |
| [R5] switchbrew NSO0 | Layout do formato, segmentos `.text`, `.rodata`, `.data`, compressão LZ4 | Documenta formato, não fornece o executável do jogo |
| [R6] ARM AAPCS64 | Convenções de chamada e passagem de parâmetros de AArch64 | É referência geral; conferir particularidades do runtime/SDK |
| [R7] objdiff | Comparação de objetos e instruções ARM64/Switch | Só é útil para L3 com setup correto de compilação e endereçamento |
| [R8] Ghidra analyzeHeadless | Pipeline de importação e scripts reprodutíveis | Algumas rotinas GUI de terceiros podem precisar adaptação headless |
| [R9] Nintendo, notas de atualização | Identifica 3.0.2, disponível em 13/04/2026 | Estado do jogo, não uma especificação da arquitetura interna |
| [R10] ac-decomp | Práticas de diretórios, build, símbolos, objdiff e exclusão de assets | Seu pipeline e `dtk-template` são de GameCube/Wii, não compatíveis diretamente com Switch |
| [R11] Switch Toolbox | Inspeção de BFRES/BNTX/SARC e outros formatos onde aplicáveis | Suporte a formato não implica compatibilidade com todo arquivo de ACNH |
| [R12] Capstone | Desmontagem de instruções AArch64 para scripts rápidos | Não recupera tipos nem lógica de alto nível sozinho |

## 2. Escolha das versões e proveniência

**Vref:** versão historicamente compatível com os dados do CylindricalEarth, idealmente **v1.1.4** se uma cópia legitimamente acessível estiver disponível. Serve como versão de investigação, não como alvo final.

**Vtarget:** versão moderna sob investigação, por exemplo **v3.0.2**, que consta na documentação de atualização da Nintendo de abril de 2026. Essa versão deve ser confirmada contra os arquivos que de fato serão analisados.

**Regras:**
1. Tratar cada versão como um executável distinto. Nunca reutilizar offset, endereço de vtable, schema ou assinatura entre versões sem conferência.
2. Guardar para cada entrada: título, versão, origem lícita, caminho interno, módulo, tamanho, SHA-256, NSO ModuleId/BuildId quando disponível, data de análise, versão do loader/Ghidra.
3. Armazenar binários e recursos somente em diretórios locais ignorados pelo Git.
4. Registrar `version_id` em toda função, tipo, enumeração, observação ou teste.
5. Decidir explicitamente se as mudanças entre versões merecem migração de *símbolos* ou reconstrução novamente.

**Deliverable M0:** manifesto `inputs.lock.json`, checksums SHA-256 e um registro claro de quais artefatos vieram de quais builds.

## 3. Estrutura de repositório proposta

```text
acnh-research/
├── README.md
├── LICENSE_NOTES.md
├── docs/
│   ├── methodology.md
│   ├── version_matrix.md
│   ├── architecture.md
│   ├── findings/
│   └── references.md
├── config/
│   ├── versions.yaml
│   └── confidence_rules.yaml
├── scripts/
│   ├── audit_inputs.py
│   ├── inspect_nso.py
│   ├── normalize_symbols.py
│   ├── map_versions.py
│   └── export_ghidra_inventory.py
├── ghidra_scripts/
│   ├── ExportFunctionInventory.py
│   ├── ExportStringXrefs.py
│   └── ImportValidatedSymbols.py
├── metadata/
│   ├── v1.1.4/
│   └── v3.0.2/
├── research/
│   ├── eventflow/
│   ├── data_tables/
│   ├── actors/
│   ├── inventory/
│   └── saving/
├── reconstructed/
│   ├── include/
│   ├── src/
│   └── tests/
├── tests/
│   ├── fixtures_synthetic/
│   └── golden_manifest.json
├── vendor/                     # Somente fontes e licenças permitidas
└── private/                    # gitignored: ROM/NSO/saves/dumps/Ghidra db
    ├── inputs/
    ├── ghidra/
    └── outputs/
```

O repositório `Elysium Crossing` **não** deve receber dumps, pseudocódigo copiado indiscriminadamente, nem assets de ACNH. Registrar requisitos funcionais observados e implementações próprias no projeto original, preservando proveniência e licenças.

## 4. Fase A — Preparação do binário e da análise AArch64

### A1. Entradas

Trabalhar somente com materiais obtidos e processados por meios autorizados. São necessárias as partes acessíveis de uma instalação/build de ACNH, tipicamente o executável principal no conteúdo **ExeFS** e os arquivos de dados **RomFS**. Não incluir neste projeto passos de contorno de proteções técnicas ou acesso a chaves.

No caso de NSO0, o header documenta `.text`, `.rodata`, `.data`, `BSS`, `ModuleId` e metadados de compressão LZ4. O Ghidra Switch Loader reconhece a assinatura `NSO0` e usa o processador `AARCH64:LE:64:v8A` para executáveis ARM64.

### A2. Setup

- Instalar uma versão estável do **Ghidra** e Java compatível.
- Instalar o **Ghidra-Switch-Loader** seguindo a documentação de build com JDK 21 e extensão zip; confirmar requisitos da revisão clonada.
- Instalar Python, Git, CMake/Ninja e Clang/LLVM para scripts e construção do código reconstruído.
- Opcional: **Capstone** para análise rápida de *disassembly* e **objdiff** para comparações.

Exemplo ilustrativo de importação automatizada, **após** validar loader e permissões locais:

```bash
"$GHIDRA_HOME/support/analyzeHeadless" \
  "$PWD/private/ghidra" acnh_reference \
  -import "$PWD/private/inputs/v1.1.4/main" \
  -log "$PWD/private/outputs/ghidra-import.log"
```

O caminho `main` é apenas uma convenção de exemplo. Não usar `-processor` à força antes de conferir que o loader reconheceu o NSO corretamente. O cabeçalho e a escolha de formato devem ser validados no log e na interface. Processar scripts próprios em passagens separadas depois que a autoanálise estiver estável.

### A3. Checagens obrigatórias após importação

- O arquivo foi identificado como **NSO0**? Ou o input é um módulo/ELF de outra natureza?
- A arquitetura está definida como **AArch64 little-endian**?
- `.text/.rodata/.data/BSS` e relocations foram interpretadas corretamente?
- A base de imagem e os endereços em xrefs são consistentes?
- Há muitas regiões de código não identificadas e entradas de função falsas?
- A análise detecta strings, referências, thunks, externals e indireções?
- Os logs do analisador e da versão da ferramenta foram preservados?

**Critério de saída:** análise reexecutável em ambiente limpo com distribuição de segmentos idêntica para o mesmo SHA-256, mais relatório de funções, basic blocks e xrefs.

## 5. Fase B — Recuperação de símbolos, RTTI e modelos de dados

Reaproveitar, **testando compatibilidade com a API do Ghidra atual**, scripts documentados em `Treeki/CylindricalEarth/ghidra_scripts`:

- `FunHelper.py`: auxilia descoberta de funções; projetado historicamente para v1.1.4.
- `BuildRTTIHierarchy.py`: recupera herança e renomeia vtables/métodos, **especializado em receptores EventFlow**. Não presumir recuperação global.
- `ACNHSaveSchemaV3.py`: importa estruturas conhecidas do formato de save para o banco de tipos.
- `ACEnumScraper2.py`: extrai enums ligados a tabelas BCSV.
- `IntrospectBCSVs.py`: ferramenta mais antiga especializada nas classes leitoras de BCSV.

**Ordem de execução:** baseline → análise de strings e referências → anotação de RTTI conhecida → aplicação de structs e enums validados → correção das assinaturas das funções → nova rodada de propagação de tipos → exportação de símbolos.

**Propriedades de cada símbolo**:

```yaml
version: '1.1.4'
module: main
address: '0x...'
size: null
name: 'EventFlow::...'
name_status: inferred      # original | demangled | inferred | provisional
confidence: medium        # high | medium | low
kind: function            # function | vtable | class | field | enum | global
signature: null
callers: []
callees: []
evidence: ['rtti', 'xref', 'string_reference']
reviewer: null
notes: ''
```

Nomes são hipóteses com evidências. **Não rebatizar centenas de `FUN_xxxx` como se a IA tivesse recuperado nomes originais.** Usar os modos `inferred` e `provisional` até que haja RTTI, chamada, dado ou teste observável sustentando a interpretação.

**Critério de saída:** inventário de funções e classes, evidências rastreáveis, tipos que não conflitam com acesso à memória, lista de símbolos de alta confiança e mapa de navegação entre módulos.

## 6. Fase C — Engenharia reversa dos formatos de dados

Essa fase pode produzir resultados úteis muito antes de decompilar uma grande fração do executável.

### C1. EventFlow

Usar `asteriation/acnh-eventflow-decompiler`, `asteriation/acnh-eventflow-compiler` e os arquivos `evfl/eventflow_actor_info.json` e `evfl/eventflow_vtables.json` do CylindricalEarth como ponto de partida.

1. Identificar os arquivos `.bfevfl` disponíveis no conjunto RomFS autorizado.
2. Obter/produzir `functions.csv` **da mesma versão** que os arquivos, com tipos de ações e queries.
3. Descompilar uma amostra com `main.py --functions functions.csv --out-dir ...` conforme o README; `hints.json` é opcional.
4. Construir análise de grafos: nós, edges, ações, condições, parâmetros, ciclos, subfluxos, atores e chamadas.
5. Compilar novamente com o projeto complementar e verificar leitura do resultado, equivalência estrutural e, quando aplicável, equivalência semântica. Bytes, hashes e tamanho **não** precisam coincidir para considerar um round-trip semântico bem-sucedido.
6. Conectar os nomes de ações/queries aos métodos e vtables do executável, registrando as evidências por versão.

**Saída:** catálogo de fluxos, ações e queries, com esquemas de argumentos, arestas condicionais e reimplementação de uma máquina de estados para um fluxo pequeno.

### C2. BCSV

Usar `bcsv.py`, `specs.py` e `ACEnumScraper2.py`. Construir inventário de tabela → colunas → tipos → enumerações → referências cruzadas. Fazer testes de parser com entradas sintéticas e entradas privadas de cada versão. Não presumir que os nomes ou esquemas estejam completos.

### C3. MSBT e recursos

Usar `msbt.py` e `generate_msbt_hints.py` para ligar referências de mensagens aos fluxos. `Switch-Toolbox` e `zeldamods/sarc` podem ajudar a inspecionar formatos compatíveis e arquivos aninhados, após verificar extensão e compatibilidade real. Não assumir que qualquer BFRES/anim contém o que seu nome sugere.

### C4. SaveIO e PBC

`savefile/parse_smmh.py`, `ACNHSaveSchemaV3.py`, `pbc.py` e `display_pbc.py` documentam caminhos de trabalho. Priorizar leitura de layouts e interpretação de colisão/altura; manter saves originais em backup, tratar campos desconhecidos explicitamente e **não editar dados reais sem testes de leitura e escrita em cópias**.

## 7. Fase D — Recuperação da lógica do executável

Para cada subsistema selecionado:

1. **Selecionar uma âncora confiável:** evento de EventFlow, nome de enum BCSV, string, vtable, referência de save ou chamada reconhecida.
2. **Localizar entradas no binário:** xrefs, referência a objeto, vtable slot, construtor e método público/handler.
3. **Delimitar o grafo relevante:** callers, callees, dependências de dados, estado persistente, callbacks e desvios.
4. **Recuperar modelos de memória:** `struct`/classe, alinhamento, offsets, tipos primitivos, arrays, ponteiros e enumeradores. Marcar offsets não validados.
5. **Interpretar o pseudocódigo sem confiar cegamente nele:** examinar assembly nos trechos com loops, switch/jump-table, conversão de tipos, vetorização, overflow, aliases, inlining e dispatch virtual.
6. **Registrar comportamento como contrato:** pré-condições, pós-condições, efeitos, mudanças de estado, argumentos e casos-limite.
7. **Reescrever em C++ próprio:** tipos explícitos, interface definida, separação de parsing, lógica e dependências de Switch.
8. **Testar** casos sintéticos e, quando possível, comparar resultados observáveis em execução autorizada do jogo.
9. **Atribuir grau de confiança:** observado, inferido, não testado, parcialmente equivalente ou divergente.

**Alvos-piloto preferenciais:** (1) uma query/action EventFlow pequena; (2) um leitor de campo BCSV; (3) uma transição de inventário ou item cujo estado inicial/final seja observável. Evitar começar por renderizador, rede, física integral ou gerenciador de mundo.

**Detalhes do ABI:** interpretar a passagem de argumentos e retorno segundo AAPCS64/AArch64, mas observar convenções específicas da implementação, funções membro, indireções do runtime e tipos agregados. Referência [R6].

## 8. Fase E — Reconstrução e validação

### E1. Compilação funcional primeiro

Usar CMake + Clang/LLVM para compilar módulos isolados em ambiente de teste. Criar *stubs* para serviços não reconstruídos (arquivos, relógio, RNG, I/O do Switch), identificando claramente onde ocorre a substituição. Isso permite L2 sem prometer executável NSO completo.

### E2. Validação em três camadas

- **Testes estruturais:** parse/serialize, tamanhos, offsets, enumeração e grafos corretos.
- **Testes comportamentais:** input → output/estado, invariantes, edge cases, testes de propriedade, fixtures sintéticas. Onde a observação no jogo original for permitida, comparar traces sem divulgar conteúdo proprietário.
- **Testes binários:** objetos AArch64 comparáveis no `objdiff`, isolamento por função, checagem de instruções, registradores, ordenação dos blocos, constantes e relocations. Distinguir métricas de *exact match* da mera semelhança.

### E3. Investigação de compilador original

Antes de perseguir matching, identificar evidências técnicas de toolchain/flags/ABI, comportamento de inlining, padrões de instruções e linking. Clang genérico **não garante** reproduzir o binário original. `objdiff` suporta ARM64, mas isso não significa que o NSO e as bibliotecas originais sejam trivialmente recompiláveis.

### E4. Métricas não enganosas

Relatar por módulo:

- funções descobertas e funções revisadas;
- funções com nome de alta confiança;
- classes/structs com offsets validados;
- formatos com round-trip testado;
- módulos L2 compiláveis;
- funções L3 com diff medido;
- cobertura de **comportamentos-alvo**, não porcentagem fictícia do jogo inteiro.

**Definição de pronto de uma função:** proveniência identificada, assinatura revisada, efeitos descritos, testes cobrindo normal + erro + edge case, ausência de divergência conhecida injustificada, diff registrado se a tarefa for L3.

## 9. Fase F — Estratégia multiversão

Construir um sistema `map_versions.py` que produza uma hipótese de correspondência entre Vref e Vtarget usando: assinaturas normalizadas da sequência de instruções, strings/constantes, callers/callees, formato dos CFGs e características de RTTI. Nenhuma dessas evidências isoladamente garante equivalência.

- Gerar **candidatos** com score e motivos.
- Revisar manualmente casos com função dividida, fundida, inline, removida ou movida entre versões.
- Registrar `mapped`, `uncertain`, `absent`, `split`, `merged` e `behavior_changed`.
- Transferir nomes e tipos somente após verificação do contexto no binário de destino.
- Produzir diff de sistemas por versão, separando mudanças de tabelas e mudanças de código.

**Saída:** `metadata/version-map.json` + relatório `docs/version_delta.md` com hyperlinks para análise local e evidência textual não proprietária.

## 10. Sequenciamento em marcos verificáveis

| Marco | Entrega | Critério objetivo de aprovação |
|---|---|---|
| M0 — Reprodutibilidade | Version lock, hashes, Ghidra + loader | Importação reproduzível, segmentação e arquitetura conferidas |
| M1 — Índice | Inventário de funções, RTTI, BCSV, MSBT, EventFlow | Evidência e confiança por símbolo; sem endereços órfãos |
| M2 — EventFlow | Descompilador funcional para fluxo-piloto | AST/CFG coerentes + teste de ida e volta |
| M3 — C++ funcional | Um parser/método independente recompilado | Testes unitários, adversariais e de regressão aprovados |
| M4 — Matching piloto | Uma função ARM64 simples selecionada | Relatório objdiff e justificativa de divergências |
| M5 — Ponte Elysium | Catálogo de mecânicas e contratos | Implementação própria no Elysium validada sem dependência do runtime Switch |
| M6 — Escala | Novos módulos com metodologia padronizada | Pipeline automático de métricas e code review técnico |

**Decisão após M4:** só perseguir matching extensivo se o compilador/flags forem suficientemente identificáveis e se a relação custo-benefício justificar. Caso contrário, manter L1/L2 e priorizar a transferência de especificações de comportamento.

## 11. Alvos para Elysium Crossing (sem misturar as codebases)

| Sistema de ACNH | Dados / âncora de RE | Adaptação recomendada |
|---|---|---|
| Interações e eventos | EventFlow, actions/queries, vtables | Máquina de estados independente; eventos multiplayer sincronizados |
| Inventário e itens | BCSV, chamadas de item, persistência | Esquema de itens próprio e validador servidor |
| Crafting | Regras de dados e eventos observáveis | Receitas e custos reimplementados; transação autoritativa |
| Decoração e objetos | Tabelas de item, regras de colocação | Validação de colisão, grade e permissões |
| NPCs | Rotinas de estado, eventos, tabelas | Scheduler e IA leves; otimizar para mobile |
| Terreno e colisão | Mapas PBC e regras de interação | Sistema próprio de malha/heightmap e pathfinding |
| Salvamento | SaveIO, campos e invariantes | Persistência própria, migrações e testes |
| Multiplayer | Observar interfaces de alto nível sem copiar netcode | Arquitetura nova cliente/servidor, autoridade do servidor |

Não usar a decompilação de ACNH como dependência de build do projeto de GameCube. Estudar uma funcionalidade e implementar comportamento equivalente é uma linha de trabalho distinta de copiar código ou recursos do jogo.

## 12. Agente de IA: protocolo de execução

**Papel:** assistente de engenharia reversa e documentação. **Não** atribuir-lhe descobertas sem prova ou dar-lhe autonomia para publicar binários.

Para cada issue:

1. Ler `docs/methodology.md` e `config/versions.yaml`.
2. Escolher **um** objetivo pequeno, com versão e módulo explícitos.
3. Consultar documentação upstream e verificar existência/compatibilidade dos scripts.
4. Reunir evidências objetivas (endereço versionado, xrefs, string, RTTI, tabela, pseudocódigo local, desassembly ou teste).
5. Propor hipótese e listar pelo menos uma explicação alternativa plausível.
6. Implementar teste/experimento discriminante antes de afirmar a conclusão.
7. Produzir artefato pequeno e reproduzível (script, schema, teste, documentação ou função isolada).
8. Rodar testes e registrar logs.
9. Atualizar mapa de símbolos e nível de confiança.
10. Abrir PR isolada; não alterar Elysium Crossing automaticamente.

**Modelo de issue:**

```yaml
id: ACNH-RE-001
version: '1.1.4'
module: main
subsystem: eventflow
objective: 'Identificar o handler de uma action conhecida'
anchors:
  - 'evfl/eventflow_actor_info.json'
required_evidence:
  - 'xref e/ou RTTI para o endereço de handler'
  - 'assinatura e disposição de parâmetros justificadas'
  - 'fluxo de controle revisado no assembly'
validation:
  - 'teste de caso normal'
  - 'teste de caso-limite'
  - 'ausência de conflito com outro consumidor da vtable'
outputs:
  - 'metadata/v1.1.4/eventflow_symbols.yaml'
  - 'docs/findings/ACNH-RE-001.md'
status: todo
```

**Guardrails:** não inventar endereço, nome de classe, número de funções, arquivo ou taxa de matching. Não misturar bases de endereçamento. Não promover nomenclatura sugerida por LLM a fato sem fonte. Não executar scripts desconhecidos fora de sandbox. Sem commits de arquivos Nintendo. Licenças de terceiros devem ser preservadas e avaliadas antes de incorporar código.

## 13. Primeiras 10 tarefas concretas

1. Criar `acnh-research` com regras de versionamento, LICENSE_NOTES e `.gitignore` de binários.
2. Escolher e registrar Vref e Vtarget; produzir `inputs.lock.json` e checksums.
3. Instalar Ghidra e Switch Loader, conferir AArch64/NSO0, exportar relatório de importação.
4. Clonar os projetos públicos referenciados, registrar commits e respectivas licenças.
5. Reproduzir o comportamento dos scripts CylindricalEarth compatíveis, começando por inventário e RTTI.
6. Gerar base `symbols.yaml` e exportação de xrefs / strings / funções do Ghidra.
7. Catalogar BCSV e EventFlow, incluindo cobertura por versão e tipos desconhecidos.
8. Produzir primeiro round-trip de EventFlow e testes da estrutura do grafo.
9. Reconstruir uma query/action pequena em C++ com três casos de teste e documentação.
10. Configurar comparação objdiff para um objeto AArch64 isolado, mesmo que o primeiro relatório mostre divergências.

## 14. Riscos e mitigação

- **Mudança de versão:** separação rigorosa e mapeamento por evidências; não copiar endereços.
- **Falsa precisão do decompilador:** revisar assembly/ABI e registrar hipóteses.
- **Matching inviável por toolchain:** começar L2 e abandonar L3 quando o custo exceder os benefícios.
- **Diferenças de middleware/runtime:** *stubs* e interfaces explícitas em código de pesquisa.
- **Muitos scripts legados:** testes em ambiente isolado e pins de commit/Ghidra.
- **Automatização de IA alucinada:** provas, confiança e revisão humana obrigatórias.
- **Direitos autorais/DRM/licenças:** inputs privados, nada de redistribuição, consulta jurídica quando for disponibilizar trabalho ou derivar software.
- **Desvio de escopo:** manter Elysium Crossing separado e usar entregas semanais por subsistema.

## 15. Bibliografia e fontes primárias

**[R1]** Treeki (Ash Wolf/Ninji), *CylindricalEarth: Research into the Internals of Animal Crossing: New Horizons*. Repositório, scripts e README. https://github.com/Treeki/CylindricalEarth

**[R2]** asteriation, *acnh-eventflow-decompiler*. README e uso do `functions.csv`. https://github.com/asteriation/acnh-eventflow-decompiler

**[R3]** asteriation, *acnh-eventflow-compiler*. README e métricas dos fluxos v1.11.0. https://github.com/asteriation/acnh-eventflow-compiler

**[R4]** Adubbz, *Ghidra-Switch-Loader*. README e `SwitchLoader.java`. https://github.com/Adubbz/Ghidra-Switch-Loader

**[R5]** switchbrew, *NSO0*. Especificação comunitária do executável principal Switch. https://switchbrew.org/wiki/NSO0

**[R6]** Arm, *Procedure Call Standard for the Arm 64-bit Architecture (AAPCS64)*. https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst

**[R7]** encounter, *objdiff*. Suporte ARM64, diff de funções e objetos. https://github.com/encounter/objdiff

**[R8]** NSA, *Ghidra Headless Analyzer README*. https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/RuntimeScripts/support/analyzeHeadlessREADME.md

**[R9]** Nintendo, *Como Atualizar Animal Crossing: New Horizons*; v3.0.2 de 13 de abril de 2026. https://pt-americas-support.nintendo.com/app/answers/detail/a_id/45806/p/988/c/950

**[R10]** ACreTeam, *ac-decomp*, metodologia de decompilação do GameCube. https://github.com/ACreTeam/ac-decomp

**[R11]** KillzXGaming, *Switch-Toolbox*, formatos de dados/modelos compatíveis. https://github.com/KillzXGaming/Switch-Toolbox

**[R12]** Capstone, *Capstone Disassembly Framework*. https://github.com/capstone-engine/capstone

**[R13]** decompals, *decompedia*, fundamentos de *matching decompilation*. https://github.com/decompals/decompedia

**[R14]** zeldamods, *evfl*, parsing/escrita de formatos EventFlow. https://github.com/zeldamods/evfl

**[R15]** zeldamods, *sarc*, parser de arquivo SARC. https://github.com/zeldamods/sarc

**[R16]** encounter, *dtk-template*, referência de organização para GameCube/Wii; **não é template Switch pronto**. https://github.com/encounter/dtk-template

---

**Recomendação de execução:** começar com M0 → M1 → M2 → M3 e realizar M4 apenas como estudo de viabilidade. O maior ganho de curto prazo para o Elysium Crossing será uma especificação verificável de EventFlow + itens/inventário, não um executável inteiro de ACNH reconstituído.
