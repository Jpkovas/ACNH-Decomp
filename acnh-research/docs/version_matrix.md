# Builds analisados

| Papel | Versão NACP | Título base | main SHA-256 | ModuleId significativo |
|---|---|---|---|---|
| Referência disponível | 1.0.0 | 01006F8002326000 | f8d248109ff72999b4600ae3749f8c7397fb960f7ad3ab8dee3018ae9e14e900 | 7fc1baff976aeca414520cb89f4616cb |
| Alvo disponível | 3.0.3 | 01006F8002326000 | 68c7fbeda353f8e4a283eac6a9b99e713e72a327048214bf6a4e7214616b87c1 | ff1d1c05670db6021c85b624a710b963 |

Os 16 bytes restantes do ModuleId são zero. Cabeçalho NSO, tamanhos, offsets, hashes descomprimidos e proveniência do pacote ficam em `metadata/<versão>/nso.json` e `inputs.lock.json`. A identificação de versão usa `control.nacp` em 0x3060.

A referência histórica 1.1.4 citada no plano não está entre os inputs. Nenhum endereço dessa versão foi aplicado. O exemplo 3.0.2 do plano foi substituído pelo alvo efetivamente presente, 3.0.3. O update é aplicado sobre a base e essa dependência está no manifesto.

Cada análise usa base Ghidra 0x7100000000. Endereços absolutos e relativos são registrados separadamente. A segmentação das reimportações limpas coincide com a inicial. Os tamanhos BSS do MOD0 foram conferidos; o campo de reserva BSS do NSO inclui diferenças de padding. A versão 3.0.3 usa RELR para relocations relativas, diferente da base.

Mapa entre versões: [version_delta.md](version_delta.md). Candidatos de funções não transferem nomes ou tipos automaticamente.
