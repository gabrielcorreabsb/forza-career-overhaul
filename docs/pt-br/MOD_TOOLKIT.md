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
| tela de escolha do primeiro carro | 🧪 | hypothesis | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| série de exibição de prêmio (um tipo de série para dirigir um carro de prêmio): **exige o carro do prêmio na garagem** para entrar; não entrega o carro | ⛔ | verified | — |

### Prêmios e progressão
| alavanca | status | evidência | ferramenta / guia |
|---|---|---|---|
| abrir uma série (nossa ou vanilla) só depois de concluir outra série ou um grupo inteiro | ✅ | verified | critérios de entrada da série ([CAREER_BASICS](../guides/CAREER_BASICS.md)) |
| uma **série com vários eventos** (2 a 8 no jogo vanilla): os eventos rodam em sequência, os pontos da série somam por piloto, a série termina no último evento e cada corrida paga o mesmo | ✅ | verified | a lista de eventos da série ([CAREER_BASICS](../guides/CAREER_BASICS.md)), [DISCOVERIES](../project/DISCOVERIES.md) |
| pagamento que cresce com o tamanho da corrida (voltas, distância) | ✅ | observed | [ECONOMY_MAP](../reference/ECONOMY_MAP.md) |
| bônus de colocação ao concluir uma série (troféu mais créditos pela posição final), (nos dados do jogo vale para toda série; **não pagou** ao vencer uma série nova nossa, até agora) | 🧪 | hypothesis | em aberto |
| corridas nas nossas séries contam para os desafios vanilla ativos do Centro de Desafios (um mensal "5 corridas em carro dos anos 2020" pagou 75.000 créditos) | ✅ | verified | escolher carros e pistas que batam com os desafios ativos: voltas, pista e carro contam 1 para 1, o progresso fica no servidor (a tela mostra 0% ao reabrir até a primeira corrida) e concluir paga o prêmio real (D69); um desafio que cita só a pista conta só pela pista (D71) |
| prêmio próprio: editar a condição, o prêmio ou o objetivo por série de um desafio | ⛔ | observed | a linha mostra **concluído**, mas nada é pago; quem entrega o prêmio é o servidor, pela lista de desafios dele |

### Evento
| alavanca | status | evidência | ferramenta / guia |
|---|---|---|---|
| pista e número de voltas por evento (vale o override do evento) | ✅ | verified | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| teto de desempenho por evento (vale o valor do evento, não o do override) | ✅ | verified | [DISCOVERIES](../project/DISCOVERIES.md) |
| os tetos usam a escala de PI **do jogo** (C 500, B 600, A 700, S 800, R 900); a coluna PI do catálogo não é essa escala | ✅ | verified | [CARS_AND_PI](../reference/CARS_AND_PI.md) §3.1 |
| elegibilidade de carros por lista de aceitos | ✅ | verified | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| limites numéricos de carro: o PI é inerte e a lista de aceitos vence (ano, potência e peso sem teste) | ⛔ | observed | — |

### Roster e comportamento da IA
| alavanca | status | evidência | ferramenta / guia |
|---|---|---|---|
| roster que acompanha o PI do jogador, ou lista fixa multiclasse | ✅ | verified | [AI_GRIDS](../guides/AI_GRIDS.md), [tutorial 04](../tutorials/04_ai_grid.md) |
| pool maior que o grid (campo diferente a cada corrida) e faixas largas de PI | ✅ | verified | [AI_GRIDS](../guides/AI_GRIDS.md) |
| **roster próprio** num documento de roster existente e sem uso (por exemplo 23 carros de um só modelo); um roster por documento, compartilhado por todo evento que aponte para ele | ✅ | verified | [AI_GRIDS](../guides/AI_GRIDS.md) §6 |
| **roster próprio pelo cache**: o documento de roster é reescrito com `cache_edit.py` e o jogo lê a cópia do cache; por classe, por marca, ou um pool com todos os carros de uma marca | ✅ | verified | [AI_GRIDS](../guides/AI_GRIDS.md) §1, §6c |
| o PI da IA fica preso ao teto da janela do roster quando o carro do jogador está acima; uma série de classe precisa de janela com teto igual ao teto da classe | ✅ | observed | [AI_GRIDS](../guides/AI_GRIDS.md) §5 |
| um **pool fechado de modelos escolhidos** no documento de roster dá um grid só desses modelos, bem distribuído (5 modelos de classe A, 23 vagas, PI 658–677) | ✅ | verified | [DISCOVERIES](../project/DISCOVERIES.md) D65 |
| a lista de carros da própria série como **filtro** do documento de roster | ⛔ | verified | D66: a lista não filtra; escreva o pool no documento |
| **liberar um documento de roster vanilla**: um evento cujo documento tem cópia idêntica pode ser apontado para a cópia (mesmo grid), e o documento liberado vira pool nosso; 313 são liberáveis | ✅ | verified | D67 |
| um arquivo de roster de IA **totalmente novo** (entrada nova que o servidor não conhece) | ⛔ | observed | o jogo ficou offline ao abrir o evento; os documentos liberados acima são o caminho alternativo |
| a distância da IA ao jogador (escolhida pelo PI do jogador contra o piso de PI do documento; o teto de desempenho do evento não limita a IA) | ✅ | observed | [AI_GRIDS](../guides/AI_GRIDS.md) §5 |
| flags de comportamento do documento de roster (catch-up, slow-down…) contra as da série: qual vence | 🧪 | hypothesis | — |
| grids acima de 24 carros | 🧪 | a testar | um documento de 46 vagas ainda mostrou 24 pilotos (D70) |
| elástico (rubber banding) da IA nos geradores da carreira | já desligado | observed | [MODDING_SURFACE](../reference/MODDING_SURFACE.md) |
| catch-up e slow-down da IA desligados na corrida: a IA ficou melhor, e os dois desligados são o padrão da carreira (relato do jogador, sem medição de voltas) | ✅ | observed | [DISCOVERIES](../project/DISCOVERIES.md) D59 |
| ajustes globais da IA que também atingem o multiplayer | ⛔ | — | não mexemos sem conversar |

