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
| árvore cup → ladder → série → evento: ordem, nomes, arte (arte existente ou pôster nosso por série) | ✅ | verified | [tutorial 02](../tutorials/02_reorder.md), [03](../tutorials/03_new_series.md) |
| séries novas, com ids próprios | ✅ | verified | `build_series.py` |
| nomes de cups, ladders, séries e eventos (chaves de texto novas, de qualquer tamanho) | ✅ | verified | `str_edit.py`, [tutorial 01](../tutorials/01_rename.md) |
| **descrições** de série, ladder e cup (chaves de texto novas) | ⛔ | observed | D92: nenhuma tela da carreira as desenha, nem as vanilla; o nome é o único texto visível |
| limite de treino da cup, rótulo da ladder e lista de conclusão da ladder | ⛔ | observed | D91: nada muda na tela (o treino é contado em voltas; a leitura da conclusão não foi provada) |
| tela de escolha do primeiro carro | 🧪 | hypothesis | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| série de exibição de prêmio (um tipo de série para dirigir um carro de prêmio): **exige o carro do prêmio na garagem** para entrar; não entrega o carro | ⛔ | verified | — |

### Prêmios e progressão
| alavanca | status | evidência | ferramenta / guia |
|---|---|---|---|
| abrir uma série (nossa ou vanilla) só depois de concluir outra série ou um grupo inteiro | ✅ | verified | critérios de entrada da série ([CAREER_BASICS](../guides/CAREER_BASICS.md)) |
| **texto do bloqueio** de uma série trancada por outra série, por uma ladder ou por um evento: o nosso texto aparece no cartão da série (mantenha em ~2 linhas / ~120 caracteres para o cabeçalho não crescer sobre a arte; 249 caracteres quebram e invadem a arte); nunca deixe vazio (mostra marcador de texto ausente); bloqueios por nível de piloto ignoram o campo (D93); nunca prometa vitória, pois qualquer posição final desbloqueia (D123) | ✅ | observed | D93, D94, D123 |
| **pôster próprio por série**: uma entrada nova, com nome próprio, nos arquivos de pôster do jogo (normal e alta resolução), no formato das entradas vanilla, Deflate aceito; a série a nomeia no `ImagePath`. Vários de uma vez e remoção funcionam; pôster ausente deixa o cartão sem arte, nada quebra. Banner e botão não mostraram nada | ✅ | observed | D98–D104 |
| **vídeo de introdução por série**: `IntroVideoPath` nomeia um vídeo do jogo e ele toca na entrada, sem outro campo; a seleção do primeiro carro (`FirstCarSelectEnabled` true) dá erro e volta ao menu ao confirmar, então mantenha false e a lista vazia. O campo de vídeo da ladder não mostra nada | ✅ | observed | D105, D106 |
| **vídeo de introdução próprio por série**: um arquivo Bink 2 com nome próprio no install, o registro dele no índice de arquivos do install (`hash.manifest`, cujo hash do caminho calculamos) e a série em tela cheia; sem cena, sem narração, sem mexer em vídeo vanilla. Codificar o clipe exige a ferramenta da RAD | ✅ | verified / observed | D107–D113 |
| **modificações visuais só no install**: qualidade de render, nível de detalhe dos carros, aparência das pistas, chuva no vidro e na lente, câmera e a marca d'água do modo foto, gravados no install; uma ferramenta aplica as de XML solto com dry-run, backup e restore, e as edições de zip mantêm cada entrada no seu offset (D120); voltado a máquinas high-end, testado em uma | ✅ | observed (uma máquina) | [INSTALL_VISUAL_MODS](../reference/INSTALL_VISUAL_MODS.md) |
| **arquivos novos no install**: o índice de arquivos lista cada arquivo e pasta que o jogo pode ler; um registro novo torna visível um arquivo novo (provado para vídeos) | ✅ | verified | D112, D113 |
| uma série trancada por **nível de piloto** mostra sempre a mensagem do jogo (o nível pedido e o seu); o texto do bloqueio não muda | ⛔ | observed | D93 |
| o **vídeo de introdução da própria cup** (`IntroVideoPath` da cup) não toca na primeira entrada na cup; o da série toca | ⛔ | observed | D122 |
| uma série trancada por **evento ou série exigidos** abre quando ele é concluído em qualquer posição (terminar em último abre); não há como trancar uma série atrás de uma vitória | ⛔ | observed | D123 |
| **não há como trancar uma série atrás de uma vitória**: o desbloqueio segue a série exigida terminada em qualquer posição e com qualquer pontuação (D123, D127), o `Ownership` da lista de carros é ignorado (D126) e o campo de conclusão da ladder não é lido | ⛔ | observed | D123, D126, D127 |
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
| elegibilidade de carros por lista de aceitos (≤ 23 entradas apenas; listas maiores falham ou são cortadas — 682 entradas mostraram só 98 carros ou falharam) | ✅ | verified | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| **lista aberta de carros por lista de bloqueio**: `Blocklist` (BCS) / `Blacklist` (XML) com `CarClassId: Any`, `CarDivisionId: Open` e gerador de classe aberta oferece todo carro exceto os excluídos (ex.: classe X; 635 carros com 1 excluído); `Class` e lista **se cruzam**; severidade estrita não mudou nada visível | ✅ | observed | D96 |
| limites numéricos de carro junto com uma lista de aceitos: o PI é inerte e a lista de aceitos vence | ⛔ | observed | — |
| **faixas da lista de carros** (ano, faixa de PI) com lista de bloqueio vazia e classe Any: um ano mínimo e um máximo e uma faixa de PI cortam a lista, na escala de PI do jogo (o máximo parece exclusivo, o mínimo inclusivo); o campo de preço não está na unidade do catálogo | ✅ | observed | D88 |
| **faixas de potência e peso da lista de carros** com lista de bloqueio vazia e classe Any: a faixa de potência lê em cavalos (a tela do carro mostra quilowatts) e o teto de peso lê em unidades de 100 kg (um teto de 1.200 kg é o valor 12); o preço mínimo não tem efeito | ✅ | observed | D121 |
| **voltas (1 a 67), hora e minuto de início, par de velocidade do relógio (16 e 32) e tipo de largada** por evento no override | ✅ | verified | D81 |
| um **teto de desempenho no override** como portão (300 barrou um carro da classe S; 999 deixou entrar e não alargou o grid) | ✅ | verified | D81 |
| classe aberta, teto 0 e vagas da série (`MaxPlayers`, `MaxAIPlayers`) como alavancas do grid | ⛔ | verified | D82: o documento de elenco decide |
| **clima por id de previsão** na corrida e no treino; uma previsão de uma fase pega o primeiro céu (quatro de quatro) | ✅ | verified (ids); observed (primeiro céu) | D83 |
| pular a **fase de construção**, um **portão de evento** e um **de série** (contador com lista vazia mantém a série trancada) | ✅ | verified | D84 |
| treino de 30 minutos, flag de pular volta e campos de qualificação | ⛔ | verified | D85: sem efeito; a carreira não tem qualificação |
| **minuto de início do treino** (30 e 15) no override do evento: o treino abre naquele minuto; a hora é um campo à parte (22 e 5) | ✅ | verified | D87, D90 |
| a **tabela de pontos** do evento (24 posições) decide os pontos da série pela posição de chegada (100 e 0, 10 iguais e 1 a 24 foram lidos de volta); o campo da volta-alvo não mostra efeito | ✅ | observed | D89 |
| os cinco switches de IA do bloco de treino e classificação, invertidos de uma vez | 🧪 | observed | D90: a corrida ficou igual; o treino e a classificação não foram relatados |
| **0 voltas de treino** dão uma volta e depois um treino livre de 10 minutos (o limite de tempo do evento, lido só no treino livre); 5 voltas dão 5 voltas de treino; duas paradas obrigatórias (`Pits` 2) exigem duas paradas | ✅ | observed | D95 |
| vácuo e pista dinâmica desligados | ⛔ | decidido | o jogo vanilla nunca os desliga (92 de 92 séries da carreira): ficam `true`, nunca testados desligados |
| gerador citado pelo override: muda só o tipo de largada; dois sem opções locais derrubaram a conexão e um travou o jogo | 🧪 | observed | D82, D85: só geradores definidos localmente |

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
| **liberar um documento de roster vanilla**: um evento cujo documento tem cópia idêntica pode ser apontado para a cópia (mesmo grid), e o documento liberado vira pool nosso; ~302 cópias idênticas são liberáveis em etapas | ✅ | verified | D67 |
| **um documento de IA por grade**: séries vanilla com vários eventos repetem o mesmo elenco, vagas e switches nos eventos e só sobem o piso da janela de PI evento a evento (uma rampa de dificuldade); um documento por grade (ou por degrau de rampa) basta, nunca um por evento | ✅ | verified (data) | [AI_GRIDS](../guides/AI_GRIDS.md) |
| um arquivo de roster de IA **totalmente novo** (entrada nova que o servidor não conhece) | ⛔ | observed | o jogo ficou offline ao abrir o evento; os documentos liberados acima são o caminho alternativo |
| **faixa estreita de velocidade por piloto** da IA (duas chaves globais do arquivo de estatísticas da IA, editado no install): a IA sai muito menos da pista; nenhum arquivo por pista as sobrescreve | ✅ | verified | D76, [AI_GRIDS](../guides/AI_GRIDS.md) |
| **limite de velocidade fora da pista mais alto e três chaves de recuperação** para a IA (quatro chaves globais): ela se recupera mais rápido e perde menos o controle depois de sair | ✅ | observed (quatro chaves juntas) | D77, D86 |
| **campo nivelado no teto da classe** (janela de 10 pontos de PI terminando no teto, banda 0…0, modelos escolhidos): os 23 carros da IA no mesmo PI nas classes S e A; o modelo ainda define o ritmo | ✅ | verified | D78 |
| rótulo `AIDifficulty` e `MaxAIPlayers` da série como alavancas da IA | ⛔ | verified (grid e ritmo) | D79 |
| um **arquivo novo por pista** no zip de estatísticas da IA (ajustar uma pista só) | ✅ | verified (uma pista) | D80 |
| a distância da IA ao jogador (escolhida pelo PI do jogador contra o piso de PI do documento; o teto de desempenho do evento não limita a IA) | ✅ | observed | [AI_GRIDS](../guides/AI_GRIDS.md) §5 |
| flags de comportamento do documento de roster (catch-up, slow-down…) contra as da série: qual vence | 🧪 | hypothesis | — |
| grids acima de 24 carros | 🧪 | a testar | um documento de 46 vagas ainda mostrou 24 pilotos (D70) |
| elástico (rubber banding) da IA nos geradores da carreira | já desligado | observed | [MODDING_SURFACE](../reference/MODDING_SURFACE.md) |
| **padrão da IA (grade + ajuste global + switches de corrida)**: uma grade de IA que **segue o PI do jogador** (banda `-20..0` em `300..980` para séries sem limite de classe) ou é **nivelada no teto da classe** (janela de 10 PI, banda `0..0`, verificado em S e A, D78), combinada com o ajuste global em `aistatics.zip` ([AI_STATICS](../reference/AI_STATICS.md), D76, D77, D86) e switches de corrida `EnableDifficultySlowDown` **ligado**, `EnableDifficultyCatchUp` **ligado**, `EnableDifficultyProximity` **desligado**, `EnablePosDifficultySpread` **desligado** e `EnableSlotCarRaceStart` **desligado** (switches de treino espelham a corrida) | ✅ | verified / observed | D76–D78, D86, D97 |
| os quatro switches de comportamento da IA na corrida da série, um de cada vez: **catch-up desligado** solta o fundo do grid (1:50–2:13 contra 1:37–1:40); **slow-down desligado** dá menos separação com os carros lentos; **proximity desligado** deixa a IA menos atrás de contato; **position spread desligado** não muda nada (testes anteriores tentaram catch-up + slow-down ambos desligados, D59) | ✅ | observed | D59, D97 |
| ajustes globais da IA que também atingem o multiplayer | ⛔ | — | não mexemos sem conversar |

