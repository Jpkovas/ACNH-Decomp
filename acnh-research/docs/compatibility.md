# Compatibilidade dos projetos de referência

Os commits e hashes de licenças estão em `config/sources.lock.json`. A inspeção do checkout real prevalece sobre os nomes exemplificativos do plano.

| Referência do plano | Evidência no checkout | Uso realizado |
|---|---|---|
| FunHelper.py | Existe, contém pressupostos/endereço histórico 1.1.4 | Discovery do Ghidra moderno e âncoras versionadas explícitas; não executado cegamente |
| BuildRTTIHierarchy.py | Existe; Python/Jython antigo, caminhos absolutos e labels esperados de receptores | Leitura independente de RTTI Itanium e recuperação pontual de vtable customizada; sem alegar recuperação global |
| ACNHSaveSchemaV3.py | Existe; schemas e caminhos antigos | BYML real lido, offsets/nested sizes validados por arquivo; nenhum endereço histórico aplicado |
| ACEnumScraper2.py | Não existe nessa revisão | ACNHScraperV3.py existe, com offsets 1.3; specs_100 verificado somente com 1.0.0; enums desconhecidos preservados |
| IntrospectBCSVs.py | Referência histórica especializada | Parser estrutural próprio e oracle bcsv.py; esquema do executável não inventado |
| eventflow_actor_info.json / eventflow_vtables.json | Não existem nessa revisão | Arquivos evflActors114/120/130 e bindInfo120 são históricos; os catálogos novos usam BFEVFL/BindInfo da versão efetiva |
| specs.py | Conteúdo é referência textual para specs_160.py | Importação explícita de specs_100.py; nenhuma tentativa de executar specs.py como módulo válido |
| parse_smmh.py | Faz leitura e escrita de arquivos também em código de nível superior | Não importado/executado diretamente; chaves estruturais revisadas e validador próprio sem nomes antigos |
| generate_msbt_hints.py | Converte tags em texto e faz I/O de nível superior | MSBT/index de labels e message xrefs próprios; não se pressupôs conservação semântica de todos os tags |
| acnh-eventflow compiler/decompiler | Revisões fixadas funcionaram no piloto das duas versões | Python 3.12 embutido com wrapper de sys.path, funções da mesma versão e grafo canônico |
| zeldamods evfl | Diferenças de vardef em parte do conjunto ACNH | Parser ACNH específico como alternativa conferida |
| Ghidra Switch Loader | Source compilou contra Ghidra 12.1.4/JDK21 | NSO reconhecido; reimportações e relocations testadas; GOT alvo não rotulado separadamente |
| hactool 1.4.0 | Base funciona; update falha no layout BKTR | 1.5.4 borntohonk fixado, com correção de validação de padding BKTR conferida; update extraído |
| ac-decomp / dtk-template | Pipeline GameCube/Wii | Referência de organização; não usado como build Switch |
| Switch Toolbox | Checkout e licença preservados | Referência opcional; não houve alegação de validação BFRES/BNTX ou execução da GUI |

O perfil baseline mantém análise de switch e desliga Decompiler Parameter ID e IPC scanning. As assinaturas ainda são provisórias. Cada projeto usa diretório de settings/cache próprio para evitar lock OSGi durante análises concorrentes. Os erros de scripts são verificados no log além do exit code do processo Java.
