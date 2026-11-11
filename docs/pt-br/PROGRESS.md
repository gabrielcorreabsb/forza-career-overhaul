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
| **Fase 0.3 — temporada própria** | 9–11/11 | uma cup nossa que se joga como as vanilla (abaixo) | em andamento |

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
| **Primeira temporada, "Ovais Alemães"** (6 séries em 3 grupos, numa cup própria): a cup aparece, o grupo 2 fica trancado até o 1 terminar, a IA só alemã fica na classe do jogador | a primeira temporada jogável | primeiro grupo jogado; grupos 2–3 ainda não | — |

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