### Sessão: treino e qualify
| alavanca | status | evidência | ferramenta / guia |
|---|---|---|---|
| voltas de treino limitadas → sessão cronometrada (**não existe sessão de qualify separada** na carreira) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.5 |
| trackday: sem treino, largada lançada, uma volta | ✅ | verified | [CAREER_MOD](../guides/CAREER_MOD.md) |
| sessão de uma volta | 🧪 | hypothesis | — |
| **voltas de treino por evento**: o `NumberOfRequiredLaps` do evento as define, separado das voltas da corrida (1 e 5 voltas de treino testadas com corrida de 2; 0 deixa sem voltas contadas e ainda deixa correr) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.4 |
| clima e hora no override do evento valem **só na corrida**; o treino mantém o próprio bloco (chuva pesada e largada à noite testadas); apontar para outro forecast funciona, editar o conteúdo de um forecast segue sem prova | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.16 |
| **escala de desgaste de pneu da série** (`TireFrictionWearScalar` nos overrides padrão da série): 6 contra 1 em 10 voltas num oval, com desgaste ligado no preset do jogador, fez o carro perder aderência no fim (o % de dano quase não mexeu, então é uma medida ruim); valores acima de 6 (testado 80) e a reação da IA não estão provados; o próprio jogo usa só 1, 3, 4 e 6 | 🧪 | observado (uma corrida de cada, por sensação) | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) |
| **velocidade do relógio da corrida**: o par `TimeOfDayTimeScale` + `TimeOfDayTimeScaleOverride` no override do evento funciona (60 e 144 levaram uma corrida de 10 voltas no oval à noite, o 144 mais rápido); o padrão da série sozinho (24 a 144) não fez nada; valores acima de 144 e o par do treino não estão provados | 🧪 | observado (a olho) | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) |
| **corpo da previsão de clima** (tempos das fases, transições e condições de céu de uma previsão existente): editável; uma chuva de 3 fases reajustada para 100 s por fase seguiu a edição numa corrida de 300 s, e uma fase de céu limpo depois de 20 s de transição secou a pista de uma vez (brusco demais: use transição maior ou uma fase intermediária); o tempo da previsão original não está claro (a primeira chuva veio por volta de 180 s com fases de 360 s) | 🧪 | observado (a olho) | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) |
| pit obrigatório: `Pits` 1 exige a parada; `Pits` 0 só a remove se o `NumQuickStops` do gerador também for 0 (um gerador com 1 ainda obrigou a parada) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.6 |
| "sem treino" zerando o orçamento de treino | ⛔ | observed | só o Trackday reproduz; duas outras séries mantiveram o treino |
| tipo de largada (parada ou lançada): definido pelo gerador de sessão, **não** pela flag de largada lançada da série; um valor no override do evento vence, então é escolha por evento (um par testado) | ✅ | verified | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.8 |
| pneu padrão, escala de combustível e desgaste de pneu da carreira | 🧪 | hypothesis | — |

### Grid e posição de largada
| alavanca | status | evidência |
|---|---|---|
| o grid da **IA** segue a classificação do treino | ✅ | observed |
| a vaga do **humano** é a escolhida na tela de aposta de posição, quando ela está ligada | ✅ | verified |
| ligar ou desligar a tela de aposta (uma flag do cliente) | ✅ | verified |
| **onde o humano larga é decidido pelo formato de grid do gerador de sessão** (a vaga escolhida na tela só vale quando o gerador não impõe nenhuma) | ✅ | observed | [ADR-006](../project/decisions/ADR-006_grid_start_shapes.md) |
| ordem por tempo estimado, sem índice de largada: a **vaga escolhida é obedecida** (escolheu 12ª, largou em 12º) | ✅ | observed | largada livre |
| ordem por rank com índice 0 a 5: **primeiro**; índice 6 ou mais: **último** (24º de 24, 8º de 8); sem vaga intermediária, e a escolha não é obedecida | ✅ | observed | largada estilo GT |
| ordem de qualify: um **valor no meio do grid que varia** com o campo, o documento de IA e o carro (3º de 8, 5º de 12 e 16, 7º de 24); a escolha não é obedecida | ⛔ | observed | documentado, não usado |
| a vaga que a tela sugere | ⛔ constante | não acompanha o tempo de treino do jogador, a tabela de aposta nem o termo de tempo projetado |
| quantas vagas a tela lista | ⛔ não é dado | o cache não muda isso |
| o **bônus pago por vaga** (tabela de aposta do cup) | ⛔ | até agora só a interface muda: uma tabela em 10,0 em todas as vagas não mudou nada nos créditos pagos no fim da corrida (observed) |

