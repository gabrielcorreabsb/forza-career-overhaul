# Andamento

> 🌐 **Português** · [English](../en/PROGRESS.md)

**O que é.** A história do projeto até agora, fase por fase: o que foi construído, o
que foi testado no jogo e o que se mostrou fechado. A visão está em
[CAREER_MOD](../guides/CAREER_MOD.md) (em inglês); o mapa alavanca por alavanca em
[MOD_TOOLKIT](MOD_TOOLKIT.md); a evidência em [DISCOVERIES](../project/DISCOVERIES.md)
(em inglês). Rótulos: **verified** (mudança feita, efeito visto no jogo),
**observed** (visto com poucas corridas), **closed** (testado, não funciona).

## Linha do tempo

| fase | quando | o que mudou para o jogador | estado |
|---|---|---|---|
| **v0.1.0 e v0.2.0** | 31/10 | o pipeline: renomear, reordenar e liberar toda a carreira; séries novas a partir de um JSON; aplicação segura (lint, dry-run, backup, verificação, rollback); grids de IA (pool ou lista fixa), corridas de 23 carros de um só modelo, uma série de trackday, a auditoria da carreira vanilla | verified |
| **Baterias de teste 3–5** | início de nov | onde você larga (escolha livre ou último), treino separado da corrida, clima e hora da corrida, parada obrigatória por evento, grids pequenos (8, 12, 16 carros) | observed |
| **Fase 0.2 — prêmios** | 6–9/11 | pagamento e prêmios da carreira mapeados. Editar tabelas de pagamento, bônus ou condições de desafio muda só o que as telas mostram; **créditos e carros são concedidos pelo servidor, contra a lista de desafios dele**. O que funciona: pagamento que cresce com a duração da corrida, desbloqueio por progressão e desafios vanilla ativos que contam corridas de séries nossas | closed para prêmios próprios; observed para o resto |
| **Fase 0.3 — temporada própria** | 9–13/11 | uma cup nossa que se joga como as vanilla, pools de IA de um tema só e uma segunda cup feita sobre os desafios ativos do jogo (abaixo) | em andamento |

## Fase 0.3, descoberta por descoberta

| descoberta | o que habilita | estado | evidência |
|---|---|---|---|
| Uma série nossa com **vários eventos** roda em sequência, soma pontos por piloto e termina no último evento | temporadas feitas de séries com várias corridas | verified | D62 |
| **O jogo lê o roster da IA pelo cache**, não pelo install; a IA fica no teto da janela do roster | grids de IA refeitos com a ferramenta normal de aplicação, sem editar o install | verified | D60, D61 |
| **A escala de PI do jogo** (C 500, B 600, A 700, S 800, R 900) não é a coluna PI do catálogo | tetos e janelas corretos | verified | D63 |
| **Um roster de IA por classe** mantém o grid na classe do jogador (só alemães, de C a S) | séries por classe com grid honesto | verified | D64 |
| **Um pool fechado de modelos escolhidos** dá um grid só desses modelos | campeonatos de uma marca, de um modelo ou temáticos | verified | D65 |
| A lista de carros da própria série **não filtra** o documento do roster | o roster tem de ser escrito no próprio documento | closed | D66 |
| **Um documento de roster vanilla com cópia idêntica pode ser liberado** (aponta-se o evento para a cópia) e reaproveitado como pool nosso | pools próprios em escala: 313 documentos liberáveis | verified | D67 |
| **Pools próprios de IA funcionam em todos os tamanhos testados**: 4, 12 (só americanos), 21 (só italianos) e 37 modelos (só anos 2010) encheram o grid inteiro com o tema, depois de liberar mais 8 documentos vanilla de uma vez, com o hub e o online intactos | campeonatos temáticos por país, marca ou década | verified | D68 |
| **Nossas séries contam nos desafios do próprio jogo e o prêmio real chega**: voltas, pista e carro contam 1 para 1; dez corridas em um Mustang deram o Mustang; uma vitória em Suzuka com um Nissan liberou o Nissan; dez voltas em Daytona com uma Ferrari deram uma Ferrari 488 GTB. O progresso fica no servidor: ao reabrir o jogo a tela mostra 0% até a primeira corrida da sessão | uma série pode ser feita para servir um desafio ativo | verified | D69 |
| **Um desafio de pontuação de segmento conta só pela pista e paga um carro**: o desafio ativo "pontuação de segmento 8 ou mais em Daytona Sports Car" completou ao terminar uma série nossa nessa pista e entregou um Porsche 911 RSR; é o único desafio de segmento ainda ativo | uma série pode servir a mais de um desafio ativo | verified | D71 |
| Um documento de roster de 46 vagas ainda mostrou **24 pilotos** | grids acima de 24 seguem fechados por enquanto | observed | D70 |
| **Primeira temporada, "Ovais Alemães"** (6 séries em 3 grupos, numa cup própria): a cup aparece, o grupo 2 fica trancado até o 1 terminar, a IA só alemã fica na classe do jogador | a primeira temporada jogável | primeiro grupo jogado; grupos 2–3 ainda não | — |
| **Segunda temporada, "Turnê dos Desafios"** (uma cup de cinco grupos, um por desafio ativo, cada um com a sua lista de carros e IA de um tema só): aplicada no jogo, a cup aparece; os grupos de Suzuka e Daytona foram jogados de ponta a ponta (IA toda japonesa e toda Ferrari; a vitória e as voltas contaram; chegaram o Nissan, uma Ferrari 488 GTB e um Porsche 911 RSR) | uma temporada que segue os desafios mensais do jogo | dois grupos jogados; três a jogar (exigem carros que o jogador ainda não tem) | D69, D71 |