### Sessão: treino e qualify
| alavanca | status | evidência | ferramenta / guia |
|---|---|---|---|
| voltas de treino limitadas → sessão cronometrada (**não existe sessão de qualify separada** na carreira) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.5 |
| trackday: sem treino, largada lançada, uma volta | ✅ | verified | [CAREER_MOD](../guides/CAREER_MOD.md) |
| sessão de uma volta | 🧪 | hypothesis | — |
| **treino separado da corrida**: o treino tem as próprias voltas (`NumberOfRequiredLaps`, 1 e 5 testadas; 0 dá uma volta + treino livre de 10 minutos), própria hora/minuto de início (`PracticeAndQualifying.TimeOfDayHour` / `TimeOfDayMinute`) e própria previsão de clima (`WeatherForecast`), independentes da corrida | ✅ | verified / observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.4, §2.16; D83, D87, D90, D95 |
| **escala de desgaste de pneu da série** (`TireFrictionWearScalar` nos overrides padrão da série): 6 contra 1 em 10 voltas num oval, com desgaste ligado no preset do jogador, fez o carro perder aderência no fim (o % de dano quase não mexeu, então é uma medida ruim); valores acima de 6 (testado 80) e a reação da IA não estão provados; o próprio jogo usa só 1, 3, 4 e 6 | 🧪 | observado (uma corrida de cada, por sensação) | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) |
| **velocidade do relógio da corrida**: o par `TimeOfDayTimeScale` + `TimeOfDayTimeScaleOverride` no override do evento funciona até **x144** (60 e 144 levaram uma corrida de 10 voltas no oval à noite, o 144 mais rápido; ex.: largada às 16:00 em x144 avança ~19 horas de jogo em 2 voltas de Le Mans); o padrão da série sozinho (24 a 144) não fez nada; valores acima de 144 e o par do treino não estão provados | 🧪 | observado (a olho) | D73, [RACE_SYSTEM](../reference/RACE_SYSTEM.md) |
| **corpo da previsão de clima** (tempos das fases, transições e condições de céu de uma previsão existente): editável, e **os tempos das fases são segundos reais** (ex.: fases de 60 s com transições de 15 s numa corrida de 3 minutos, ou fases de 100 s numa corrida de 300 s); uma fase de céu limpo depois de 20 s de transição secou a pista de uma vez (brusco demais: use transição maior ou uma fase intermediária) | 🧪 | observado (a olho) | D74, [RACE_SYSTEM](../reference/RACE_SYSTEM.md) |
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
- **Nível do carro, pontos de carro (CP) e preço do CP (sete testes, novembro de 2026):** a curva de nível no cache é lida pelo cliente (um carro
  passou de um limite editado e mostrou o nível seguinte), mas o CP que a conta recebe, o CP pago por nível e o preço de uma compra de CP não
  mudaram; um preço editado fez a compra falhar. O serviço online guarda o saldo de cada carro; o cache só alimenta as telas.