A tabela de bônus pertence a um **cup**, mas só muda o que a tela mostra, não os créditos pagos. A célula de pagamento base de uma pista e classe de carro se comporta do mesmo jeito (veja [ECONOMY_MAP](../reference/ECONOMY_MAP.md)).

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
| **Largada estilo GT** (largar em último e ultrapassar todo mundo) | ✅ forçada (observed, várias séries) | um gerador de sessão em ordem por rank com índice de largada 23 põe o jogador em **último** seja qual for a volta de treino, em grids de 8 e de 24 carros; o projeto fixa esse formato ([ADR-006](../project/decisions/ADR-006_grid_start_shapes.md)) |
| **Largada livre** (escolher a sua vaga) | ✅ | um gerador com ordem por tempo estimado e sem índice de largada; a escolha da tela é obedecida |
| **Treino curto** (1 a 5 voltas) | ✅ | defina o `NumberOfRequiredLaps` do evento, separado das voltas da corrida |
| **Trackday** | ✅ | [CAREER_MOD](../guides/CAREER_MOD.md) |
| **Grid multiclasse em qualquer série** | ✅ | [AI_GRIDS](../guides/AI_GRIDS.md) |
| **Qualify automático para o humano** | ⛔ | nenhuma alavanca de dados encontrada até agora |

## 3. Fechado — por favor, não repetir

- **"O formato de grid do gerador não mexe no humano"** foi uma leitura inicial e hoje está errada: testes posteriores mostraram que o
  formato por rank com o seu índice e o formato de qualify decidem onde o humano larga (veja a tabela de grid). Os geradores Featured e
  multiplayer continuam usando o formato de qualify, e os da carreira o de tempo estimado.
- **Remover o bloco de aposta** não tira a tela; só a flag do cliente tira.
- **"A vaga fixa é a sugestão da aposta aplicada escondida"** está refutado: com a
  tela ligada, a sugestão é diferente da constante escondida.
- **O termo de tempo projetado do bloco de aposta** não mexeu na sugestão, na
  escala do bônus nem no grid da IA.
- **Campos de série e de evento testados para um Qualifying de verdade ou outra IA**,
  todos sem efeito na carreira: um roster de IA com janela de PI maior para o evento
  (a IA continuou limitada a cerca de classe D), um tamanho de campo menor na série (o
  grid continuou com 24), uma referência de regras no nível da série (o Featured tem,
  a carreira ignora) e o tipo de limite de treino `Disabled` (o treino continuou
  limitado). O cliente tem uma atividade de Qualification própria, mas nenhum campo da
  carreira que alcançamos a seleciona.
- **O regulamento 103 num gerador da carreira** não teve efeito visível: sem fantasma, sem penalidade de saída de pista nem de
  contramão; a colisão já era punida sem regulamento.
- **A duração do treino pela série ou pelo gerador** (limites de 1, 3 e 6 voltas testados) não mudou o treino; as voltas exigidas do
  evento mudam.
- **A vaga sugerida** também não acompanhou uma volta cerca de seis segundos à frente
  do grid nem a classe do carro.
- **Prêmio próprio por desafio (quatro testes):** ligar os objetivos por série, apontar um desafio para uma série nossa, trocar a condição
  de um desafio (voltas, pista, divisão de carro) e abrir uma exibição de prêmio. O cliente lê as condições editadas e marca a linha como
  concluída, mas nenhum carro ou crédito chega e a conclusão pode sumir ao reabrir o jogo. Só os desafios ativos, sem edição, pagam, e esses mantêm o progresso ao reabrir.
- **Um campo numa série de bancada, sem efeito nos créditos pagos:** o modificador de pagamento e o preset de overrides do gerador, e a
  dificuldade de IA da série. A escolha de dificuldade do próprio jogador pode mascarar a última (hipótese).
- **Flag de ordenação manual de grid**: o nome pertence ao código de lobby de
  multiplayer/freeplay; é global e não foi tocada.

## 4. Próximos passos

Prêmios respondidos: a carreira recompensa o jogador com o que o jogo já paga (tamanho da corrida, bônus de colocação, desafios vanilla
ativos) e com desbloqueio por progressão; prêmio próprio está fechado (veja [ECONOMY_MAP](../reference/ECONOMY_MAP.md)). Em seguida vem uma
primeira série jogável e depois uma temporada, montadas com as alavancas acima. Uma mudança por vez, cada uma revertida antes da próxima. Veja [OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md).