## O que vem

Rótulos: **viable** (o mecanismo é conhecido), **to test** (plausível, pede uma corrida controlada no jogo), **not possible**
(decidido pelo jogo ou pelo servidor, não pelos dados de conteúdo).

| item | por quê | estado |
|---|---|---|
| **Pools de IA próprios em escala** | um roster por série sobre os documentos liberáveis (marca, década, país) | viable |
| **Trilha de entrada em E e D** | 209 de 711 carros não estão em nenhum evento; E (31 de 50 usados) e D (50 de 106) são as classes pior servidas; séries curtas para eles, com uma faixa de IA que mantém o grid na classe | viable |
| **Matriz carro × evento** | uma lista que põe todo carro em ao menos um evento transforma o catálogo em carreira; limites numéricos (ano, potência) não foram testados | viable, em parte to test |
| **Lista permanente de eventos** | o conteúdo com prazo (Featured) não tem casa permanente; reaparentar uma série com ids novos está provado, sintetizar as listas é a parte aberta | viable |
| **Formato de corrida** | desgaste e combustível, clima e hora passando durante a corrida, as flags de comportamento da IA contra as da série | to test |
| **Composto de pneu da carreira** | listas por modo nas flags do cliente definem o pneu padrão dos modos online, não o da carreira; acrescentar um item de carreira é uma entrada | to test |
| **Grids acima de 24 carros** | sem precedente: todo documento vanilla pede 23 IA + o jogador ([OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md) 8) | to test |
| **Arte própria por série** | pôsteres e banners vêm da série doadora; o formato foi lido, a escrita não foi testada | to test |
| **Outros idiomas** | textos novos vão só para a tabela pt-BR; os outros 19 idiomas não têm chaves | depois |

**Not possible, não repetir:** Qualifying real (D33), prêmios próprios e edição de pagamento no cache ou nos arquivos do
install (o servidor concede), afinidade com fabricante (valor do servidor; o substituto é a série de uma só marca), física,
economia da conta e chaves globais de IA que também atingem o multiplayer.

## Como ajudar

- **Rode o pipeline numa cópia** e relate o que quebra: [GETTING_STARTED](GETTING_STARTED.md) leva cerca de 15 minutos e nunca toca o jogo.
- **Construa uma série** a partir de um spec e abra uma issue com o spec: uma década, um país, um grid de uma só marca, uma trilha de entrada.
- **Resolva uma pergunta em aberto**: cada item de [OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md) nomeia o experimento que decide.
- **Melhore um guia** com um sintoma que você viu e a causa: [TROUBLESHOOTING](../guides/TROUBLESHOOTING.md).

## Lendo a evidência

Achados marcados *observed* dependem de uma ou duas corridas. Se o seu resultado
diferir, abra uma issue com os números (veja o README, seção "Contributing").
Histórico de versões: [CHANGELOG](../../CHANGELOG.md).
