# PIPELINE — como aplicar um mod de carreira no FM8

> 🌐 **Português** · [English](../en/PIPELINE.md) — primeira vez? Comece por [COMECE_AQUI / GETTING_STARTED](GETTING_STARTED.md).

Manual operacional do pipeline validado. Detalhes de pesquisa e formato
ficam no log do mantenedor; aqui só o que precisa para **reproduzir**.

## Regras de ouro

1. **Feche o jogo antes de escrever.** Ele trava os blobs do CmsCache
   (tentar escrever com o jogo aberto dá `WinError 5` e deixa o cache
   inconsistente — foi assim que o unlock quebrou na primeira vez).
2. **A fonte runtime é o CmsCache**, não o install:
   `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\`.
   O `install` (`media/pcfamily/cms/`) é só semente e **não** precisa ser
   modificado (a POC provou que o jogo ignora o install para texto).
3. **Todo write faz backup automático** (`_backup\cache_<timestamp>`,
   ~13 MB). Rollback: `python _tools\rollback_cache.py`.
4. **Não espelhe `mediapc/`** — **descontinuado em 30/10/2026**: confirmado
   que o jogo não lê `mediapc/`; a única fonte é o CmsCache (regra 2).
5. **Nunca commitar** a chave AES do CMS, o Forza Mod Tool ou arquivos do
   jogo. O repo é público; as regras do `.gitignore` e o `docs/THIRD_PARTY.md`
   dizem o que fica só local.

## Pré-requisitos

Python 3, .NET 10 SDK, e os oráculos compilados:

```powershell
dotnet build _tools\cmsoracle\cmsoracle.csproj -c Release
dotnet build _tools\cacheoracle\cacheoracle.csproj -c Release
```

Os oráculos dependem do runtime e das tabelas do Forza-Mod-Tool v1.3.0, que
você mantém localmente (fora do repo): veja `docs/THIRD_PARTY.md` e o README.

## Conceitos mínimos

| peça | o quê | observações |
|---|---|---|
| `prod\<snapshot>.json` | manifesto plaintext da snapshot (10.434 arquivos, 8 grupos) | `Size` = tam. do payload **cifrado**; `Checksum` = SHA-256(base64) do payload cifrado |
| blob `<bucket>\<SHA256HEX>` | ZIP deflate com as entradas cifradas | **content-addressed**: o nome original = sha256 do conteúdo. Mantemos o nome e só atualizamos `Size`/`Checksum` no manifesto (Strategy S) — validado no jogo |
| `cache-manifest.json` | índice snapshot→blob (10 entradas), **criptografado** (asset container) | re-criptar com o original como template: `cacheoracle.exe enc <plain> <template> <out>` |
| `Id` (int64) no manifesto | opaco (não é hash do Path — testado fnv/murmur/crc/md5/sha) | nunca recalcular; só manter |
| CMS payload | `AES-128-CBC(IV=0×16)` sobre `gzip` | cifra via oráculo: `cmsoracle.exe enc <plain> <template_cifrado> <out>` (template = payload atual); fallback Python `cms_crypto.py` |

## Criando e aplicando um mod

```powershell
# 1. gerar o kit (série nova: spec + build_series; outros: gerador sobre _tools/fmlib)
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

Teste sem tocar no jogo: `python _tools\snapshot_cache.py` e acrescente
`--cache-dir _work\cachetest` aos comandos acima.

Travas no código (valem para Claude, opencode ou humano): o apply **recusa**
sem um `--dry-run` sem erros nos últimos 30 min para o mesmo plano/payloads/estado
do cache, com processo `forza*` aberto, ou se `_tools\plan_lint.py` reprovar
(estático + multiplayer intocado + Strategy S/Checksum). Lint avulso:
`python _tools\plan_lint.py --plan <plan.json>`.

`plan.json` (exemplo comentado em `_tools\cache_edit_plan_example.json`):
4 alvos no ModCarrera 1 — 2 entradas `json` (`BuildersCupScheduleDataV4.json`
nas 2 snapshots) + 2 `bytes` (`LocStrings_pt-BR.str` pré-editado nas
2 snapshots). `cache_edit.py` resolve snapshot→blob **pelo Checksum das
entradas no manifesto** (nunca por nome/mtime — a 1ª versão pegava o blob
antigo por causa disso).

## Editando textos (`.str`)

`_tools\str_edit.py` — parse/rewrite com round-trip byte-idêntico.
Chaves novas são livres (`IDS_<md5("MC44|<rótulo>")>` desde o mc44 —
`fmlib.strs.key_for`; colisão verificada) e
de **qualquer tamanho** (a restrição "mesmo nº de chars" era só do patch
byte-a-byte da POC). Hoje só `LocStrings_pt-BR.str` recebe as chaves novas;
os outros 19 idiomas ficam sem elas (pendência).

## Editando a carreira (`BuildersCupScheduleDataV4.json`)

- Reordenar = permutar `cup.LadderOrderData` e `ladder.OrderData`
  (listas de IDs). Barato, sem IDs novos, sem risco de save.
- Destravar = zerar `RequiredLadders/RequiredSeries/RequiredEvents`
  (+ contadores) em cada série .
- Re-serializar com `json.dump(obj, ensure_ascii=False, separators=(",",":"))`
  reproduz o original **byte-idêntico** (validado nos 1.197.441 B).

## Publicando um kit (`patches/<nome>/`)

Estrutura do `modcarrera1` (modelo): `plan.json` + payloads `.enc`
+ `report.<snap>.txt` + the kit's notes file (escopo + como reaplicar).
Só vale para CmsCache com as
**mesmas snapshots** (se o servidor baixar snapshot nova, regenerar o kit).

## Séries novas (F3) e trackday (F6)

Nada disso muda o pipeline de aplicação acima (plano → `--dry-run` →
`--verify`); muda só o que vai dentro do plano.

- **Série nova (F3):** caminho padrão = spec + `build_series.py`
  (`specs/README.md`); receita e porquês em **`docs/F3_TEMPLATE.md`** — ids
  novos (`ChampionshipSeriesId` ≥20000, `EventDataId` 65897900–65899999, nunca
  reusar), série + `OrderData` do ladder, eventos + `BCEventOverrides`,
  entrada em `BCSeriesSelectableCars.xml` (sem ela o clique crasha) e chave
  `IDS_` nova no `.str`. Validada na 20003; kits mc30–mc53 do laboratório do mantenedor.
  Sintomas/causas já vistas: [TROUBLESHOOTING](../TROUBLESHOOTING.md).
- **Trackday e grid de IA (F6):** série 20004 no cup 103 "7. Trackday"
  (kits mc55–mc58 do laboratório do mantenedor). A IA não vem só do BCS: o campo é fixado por
  `AIField_117160001_Gen.xml`, que **não existe no CmsCache** (só no zip do
  install). Conteúdo desse tipo de grupo **não** é aplicado pelo
  `cache_edit.py`: use `python _tools\install_edit.py --logical <arquivo>
  --payload <.enc>` (`--dry-run` antes, jogo fechado, `--verify`; backup em
  `_backup\install_<ts>`, desfaz com `--restore`). Ele reescreve o zip, o
  manifesto do install e as 2 snapshots de `prod\` + `cache-manifest.json`
  juntos. Testado em jogo com o mc58. Ver **`docs/AIFIELD_GRIDS.md`**.

## Verificação pós-escrita

`python _tools\cache_verify.py` — confere `Size`/`Checksum` de todos os
arquivos, consistência blob↔manifesto e divergências por snapshot.
Toda aplicação deve terminar com 0 erros.
