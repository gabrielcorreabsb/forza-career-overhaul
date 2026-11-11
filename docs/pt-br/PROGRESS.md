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
| **v0.1.0** | out/2026 | o pipeline: renomear, reordenar e liberar toda a carreira; séries novas a partir de um JSON; aplicação segura (lint, dry-run, backup, verificação, rollback) | verified |
| **v0.2.0** | 31/10 | grids de IA (pool ou lista fixa), corridas de 23 carros de um só modelo, uma série de trackday, a auditoria da carreira vanilla | verified |
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

- **Pools de IA próprios em escala**: um roster por série sobre os documentos liberáveis (marca, década, país).
- **Formato de corrida**: desgaste e combustível, clima e hora passando durante a corrida, as flags de comportamento da IA contra as da série.
- **Grids acima de 24 carros**: sem precedente ainda ([OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md)).
- **Arte própria por série** (pôsteres e banners): o formato foi lido, a escrita não foi testada.
- **Fechado, não repetir**: Qualifying real, prêmios próprios, edição de pagamento no cache ou nos arquivos do install.

## Lendo a evidência

Achados marcados *observed* dependem de uma ou duas corridas. Se o seu resultado
diferir, abra uma issue com os números (veja o README, seção "Contributing").
Histórico de versões: [CHANGELOG](../../CHANGELOG.md).
