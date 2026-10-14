# Revisão local da segunda entrega do verificador

Data: 2026-10-13. Tarefa: `/root/cloud_repro_audit`. Coordenador:
`01a13734-dae4-73f2-87e4-e4a88be7d1da`.

R2 corrigiu e passou no Windows os três contraexemplos centrais da primeira
entrega: seletores diretos de CPU conflitantes, relatórios reais pass/fail/not_run
contraditórios e junctions internos em componentes, raízes ou ancestrais. Continua
sendo um verificador de inventário e afirmações declaradas. Um adaptador que
confira os comandos efetivos, a identidade das ferramentas e a origem dos
relatórios ainda é necessário antes da integração.

Pacote de 50.661 bytes: `acnh-repro-verifier-r2.zip`, SHA256
`b66506c3e22f6c19b2fd0c033acc29eb8297f934a244e0eacab706fc2b71d2cd`.
`verifier.py` SHA256:
`b527c86ecd80f40679efaacff6529a73526d2a93b867ffe03aa249cfb6391d0d`.
Os 27 hashes internos conferiram, os 28 arquivos importados permaneceram iguais
antes/depois e os 12 arquivos de `previous/` são idênticos ao pacote R1 local.
Fontes e documentação histórica permaneceram intactas. Licença da entrega: MIT.

## Reprodução e distinção das provas

Ambiente: Windows 11 build 26200, Python 3.12.10 AMD64. Python SHA256
`4d6f5f81a4bca11191c4c7c6b43632694d0a4ce74e068619d8fdc161d469859a`.
LLVM-MinGW Clang SHA256
`ee85bef2c733e24a26c22be3df94bd631cf9528a048fce91241c182a936737fe`.

| Grupo | Resultado local |
| --- | --- |
| Suite do pacote | 77 métodos: 73 aprovados, 4 skipped, zero falhas/erros |
| Mutações originais | 51 métodos aprovados; oito adulterações por papel continuam subtestes de um método |
| Teste Windows de junction do pacote | Executou em NTFS e passou; não foi o skip Linux |
| Skips locais | Três symlinks indisponíveis e um FIFO POSIX indisponível |
| CLI própria final | 34/34 expectativas conferidas; 23 recusas e 11 aceitações intencionais |
| NTFS próprio | Seis casos criados e recusados com `path.reparse` |
| Comparação old/new | Três contraexemplos reproduzidos: aceitos em R1 e recusados em R2 |
| Followups de features | Dois casos adicionais recusados: AVX2 duplicado e AVX2 seguido de desativação |

O followup AVX2 duplicado reaparece no lote final; esses grupos não são uma soma
de casos únicos nem chamadas ABI do jogo.

O teste de atributo reparse na comparação old/new é um **modelo**, preservando
`ntfs_execution=false`. A prova Windows real é separada: o método do pacote e
as seis fixtures próprias criaram junctions NTFS via Win32. As fixtures próprias
cobrem componente interno, componente externo, raiz pública, raiz privada,
ancestral do manifesto e ancestral de ambas as raízes. Todos exibiram
`is_junction=true`, `is_symlink=false`, atributo reparse e recusa explícita.
Os links foram removidos individualmente e a pasta temporária própria foi apagada
após verificar o limite e o nome exclusivo. Nenhum caminho do jogo foi usado.

Os casos de CPU cobrem ordem dos seletores, duplicata idêntica, `mcpu`, `/arch`,
argumentos separados, AVX2 direto/duplicado, tuning nativo, response file direto,
`-Xclang`, `/clang:`, config e plugin. As recusas previstas ocorreram. Relatórios
real_call fail/not_run vetaram entradas completas integradas tanto dentro quanto
fora de `evidence`, independentemente da ordem. Dois passes continuaram aceitos.
Falhas de fixture_model permaneceram separadas de chamadas reais; uma entrada
guarded com falha preservou a contagem de observações e cobertura zero.

Os números `report_outcome_counts` representam observações declaradas, não casos
ABI únicos, processos executados ou funções reconstruídas. Nenhum relatório
sintético foi convertido em cobertura do projeto.

Comandos executados, a partir de `acnh-research`:

```powershell
& ./private/tools/python/python.exe ./scripts/cloud_repro_team_candidate_r2_review.py --run-id windows-r2-review-02
& ./private/tools/python/python.exe ./scripts/cloud_repro_team_candidate_r2_compare.py
```

O lote NTFS foi autorizado por revisão automática fora do sandbox que impede a
criação dos links, limitado à fixture própria. `TIMING-LOCK.active` estava `false`;
os scripts conferem a liberação antes dos lotes e o runner principal antes de cada
fase/caso. Não há benchmark, módulo, runtime, gameplay ou material proprietário.

Uma primeira execução agregada terminou com exit 1 somente porque o Python
embutido local não inclui automaticamente o diretório do script em `sys.path`:
`compare_revisions.py` recebeu `ModuleNotFoundError: verifier`. Os outros resultados
desse lote foram preservados, assim como o snapshot do runner que os produziu.
O bootstrap próprio passou a inserir explicitamente o diretório revisado antes de
`runpy.run_path`, sem editar a entrega. A comparação separada e a reprodução final
com o runner corrigido terminaram com exit 0. Não se trata de falha de junction
ou de adulteração do pacote.

