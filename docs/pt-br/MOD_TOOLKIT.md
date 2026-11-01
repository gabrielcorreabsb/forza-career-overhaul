# Caixa de ferramentas do mod

> 🌐 **Português** · [English](../en/MOD_TOOLKIT.md)

**O que é.** Um mapa do que o Career Overhaul consegue mudar hoje, o quanto temos
de certeza de cada alavanca e o que ainda está em teste. É a resposta curta para
"o que o mod faz?". A evidência de cada linha está em
[DISCOVERIES](../project/DISCOVERIES.md), [MODDING_SURFACE](../reference/MODDING_SURFACE.md),
[RACE_SYSTEM](../reference/RACE_SYSTEM.md) e [OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md)
(esses quatro estão em inglês).

Rótulos de evidência: **verified** (a mudança foi feita e o efeito visto no jogo),
**observed** (visto, com poucas corridas ou de forma indireta), **hypothesis**
(deduzido dos dados ou dos nomes, não executado). Status: ✅ pronto · 🧪 em teste ·
⛔ fechado.

## 1. Pilares

### Estrutura da carreira e textos
| alavanca | status | evidência | ferramenta / guia |
|---|---|---|---|
| árvore cup → ladder → série → evento: ordem, nomes, arte (reuso da arte existente) | ✅ | verified | [tutorial 02](../tutorials/02_reorder.md), [03](../tutorials/03_new_series.md) |
| séries novas, com ids próprios | ✅ | verified | `build_series.py` |
| nomes e descrições (chaves de texto novas, de qualquer tamanho) | ✅ | verified | `str_edit.py`, [tutorial 01](../tutorials/01_rename.md) |
| carro livre × carro travado por série; tela de escolha do primeiro carro | 🧪 | hypothesis | [CAREER_BASICS](../guides/CAREER_BASICS.md) |

### Evento
| alavanca | status | evidência | ferramenta / guia |
|---|---|---|---|
| pista e número de voltas por evento (vale o override do evento) | ✅ | verified | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| teto de desempenho por evento (vale o valor do evento, não o do override) | ✅ | verified | [DISCOVERIES](../project/DISCOVERIES.md) |
| elegibilidade de carros por lista de aceitos | ✅ | verified | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| limites numéricos de carro (PI, ano, potência, peso) | 🧪 | hypothesis | — |

### Roster e comportamento da IA
| alavanca | status | evidência | ferramenta / guia |
|---|---|---|---|
| roster que acompanha o PI do jogador, ou lista fixa multiclasse | ✅ | verified | [AI_GRIDS](../guides/AI_GRIDS.md), [tutorial 04](../tutorials/04_ai_grid.md) |
| pool maior que o grid (campo diferente a cada corrida) e faixas largas de PI | ✅ | verified | [CUSTOM_RACE](../guides/CUSTOM_RACE.md) |
| grids acima de 24 carros | 🧪 | a testar | — |
| elástico (rubber banding) da IA nos geradores da carreira | já desligado | observed | [MODDING_SURFACE](../reference/MODDING_SURFACE.md) |
| catch-up e slow-down da IA na corrida e no treino | 🧪 | hypothesis | — |
| ajustes globais da IA que também atingem o multiplayer | ⛔ | — | não mexemos sem conversar |

### Sessão: treino e qualify
| alavanca | status | evidência | ferramenta / guia |
|---|---|---|---|
| voltas de treino limitadas → sessão cronometrada (**não existe sessão de qualify separada** na carreira) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.5 |
| trackday: sem treino, largada lançada, uma volta | ✅ | verified | [CIRCUIT_EXPERIENCE](../guides/CIRCUIT_EXPERIENCE.md) |
| sessão de uma volta | 🧪 | hypothesis | — |
| pneu padrão, escala de combustível e desgaste de pneu da carreira | 🧪 | hypothesis | — |

### Grid e posição de largada
| alavanca | status | evidência |
|---|---|---|
| o grid da **IA** segue a classificação do treino | ✅ | observed |
| a vaga do **humano** é a escolhida na tela de aposta de posição, quando ela está ligada | ✅ | verified |
| ligar ou desligar a tela de aposta (uma flag do cliente) | ✅ | verified |
| a vaga do humano com a tela desligada é uma constante por evento | observed | origem desconhecida |
| a vaga que a tela sugere | ⛔ constante | não acompanha o tempo de treino do jogador, a tabela de aposta nem o termo de tempo projetado |
| quantas vagas a tela lista | ⛔ não é dado | o cache não muda isso |
| o **bônus pago por vaga** (tabela de aposta do cup) | 🧪 | a tela lê a tabela; uma curva própria e o crédito no fim da corrida estão em teste |

A tabela de bônus pertence a um **cup**, então vale para todas as séries desse cup.

### Flags do cliente
O cliente lê suas feature flags do cache (verified). Listas por modo (tipo de pneu,
escala de combustível) com um item para a carreira afetam só a carreira. Uma flag
compartilhada com o Featured ou o multiplayer não é alterada sem conversar; depois
de mudar qualquer flag, abra um evento Featured ou multiplayer para confirmar que
nada mudou.

## 2. Receitas

| receita | funciona hoje? | como |
|---|---|---|
| **Qualify honesto** | ✅ manual | deixe a tela de aposta ligada; a IA já segue o treino; veja sua posição na tabela do treino e escolha essa vaga |
| **Largada estilo GT** (largar em último e ultrapassar todo mundo) | ✅ incentivo · ⛔ forçada | escolha a última vaga na tela e faça ela pagar mais com uma curva de bônus própria (em teste) |
| **Trackday** | ✅ | [CIRCUIT_EXPERIENCE](../guides/CIRCUIT_EXPERIENCE.md) |
| **Grid multiclasse em qualquer série** | ✅ | [CUSTOM_RACE](../guides/CUSTOM_RACE.md) |
| **Qualify automático para o humano** | ⛔ | nenhuma alavanca de dados encontrada até agora |

## 3. Fechado — por favor, não repetir

- **Formato de ordenação de grid dos geradores de sessão.** O formato de qualify
  (com vaga de agrupamento dos humanos) não mudou nem a vaga do humano nem a ordem
  da IA. Os geradores Featured e multiplayer usam esse formato e não têm carros de
  IA; os da carreira usam o formato por tempo estimado e não compartilham gerador
  com o Featured. Leitura provável: o multiplayer faz qualify porque todos os carros
  são humanos e se agrupam pelo tempo, e a carreira ignora essa configuração.
- **Remover o bloco de aposta** não tira a tela; só a flag do cliente tira.
- **"A vaga fixa é a sugestão da aposta aplicada escondida"** está refutado: com a
  tela ligada, a sugestão é diferente da constante escondida.
- **O termo de tempo projetado do bloco de aposta** não mexeu na sugestão, na
  escala do bônus nem no grid da IA.
- **Flag de ordenação manual de grid**: o nome pertence ao código de lobby de
  multiplayer/freeplay; é global e não foi tocada.

## 4. Próximos passos

Uma curva de bônus própria em um cup (conferindo o crédito depois da corrida), mais
uma busca só de leitura no install por uma fonte de dados da vaga do humano e, em
seguida, a sessão de uma volta, o controle do catch-up da IA e as flags de pneu e
combustível, uma mudança por vez, cada uma revertida antes da próxima. Veja
[OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md).
