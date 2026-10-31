# Comece aqui

> 🌐 **Português** · [English](../en/GETTING_STARTED.md)

Objetivo: em uns 15 minutos, ver o pipeline inteiro funcionando numa **cópia**
do cache, sem tocar no jogo. Depois leia [CONCEITOS](CONCEPTS.md) e
[PIPELINE](PIPELINE.md).

## 1. Requisitos

- Windows e Forza Motorsport (2023) na Steam, aberto pelo menos uma vez. Isso
  cria o CmsCache em `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\`.
- Python 3.10+ e o .NET 10 SDK.
- O [Forza Mod Tool](https://github.com/HTTPJXRDN/Forza-Mod-Tool) v1.3.0 e a
  chave do CMS, guardados só localmente (ignorados pelo git): veja
  [THIRD_PARTY](../THIRD_PARTY.md) (em inglês).
- Terminal PowerShell na raiz do repo.

## 2. Preparação (uma vez)

```powershell
dotnet build _tools\cmsoracle\cmsoracle.csproj -c Release
dotnet build _tools\cacheoracle\cacheoracle.csproj -c Release
git config core.hooksPath .githooks          # travas de pre-commit
# só se o jogo NÃO estiver em F:\SteamLibrary\steamapps\common\Forza Motorsport:
$env:FM_INSTALL = "D:\...\Forza Motorsport"
```

## 3. Olhe antes de mexer

```powershell
python _tools\snapshot_cache.py              # copia o cache para _work\cachetest (jogo fechado)
python _tools\inventory.py --check           # os inventários gerados estão atualizados?
```

Abra the `CARREIRA` inventory page (árvore da carreira),
the `PISTAS` inventory page, the `CARROS` inventory page e
the `ESTADO` inventory page (quais kits estão ativos no seu cache).

## 4. Dry-run de um kit na cópia

Use qualquer kit que você já gerou (o passo 5 gera um; a pasta do kit é `patches\<kit>\`).

```powershell
python _tools\plan_lint.py --plan patches\<kit>\plan.json
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json --cache-dir _work\cachetest
```

Esperado: `lint profundo: ok` e a linha de resumo. `ja corretos` significa
"já está no estado desejado". Exit 3 indica só avisos, por exemplo alvos que
vivem no install e são ignorados.

## 5. Gere uma série a partir de uma spec (ainda na cópia)

```powershell
python _tools\build_series.py --spec specs\_TEMPLATE.json --cache-dir _work\cachetest --out _work\kit_demo
python _tools\cache_edit.py --dry-run --plan _work\kit_demo\plan.json --cache-dir _work\cachetest
python _tools\cache_edit.py --plan _work\kit_demo\plan.json --cache-dir _work\cachetest --verify --no-backup
```

Esperado: `verificacao: OK`. Você acabou de adicionar a série 20005 a uma cópia
do cache. Os mantenedores também conferem o gerador contra um kit de regressão
privado (só no laboratório; não faz parte deste repositório).

## 6. Para valer (jogo FECHADO)

Crie sua spec em `specs/` (ver `specs/README.md`), escolha um nome de kit e
siga o [PIPELINE](PIPELINE.md) sem `--cache-dir`. O apply faz backup, grava
`patches/ledger.jsonl` e recusa rodar com o jogo aberto ou sem dry-run recente.
Para desfazer: `python _tools\rollback_cache.py`.

## Se der errado

| sintoma | causa / correção |
|---|---|
| `nenhum --dry-run sem erros encontrado` | rode antes o `--dry-run` do mesmo plano e cache (vale 30 min) |
| `jogo aberto (ForzaMotorsport.exe)` | feche o jogo por completo |
| `cmsoracle.exe not found` | compile os oráculos (passo 2) |
| `WinError 5` ao escrever | jogo ou outro processo segurando os arquivos: feche e rode `rollback_cache.py` |
| série crasha ao clicar | falta a entrada no `BCSeriesSelectableCars.xml` (o `build_series` adiciona); ver [TROUBLESHOOTING](../TROUBLESHOOTING.md) (em inglês) |