## Limitações ainda demonstradas

**Linker/LTO e response encaminhado:** R2 aceita os tokens
`-Wl,-plugin-opt=mcpu=native` e `-Wl,@own.rsp`, embora recuse os equivalentes
diretos conhecidos. O Clang fixado, com `-flto` e `-###`, encaminhou
`-plugin-opt=mcpu=native` ao linker. Isso demonstra o canal, sem executar o linker
ou provar que uma DLL concreta recebeu ISA do host. Flags de linker, assembler,
wrappers e response files precisam ser expandidos e auditados pelo adaptador,
ou recusados até que ele exista.

**Target declarado versus efetivo:** um manifesto `x86_64-windows` com o token
`--target=x86_64-unknown-linux-gnu` foi aceito. `clang -###` exibiu a triple Linux
efetiva, com exit 0. O campo target não é vinculado à ação efetiva nem ao formato
PE de um artefato. Exigir esse vínculo e hashes dos executáveis reais é trabalho
do adaptador/produtor; não é fornecido por este checker.

**Validade e ação do driver:** `-Wa,-mavx2` foi aceito pelo checker, mas recusado
pelo Clang fixado, com exit 1 no próprio dry run. Portanto sua aceitação lexical
não significa um bypass de ISA executado. `-Mnot_a_real_option` também passa o
skip amplo de `-M`; identidade do argv[0], modos somente dependências, impressão
ou preprocessamento não são provados pelo inventário. Nenhum `-###` desta revisão
foi apresentado como compilação ou chamada DLL.

**Raiz lexical com `..`:** uma raiz segura `anchor/../public`, com diretórios reais
sem links, foi recusada com `path.missing_or_escape`. É uma rejeição conservadora
por comparação de raiz lexical com arquivo canônico, não uma fuga aceita. Rever
erro específico para roots não canônicas ou normalizar somente depois da auditoria
da cadeia lexical; resolver a raiz antes esconderia links e recriaria a falha R1.

**Portabilidade Win32:** o filtro lexical ainda omite caracteres Win32 inválidos,
controles 1–31 e dispositivos COM/LPT com dígitos sobrescritos. É achado estático,
sem nova execução Linux nesta revisão. Completar o filtro por componente em todos
os hosts continua necessário; uma falha incidental de abertura no Windows não
comprova portabilidade de um manifesto anteriormente aprovado em outro host.
As restrições Win32 são documentadas pela
[Microsoft](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file).

**Limites de autoria:** hashes, nomes de status, denominador e intervalos continuam
afirmações revisadas pelo produtor. O checker não examina corpos completos,
espaços main/SDK, código traduzido, fallback, closure do build, módulos carregados,
conteúdo da pesquisa 3.0.3 ou persistência do jogo. Os achados independentes estão
em `private/team/cloud-repro-review/revision2/static-review.md`; ele e seu revisor
de CPU fizeram apenas leitura.

## Compatibilidade com a receita local observada

R2 não fornece patch novo. O patch em `previous/` pertence à revisão pública antiga,
usa `TargetCpu`/`ACNH_TARGET_CPU` e não deve ser aplicado à árvore atual. A receita
atual, lida sem alterações nesta tarefa, usa `CpuTarget`/`ACNH_CPU_TARGET`, preserva
SaveIoProfile/RuntimePath, PlayerConnected, CleanModuleBuild, isolamento de outputs
e veto a objetos cacheados quando a CPU muda. O dono dessa receita é `pin_review`.

Hashes observados durante a reprodução final:

- `windows_bridge/CMakeLists.txt`: `18df28b8e1cc03753d26a5a7591840dbc092ae27f4db0106b31e8bfcfc6aa0b6`.
- `scripts/build_windows_game.ps1`: `32e3382fe1a36812205a4dc44c99f928cdcf5b5ae5838a53fab50ae748c9f38e`.

Essa receita emite `-mcx16` para native/v2 e `-mno-cx16` para x86-64; R2 recusa
ambos na política conservadora de features. Um adaptador não pode simplesmente
omitir flags consumidos para conseguir `valid=true`: deve registrar o argv real
e ter política revisada para features explícitas/redundantes e o baseline escolhido.
Nesta tarefa não foi aplicado patch, configurado CMake ou compilado o módulo.

## Entrega e gates posteriores

Novos arquivos públicos desta tarefa: dois scripts `cloud_repro_team_candidate_r2*`,
este relatório e `REVISION2-delivery.json`. Resultados, fixtures, snapshots e logs
permanecem em `private/team/cloud-repro-review/revision2/`, com inventário de hashes.
R1 e importação R2 permanecem intactas. Nenhum stage, commit, push ou publicação.

Antes de promoção, revisar adaptador por driver/ação/target, ligação do executável
ao toolchain inventariado, canais encaminhados e CPU efetiva de todas as etapas;
completar nomes Win32 e política de raízes canônicas; produzir evidências reais
ligadas ao DLL/runtime observado e executar builds independentes com entradas
imutáveis. Boot, gameplay, input, áudio, salvamento e reload exigem suas provas reais.

Contribuição de cobertura desta infraestrutura: **0 entradas / 0 bytes**.
Gameplay e save/reload reais: **não validados**.
