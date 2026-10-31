# Comece aqui

> 🌐 **Português** · [English](../en/GETTING_STARTED.md)

Objetivo: em uns 15 minutos, ver o pipeline inteiro funcionando numa **cópia**
do cache, sem tocar no jogo. Depois leia [CONCEITOS](CONCEPTS.md) e
[PIPELINE](PIPELINE.md).

Cada passo abaixo diz o que você deve ver. As citações são a saída real das
ferramentas deste repositório; `<...>` marca os valores que dependem da sua
máquina.

## 1. Requisitos

- Windows e Forza Motorsport (2023) na Steam, aberto pelo menos uma vez. Isso
  cria o CmsCache em `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\`.
- Python 3.10+.
- O **.NET 10 SDK**: os dois projetos de oráculo apontam para `net10.0`, então um
  SDK mais velho falha na compilação. `dotnet --version` precisa imprimir `10.`.
- O [Forza Mod Tool](https://github.com/HTTPJXRDN/Forza-Mod-Tool) v1.3.0 e a
  chave do CMS. Eles **não** estão neste repositório: você baixa a ferramenta e
  coloca ela e a chave nos caminhos ignorados pelo git indicados em
  [THIRD_PARTY](../THIRD_PARTY.md) (aquela página também explica por que nada
  dela é distribuído aqui).
- Terminal PowerShell na raiz do repo.

## 2. Preparação (uma vez)

```powershell
dotnet build _tools\cmsoracle\cmsoracle.csproj -c Release
dotnet build _tools\cacheoracle\cacheoracle.csproj -c Release
git config core.hooksPath .githooks          # travas de pre-commit
```

O que você deve ver: dois blocos `Build succeeded` terminando em
`... -> _tools\cmsoracle\bin\Release\net10.0\cmsoracle.exe` e o mesmo para o
`cacheoracle.exe`. Se o build parar numa referência ausente, os arquivos de
terceiros do [THIRD_PARTY](../THIRD_PARTY.md) ainda não estão no lugar — o
oráculo do cache não compila sem eles.

**Onde está o jogo.** As ferramentas procuram o install em
`F:\SteamLibrary\steamapps\common\Forza Motorsport` por padrão (a variável de
ambiente `FM_INSTALL`, lida pelo `_tools\install_edit.py`). Se o seu fica em
outro lugar, defina para a sessão:

```powershell
$env:FM_INSTALL = "D:\Steam\steamapps\common\Forza Motorsport"
# ou grave para os próximos terminais:
[Environment]::SetEnvironmentVariable("FM_INSTALL", "D:\Steam\steamapps\common\Forza Motorsport", "User")
```

O caminho do CmsCache não tem variável: é sempre
`%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\`.

## 3. Copie o cache e olhe antes de mexer

```powershell
python _tools\snapshot_cache.py              # copia o cache para _work\cachetest
python _tools\inventory.py --check           # os inventários gerados estão atualizados?
```

O que você deve ver:

- a cópia imprime `copia: <CmsCache> -> <repo>\_work\cachetest (<N> B)`. Ela se
  recusa a copiar com o jogo aberto, com
  `ERRO: jogo aberto (forza_steamworks_release_final.exe); feche antes de copiar`
  — uma cópia feita com o jogo rodando pode sair inconsistente.
- o check do inventário imprime
  `live snapshot: <snapshot> (<N> entries resolved)` e depois
  `inventory up to date` ou uma lista `STALE`. "Stale" só quer dizer que seu
  cache andou (você aplicou um kit, ou o servidor baixou uma snapshot nova):
  rode `python _tools\inventory.py` para regerar os dados gerados e as páginas
  do inventário.

Depois abra a página `CARREIRA` do inventário (árvore da carreira), `PISTAS`
(pistas), `CARROS` (carros) e `ESTADO` (quais kits estão ativos no seu cache).

**Quando o jogo precisa estar fechado?** Só para escrita. Copiar o cache (acima)
e qualquer `--dry-run` são somente leitura e funcionam com o jogo aberto; a
primeira escrita de verdade tem que ser com ele fechado (passo 6).

## 4. Gere uma série de demonstração na cópia

`specs\_TEMPLATE.json` é uma spec que funciona: copie e ajuste os ids. Ela
adiciona a série **20005** e dois eventos.

```powershell
python _tools\build_series.py --spec specs\_TEMPLATE.json --cache-dir _work\cachetest --out _work\kit_demo
```

O que você deve ver: um bloco por snapshot (`series <id> -> ladder <id> |
events [...]`, `XML entry SeriesId=...`, `override ... -> <evento>`,
`.str + IDS_...`) e depois

```
plan: <repo>\_work\kit_demo\plan.json (8 targets) | 1 warning(s)
```

Exit code **3** é normal: o aviso diz que a acceptlist "showroom" tem carros
sempre vetados (o jogo os ignora). Exit code 1 com
`ERROR: series id 20005 already in use` quer dizer que esse id já está em uso no
seu cache — troque `series.id` (≥ 20000) e `events[].id` (65897900–65899999) por
ids livres; o registro de ids (`ids.json`) mostra o
que já está em uso.

## 5. Lint, dry-run e apply na cópia

```powershell
python _tools\plan_lint.py --plan _work\kit_demo\plan.json
python _tools\cache_edit.py --dry-run --plan _work\kit_demo\plan.json --cache-dir _work\cachetest
python _tools\cache_edit.py --plan _work\kit_demo\plan.json --cache-dir _work\cachetest --verify --no-backup
```

O que você deve ver, nesta ordem:

- `_work\kit_demo\plan.json: 0 erros, 0 avisos` (exit 0; exit 3 = só avisos,
  exit 1 = plano reprovado, e o apply também vai recusar).
- o dry-run termina com `lint profundo: ok (multiplayer intocado, Strategy S,
  Size/Checksum)`, a lista de alvos e um `=== RESUMO ===` com
  `alvos avaliados: N (alterados: X, ja corretos: Y, ignorados: Z)`.
  `ja corretos` significa "já está no estado desejado".
- o apply termina com `=== VERIFICACAO ===` mostrando `0 divergentes` por
  snapshot e `verificacao: OK`, e então `blobs gravados: N`.

Um dry-run real numa cópia fica assim (resumido):

```
snapshot 20260923t185113xwyk: 10434 arquivos, 8 grupos, 4 grupos no cache
  [+] LocStrings_pt-BR.str -> blob C0A94D0949D8 (...)
      payload 79920 -> 79968 B | plaintext 272894 -> 273026 B
