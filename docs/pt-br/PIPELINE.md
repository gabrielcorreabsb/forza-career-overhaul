# PIPELINE — como aplicar um mod de carreira no FM8

> 🌐 **Português** · [English](../en/PIPELINE.md) — primeira vez? Comece por [COMECE_AQUI / GETTING_STARTED](GETTING_STARTED.md).

Uma página, do plano ao cache verificado. Formatos e modelo de dados ficam no
[CONCEITOS](CONCEPTS.md); aqui só o passo a passo operacional.

## Regras de ouro

1. **Feche o jogo antes de escrever.** Ele trava os blobs do CmsCache; escrever
   com o jogo aberto dá `WinError 5` e deixa o cache inconsistente.
2. **A fonte runtime é o CmsCache**, não o install:
   `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\`. O `install`
   (`media/pcfamily/cms/`) é só semente e não precisa ser modificado.
3. **Todo write faz backup automático** (`_backup\cache_<timestamp>`, ~13 MB).
   Rollback: `python _tools\rollback_cache.py`.
4. **Não espelhe `mediapc/`.** O jogo não lê `mediapc/`; a única fonte é o
   CmsCache (regra 2).
5. **Nunca commitar** a chave AES do CMS, o Forza Mod Tool ou arquivos do jogo.
   O repo é público; o `.gitignore` e o `docs/project/THIRD_PARTY.md` dizem o que fica
   só local.

## Pré-requisitos

Python 3, o .NET 10 SDK e os oráculos compilados. Os oráculos também dependem do
runtime e das tabelas do Forza-Mod-Tool v1.3.0, que você mantém localmente (fora
do repo): veja [THIRD_PARTY](../project/THIRD_PARTY.md).

```powershell
dotnet build _tools\cmsoracle\cmsoracle.csproj -c Release
dotnet build _tools\cacheoracle\cacheoracle.csproj -c Release
```

## Peças

| peça | o quê | observações |
|---|---|---|
| `prod\<snapshot>` | manifesto plaintext da snapshot (10.434 arquivos, 8 grupos) | `Size` = tam. do payload **cifrado**; `Checksum` = SHA-256(base64) do payload cifrado |
| blob `<bucket>\<SHA256HEX>` | ZIP deflate com as entradas cifradas | endereçado por conteúdo: o nome original = sha256 do conteúdo. Mantemos o nome e só atualizamos `Size`/`Checksum` no manifesto (Strategy S) |
| `cache-manifest.json` | índice snapshot→blob (10 entradas), **criptografado** (asset container) | re-criptar com o original como template: `cacheoracle.exe enc <plain> <template> <out>` |
| `Id` (int64) no manifesto | opaco (não é hash do Path — testado fnv/murmur/crc/md5/sha) | nunca recalcular; só manter |
| CMS payload | `AES-128-CBC(IV=0×16)` sobre `gzip` | cifra via oráculo: `cmsoracle.exe enc <plain> <template_cifrado> <out>` (template = payload atual); fallback Python `cms_crypto.py` |

## O ciclo

```powershell
# 1. gerar o kit (série nova: spec + build_series; o resto: gerador sobre _tools/fmlib)
python _tools\build_series.py --spec specs\<serie>.json   # grava patches\<kit>\
# 2. lint + simular
python _tools\plan_lint.py --plan patches\<kit>\plan.json
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json
# 3. aplicar + verificar (JOGO FECHADO)
python _tools\cache_edit.py --plan patches\<kit>\plan.json --verify
# 4. atualizar inventário/estado e commitar (ledger + _data + docs/inventario)
python _tools\inventory.py
# 5. reverter se precisar
python _tools\rollback_cache.py
```

O plano é uma lista de alvos; o exemplo comentado é
`_tools\cache_edit_plan_example.json` (quatro alvos num kit: dois `json` em
`BuildersCupScheduleDataV4.json` e dois `bytes` no `LocStrings_pt-BR.str` já
editado, um por snapshot).

## Travas no código

O apply **recusa** rodar quando:

- o jogo está aberto (qualquer processo `forza*`);
- não há `--dry-run` sem erros nos últimos 30 min para o mesmo plano, payloads e
  estado do cache;
- o `plan_lint.py` reprova o plano (checagens estáticas, campeonato 1 intocado,
  Strategy S/Checksum, ids aposentados).

O `cache_edit.py` resolve snapshot→blob **pelo Checksum das entradas no
manifesto**, nunca por nome ou mtime. Lint avulso:
`python _tools\plan_lint.py --plan <plan.json>`.

## Textos (`.str`)

`_tools\str_edit.py` — parse/rewrite com round-trip byte-idêntico. Chaves novas
são livres (`IDS_<md5("MC44|<rótulo>")>`, ver `fmlib.strs.key_for`; colisão
verificada) e de **qualquer tamanho** — o jogo resolve a chave por hash do nome.
Hoje só `LocStrings_pt-BR.str` recebe as chaves novas; os outros 19 idiomas ficam
sem elas (pendência).

## Carreira (`BuildersCupScheduleDataV4.json`)

- Reordenar = permutar `cup.LadderOrderData` e `ladder.OrderData` (listas de
  IDs). Sem IDs novos, sem risco de save.
- Destravar = zerar `RequiredLadders/RequiredSeries/RequiredEvents` (+
  contadores) em cada série.
- Re-serializar com `json.dump(obj, ensure_ascii=False, separators=(",",":"))`
  reproduz o original **byte-idêntico** (validado nos 1.197.441 B).

## Publicando um kit (`patches/<nome>/`)

Um kit tem `plan.json`, os payloads `.enc` e uma NOTA que diz o escopo e como
reaplicar. Só vale para CmsCache com as **mesmas snapshots**; se o servidor
baixar snapshot nova, regenerar o kit.

## Série nova, trackday e grid de IA

Nada disso muda o ciclo acima (plano → `--dry-run` → apply com `--verify`);
muda só o que vai dentro do plano.

- **Série nova:** caminho padrão = spec + `build_series.py` (`specs/README.md`);
  passo a passo no [tutorial 03](../tutorials/03_new_series.md). A receita e os
  porquês estão no [SERIES_CHECKLIST](../reference/SERIES_CHECKLIST.md): ids novos
  (`ChampionshipSeriesId` ≥ 20000, `EventDataId` 65897900–65899999, nunca
  reusar), série + `OrderData` do ladder, eventos + `BCEventOverrides`, entrada
  em `BCSeriesSelectableCars.xml` (sem ela o clique crasha) e chave `IDS_` nova
  no `.str`.
- **Trackday:** série custom cujo evento é uma volta de um circuito longo, sem
  treino (`OpenPracticeLimitationTimeInSeconds = 0`).
- **Grid de IA:** a IA não vem só do BCS. O campo é fixado por
  `AIField_<n>_Gen.xml`, nomeado por evento pelo `AIFileName` do override, que
  **não existe no CmsCache** (só no zip do install). Conteúdo desse tipo de
  grupo **não** é aplicado pelo `cache_edit.py`: use
  `python _tools\install_edit.py --logical <arquivo> --payload <.enc>`
  (`--dry-run` antes, jogo fechado, `--verify`; backup em
  `_backup\install_<ts>`, desfaz com `--restore`). Ele reescreve o zip, o
  manifesto do install e as 2 snapshots de `prod\` + `cache-manifest.json`
  juntos — e, ao contrário do `cache_edit.py`, não tem sandbox
  (`--cache-dir`): um apply real toca o install real. Ver
  [AI_GRIDS](../guides/AI_GRIDS.md) e
  [CUSTOM_RACE](../guides/CUSTOM_RACE.md).

Sintomas e causas já vistas: [TROUBLESHOOTING](../guides/TROUBLESHOOTING.md).

## Verificação pós-escrita

`python _tools\cache_verify.py` confere `Size`/`Checksum` de todos os arquivos,
consistência blob↔manifesto e divergências por snapshot. Todo apply termina com
`verificacao: OK` e `0 divergentes`; qualquer outra coisa significa restaurar
(`rollback_cache.py`) em vez de jogar.
