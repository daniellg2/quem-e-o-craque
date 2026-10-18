# Quem é o Craque?

Jogo de adivinhação de futebol em um único HTML, com dados raspados do Transfermarkt.

## Endereços

| | |
|---|---|
| **Site (principal)** | https://quem-e-o-craque.danielsoqalt.workers.dev/ |
| Link antigo (Netlify) | https://craques.netlify.app/ — só redireciona (301) para o endereço novo, via `netlify.toml` |
| Repositório | https://github.com/daniellg2/quem-e-o-craque |

## Arquivos do jogo (carregados pelo navegador)

| Arquivo | Papel |
|---|---|
| `index.html` | o jogo inteiro (HTML + CSS + JS). A cópia local é o `index6.html` |
| `dados.js` | jogadores: nome, clube atual, posição, idade, valor, liga, id e foto (Transfermarkt), nacionalidade, **fama** (campo 13) e famaBruta (14) |
| `gols.js` / `gols.json` | gols, jogos em que marcou, gols decisivos/pênaltis/faltas, gols por clube e seleção |
| `copas.js` / `copas.json` | histórico de Copas do Mundo |
| `copero-times.js` | ligas e clubes do "Modo Copero" (base extraída do site copero.com.ar) |
| `historico.js` / `historico.json` | títulos oficiais por competição + trajetória de clubes (usado pelo "Gêmeo de Carreira") |
| `famosos.txt` | IDs do Transfermarkt de jogadores "estrela" (entrada do cálculo da fama) |
| `copas_tm.json` | cruzamento Copas × Transfermarkt (entrada do bônus de fama por Copa) |
| `netlify.toml` | manda a Netlify apenas redirecionar para o endereço novo |

## Scripts (rodam no PC ou no GitHub Actions)

| Arquivo | Papel |
|---|---|
| `pipeline_dados.py` | orquestrador: `--escopo clubes \| fama \| gols \| historico \| tudo` |
| `pegar_dados.py` | baixa as ligas, gera `dados.txt` e atualiza o `dados.js` (também recalcula a fama com `--so-fama`) |
| `pegar_gols.py` | gera `gols.json`/`gols.js` (retoma de onde parou) |
| `pegar_historico.py` | gera `historico.json`/`historico.js` (retoma de onde parou) |
| `pegar_copas.py` / `pegar_copas2.py` | copas (fonte: oGol) — só quando muda |
| `cruzar_copas.py` | gera `copas_tm.json` |
| `fama_copas.py` | grava a fama de Copa no `copas.js` |
| `publicar.py` | copia os arquivos para o clone do repositório e publica (`[skip netlify]` automático) |

## Como atualizar os dados

```bash
# no PC (na pasta do jogo)
python pipeline_dados.py --escopo clubes     # clubes/valores + fama  (~500 requisições, 20-40 min)
python pipeline_dados.py --escopo gols       # gols/jogos + fama      (retoma de onde parou)
python pipeline_dados.py --escopo historico  # títulos/trajetória     (retoma de onde parou)
python pipeline_dados.py --escopo tudo       # tudo, na ordem

python publicar.py                            # publica os dados no repositório
python publicar.py --jogo                     # + o index6.html (vira index.html)
```

### No servidor (grátis, sem PC ligado)

`.github/workflows/atualizar-dados.yml`:

| Quando | Escopo |
|---|---|
| segunda 06:00 UTC | `clubes` + fama |
| dia 1 06:00 UTC | `gols` + fama |
| 15/jan, abr, jul, out | `historico` |
| botão **Run workflow** | você escolhe |

O robô roda o pipeline e commita sozinho. O commit sai com `[skip netlify]` — a Netlify ignora, o Cloudflare constrói. **Não use `[skip ci]`**: o Cloudflare pularia a construção.

## Como publicar uma mudança no jogo

1. Edite o `index6.html` (é um arquivo só: HTML + CSS + JS num lugar).
2. Dê dois cliques no **`publicar.cmd`** (ou rode `python publicar.py --jogo`).
3. O Cloudflare reconstrói em ~30 s e o site já está atualizado para todo mundo.

> Alternativa: subir o arquivo pelo GitHub (Add file → Upload files). Funciona,
> mas aí rode `git -C C:\dev\quem-e-o-craque pull` depois para a cópia local
> não ficar para trás — e lembre de nomear como `index.html`.

## Cuidados

- Arquivo novo (ex.: `modo7.js`) só entra no repositório se estiver na lista do `publicar.py` — publique com `python publicar.py --incluir modo7.js` ou peça para eu adicionar de vez.
- O `pegar_dados.py` tem trava de segurança: se a raspagem voltar vazia (site bloqueando, layout novo) ele **falha sem gravar nada** — o site nunca fica sem jogadores.
- `dados.txt` é o intermediário do `pegar_dados.py` (fonte para `pegar_gols.py`/`pegar_historico.py`); é regenerado automaticamente quando falta.
- `cache/` (Transfermarkt) e `cache_ogol/` (oGol) são caches locais — podem ser apagados, só deixam a próxima raspagem mais lenta.
- O `pegar_dados.py` só enxerga mudança de clube se rodar com `--sem-cache` (o pipeline já faz isso).
- Workflows agendados do GitHub são desativados após 60 dias sem atividade no repositório (qualquer commit reativa).
- A pasta `_rea_copero/` guarda o material do reverse-engineering do site copero.com.ar (bundle baixado, evidências e testes) — é histórico, não entra no site.
