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
| `index.html` | o jogo (HTML + CSS + JS) |
| `assets/career-events/` | imagens das escolhas do modo carreira; devem ser publicadas junto com o jogo |
| `dados.js` | jogadores: nome, clube atual, posição, idade, valor, liga, id e foto (Transfermarkt), nacionalidade, **fama** (campo 13) e famaBruta (14) |
| `gols.js` / `gols.json` | gols, jogos em que marcou, gols decisivos/pênaltis/faltas, gols por clube e seleção |
| `copas.js` / `copas.json` | histórico de Copas do Mundo |
| `copero-times.js` | ligas e clubes do "Modo Copero" (base extraída do site copero.com.ar) |
| `reputacao_clubes.json` | reputação real e divisão de cada clube (chave `nome do jogo\|liga`), casadas com a base do Copero — é o que deixa os títulos fiéis (clube fraco não ganha continental). Gerado pelo `gerar_reputacao.py` |
| `historico.js` / `historico.json` | títulos oficiais por competição + trajetória de clubes (usado pelo "Gêmeo de Carreira") |
| `famosos.txt` | IDs do Transfermarkt de jogadores "estrela" (entrada do cálculo da fama) |
| `copas_tm.json` | cruzamento Copas × Transfermarkt (entrada do bônus de fama por Copa) |
| `netlify.toml` | manda a Netlify apenas redirecionar para o endereço novo |

## Scripts (rodam no PC ou no GitHub Actions)

| Arquivo | Papel |
|---|---|
| `pipeline_dados.py` | orquestrador: `--escopo clubes \| fama \| gols \| historico \| reputacao \| tudo` (clubes/fama/gols/tudo refazem o `reputacao_clubes.json` no fim) |
| `gerar_reputacao.py` | casa os clubes do `dados.js` com a base do Copero e grava o `reputacao_clubes.json` (é o que corrige os títulos) |
| `atualizar_dados.cmd` / `atualizar_dados.ps1` | menu bonito no PC para rodar o pipeline e publicar (dois cliques no `.cmd`) |
| `pegar_dados.py` | baixa as ligas, gera `dados.txt` e atualiza o `dados.js` (também recalcula a fama com `--so-fama`) |
| `pegar_gols.py` | gera `gols.json`/`gols.js` (retoma de onde parou) |
| `pegar_historico.py` | gera `historico.json`/`historico.js` (retoma de onde parou) |
| `pegar_copas.py` / `pegar_copas2.py` | copas (fonte: oGol) — só quando muda |
| `cruzar_copas.py` | gera `copas_tm.json` |
| `fama_copas.py` | grava a fama de Copa no `copas.js` |
| `publicar.py` | copia os arquivos para o clone do repositório e publica (`[skip netlify]` automático) |

## Como atualizar os dados

O jeito fácil: dê dois cliques no **`atualizar_dados.cmd`** — abre um menu (dados + publicação) que mostra o progresso e publica quando você mandar. Por baixo dele é o mesmo pipeline abaixo.

Na mão:

```bash
# no PC (na pasta do jogo)
python pipeline_dados.py --escopo clubes     # clubes/valores + fama  (~500 requisições, 20-40 min)
python pipeline_dados.py --escopo gols       # gols/jogos + fama      (retoma de onde parou)
python pipeline_dados.py --escopo historico  # títulos/trajetória     (retoma de onde parou)
python pipeline_dados.py --escopo reputacao  # razão/divisão dos clubes p/ os títulos (usa a base do Copero)
python pipeline_dados.py --escopo tudo       # tudo, na ordem

python publicar.py                            # publica os dados no repositório
python publicar.py --jogo                     # + index.html, JS da carreira e assets/ inteiro
```

### No servidor (grátis, sem PC ligado)

> **Atenção**: na prática o Transfermarkt bloqueia o robô do GitHub Actions (responde `HTTP 202` com 0 bytes), então a atualização de verdade sai pelo PC, pelo menu `atualizar_dados.cmd`. O workflow abaixo fica de reserva (histórico de copas e outras fontes).

`.github/workflows/atualizar-dados.yml`:

| Quando | Escopo |
|---|---|
| segunda 06:00 UTC | `clubes` + fama |
| dia 1 06:00 UTC | `gols` + fama |
| 15/jan, abr, jul, out | `historico` |
| botão **Run workflow** | você escolhe |

O robô roda o pipeline e commita sozinho. O commit sai com `[skip netlify]` — a Netlify ignora, o Cloudflare constrói. **Não use `[skip ci]`**: o Cloudflare pularia a construção.

## Como publicar uma mudança no jogo

1. Edite o `index.html` e coloque novas imagens nas subpastas de `assets/`.
2. Dê dois cliques no **`publicar.cmd`** (ou rode `python publicar.py --jogo`). O script inclui o `index.html`, o JavaScript da carreira e toda a pasta `assets/`, inclusive taças e escudos.
3. O Cloudflare reconstrói em ~30 s e o site já está atualizado para todo mundo.

> Alternativa: subir o arquivo pelo GitHub (Add file → Upload files). Funciona,
> mas aí rode `git -C C:\dev\quem-e-o-craque pull` depois para a cópia local
> não ficar para trás. Se enviar `index.html`, envie também os arquivos necessários de `assets/` e `career-divisions.js`.

## Cuidados

- Arquivo novo (ex.: `modo7.js`) só entra no repositório se estiver na lista do `publicar.py` — publique com `python publicar.py --incluir modo7.js` ou peça para eu adicionar de vez.
- O `pegar_dados.py` tem trava de segurança: se a raspagem voltar vazia (site bloqueando, layout novo) ele **falha sem gravar nada** — o site nunca fica sem jogadores.
- `dados.txt` é o intermediário do `pegar_dados.py` (fonte para `pegar_gols.py`/`pegar_historico.py`); é regenerado automaticamente quando falta.
- `cache/` (Transfermarkt) e `cache_ogol/` (oGol) são caches locais — podem ser apagados, só deixam a próxima raspagem mais lenta.
- O `pegar_dados.py` só enxerga mudança de clube se rodar com `--sem-cache` (o pipeline já faz isso).
- Workflows agendados do GitHub são desativados após 60 dias sem atividade no repositório (qualquer commit reativa).
- A pasta `_rea_copero/` guarda o material do reverse-engineering do site copero.com.ar (bundle baixado, evidências e testes) — é histórico, não entra no site.