lint profundo: ok (multiplayer intocado, Strategy S, Size/Checksum)
DRY-RUN: nenhuma escrita realizada.
marcador de dry-run gravado (valido por 30 min)
=== RESUMO ===
alvos avaliados: 2  (alterados: 2, ja corretos: 0, ignorados: 0)
  20260923t185113xwyk  LocStrings_pt-BR.str  blob=C0A94D0949D8  payload 79920->79968 B  [bytes]
blobs a gravar: 2 | snapshots a gravar: 2
```

e aplicando o mesmo plano na cópia:

```
backup: desativado (--no-backup)
blobs gravados: 2
=== VERIFICACAO ===
  prod/20260923t185113xwyk: 10434 arquivos, 8 grupos, 9153 fora do cache (base), 0 divergentes
  verificacao: OK
```

Repare nas duas frases que pertencem a camadas diferentes: `lint profundo: ok`
vem do `cache_edit.py` (lint profundo); `0 erros, 0 avisos` vem do
`plan_lint.py`. Os `9153 fora do cache (base)` são as entradas que o cache não
guarda (o install fornece); não é erro.

## 6. Para valer (jogo FECHADO)

Use o kit que você gerou (ver [PIPELINE](PIPELINE.md)) e tire o `--cache-dir`
e o `--no-backup`:

```powershell
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json
python _tools\cache_edit.py --plan patches\<kit>\plan.json --verify
```

O apply faz backup do cache inteiro em `_backup\cache_<timestamp>` e acrescenta
uma linha em `patches\ledger.jsonl`; ele recusa com processo `forza*` aberto ou
quando o último dry-run limpo daquele plano exato tem mais de 30 minutos. Para
desfazer: `python _tools\rollback_cache.py`.

## Se der errado

| sintoma | causa / correção |
|---|---|
| `nenhum --dry-run sem erros encontrado` | rode antes o `--dry-run` do mesmo plano e cache (vale 30 min) |
| `jogo aberto (ForzaMotorsport.exe)` | feche o jogo por completo (só na escrita) |
| `ERRO: jogo aberto (...)` vindo do `snapshot_cache.py` | idem: a cópia também recusa com o jogo rodando |
| `cmsoracle.exe not found` | compile os oráculos (passo 2) |
| `ERROR: series id 20005 already in use` | escolha ids livres (registro de ids: `ids.json`) |
| `WinError 5` ao escrever | jogo ou outro processo segurando os arquivos: feche e rode `rollback_cache.py` |
| `verificacao: FALHOU` | não jogue: restaure com `rollback_cache.py` e abra uma issue com o plano |
| série crasha ao clicar | falta a entrada no `BCSeriesSelectableCars.xml` (o `build_series` adiciona); ver [TROUBLESHOOTING](../TROUBLESHOOTING.md) (em inglês) |