- **Um servidor próprio (uma carreira sem o serviço online) não é possível, e este projeto não oferece suporte a isso.** O jogo confere uma
  assinatura em toda resposta do serviço online, e um substituto não consegue produzi-la; não existe modo offline para recorrer. Vale o mesmo
  para falsificar as respostas do serviço real. A única edição que o cliente aceita é a que este projeto faz: mudanças no conteúdo que ele baixa e
  guarda em cache. Não documentamos, não testamos nem ajudamos a redirecionar o tráfego do jogo. Quem tentar mesmo assim faz isso **por sua conta e
  risco**: pode quebrar o jogo, fazer a conta ser sinalizada ou banida, e pode violar os termos de uso do jogo.
- **Um campo numa série de bancada, sem efeito nos créditos pagos:** o modificador de pagamento e o preset de overrides do gerador, e a
  dificuldade de IA da série. A escolha de dificuldade do próprio jogador pode mascarar a última (hipótese).
- **Flag de ordenação manual de grid**: o nome pertence ao código de lobby de
  multiplayer/freeplay; é global e não foi tocada.
- **Aplicar edições com o jogo aberto ("carreira ao vivo") está refutado (verified, novembro de 2026).** Trocar blobs do CmsCache enquanto o jogo roda falha logo no primeiro arquivo com `WinError 5` (acesso negado) porque o jogo aberto mantém travas nos arquivos do cache. O jogo precisa estar sempre fechado antes de qualquer escrita. Variedade dinâmica vem de pools de IA maiores que 23 vagas, previsões de clima com múltiplas condições, travas de progressão e aplicação antes de abrir o jogo.

## 4. Próximos passos

O mapeamento da carreira está fechado: cada camada, precedente e limite duro acima está mapeado. O projeto agora constrói temporadas da FCO a partir de um **perfil-base** documentado ([CAREER_MOD](../guides/CAREER_MOD.md)), começando pela Intro Series dentro de uma cup da FCO ao lado da Builders Cup vanilla. As recompensas vêm do que o jogo já paga (tamanho da corrida, bônus de colocação, desafios vanilla ativos) e de desbloqueios por progressão ([ECONOMY_MAP](../reference/ECONOMY_MAP.md)). Hipóteses em aberto seguem em [OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md).
