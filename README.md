# Quem é o Craque?

Jogo de adivinhação de futebol em um único HTML, com dados raspados do Transfermarkt.

## Endereços

| | |
|---|---|
| **Site (principal)** | https://quem-e-o.craque.workers.dev/ |
| Link antigo (Netlify) | https://craques.netlify.app/ — só redireciona (301) para o endereço novo, via `netlify.toml` |
| Repositório | https://github.com/daniellg2/quem-e-o-craque |

## Arquivos do jogo (carregados pelo navegador)

| Arquivo | Papel |
|---|---|
| `index.html` | o jogo (HTML + CSS + JS) |
| `assets/career-events/` | imagens das escolhas do modo carreira; devem ser publicadas junto com o jogo |
| `dados.js` | jogadores: nome, clube atual, posição, idade, valor, liga, id e foto (Transfermarkt), nacionalidade, **fama** (campo 13) e famaBruta (14) |
| `assets/database/` | escudos, bandeiras e logos extraídos de `dados.js`, mais os escudos especiais em `crests/`; mantenha a árvore de pastas ao copiar |
| `imagens-offline.js` | compatibilidade das imagens com canvas ao abrir por `file://`; não é solicitado na navegação HTTP/HTTPS |
| `_headers` | revalidação do jogo e escudos; cache longo das bandeiras e logos com hash na Cloudflare |
| `gols.js` / `gols.json` | gols, jogos em que marcou, gols decisivos/pênaltis/faltas, gols por clube e seleção |
| `copas.js` / `copas.json` | histórico de Copas do Mundo |
| `copero-times.js` | ligas e clubes do "Modo Copero" (base extraída do site copero.com.ar) |
| `copero-serie-d.js` | clubes da Série D e convidados sem divisão do modo Copero |
| `copero-angola-tahiti.js` | Girabola 2025/26 (16 clubes) e Tahiti 2026/27 (16 equipes, incluindo 3 reservas; AS Mira mantido como legado). Reputações do simulador, escudos locais e paletas calculadas com `corDoEscudo` para os cards funcionarem também ao abrir o jogo como arquivo local. |
| `reputacao_clubes.json` / `reputacao_clubes.js` | reputação real e divisão por `nome do jogo\|liga`; JSON no site e JS ao abrir por arquivo local. Ambos são gerados por `gerar_reputacao.py` e incluídos na publicação |
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
| `pegar_gemeos.py` | coleta Wikidata/Commons e incorpora Transfermarkt com validação automática, cache e retomada |
| `gemeos_transfermarkt.py` | consulta partidas e trajetórias; descobre jogadores em elencos antigos das ligas da database |
| `revisar_gemeos.py` | confere fichas e tabelas com a Wikipédia, separa escopos e gera a base revisada e o relatório |
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

## Coletar novos candidatos ao Gêmeo de Carreira

### Comparação no jogo

Ao encerrar a carreira, o jogo envia um resumo e três jogadores que já têm
figurinha para `/api/gemeo`. O Worker usa `gemini-3.5-flash-lite` para escolher
o mais parecido; o navegador aceita apenas o índice de um candidato
enviado e concede a figurinha correspondente. Se a consulta falhar ou demorar,
o gêmeo calculado localmente continua valendo em até 10 segundos. A pontuação mostrada no jogo é
o índice local de semelhança, não uma probabilidade da IA.

Configure `GEMINI_API_KEY` como Secret do Worker `quem-e-o` em Production.
Publique mudanças no jogo com `python publicar.py --jogo`; a publicação padrão
inclui `worker.js` e `wrangler.jsonc`, mas não inclui `index.html`.
O Worker limita cada IP a cinco comparações por minuto em cada local da Cloudflare.

### Experimento de comparação com Gemini

O teste usa exemplos fictícios e o conhecimento do modelo; não treina a IA, não
consulta a web e não altera a base do jogo. No mesmo Prompt em que configurou a chave:

```bat
set "GEMINI_API_KEY=SUA_CHAVE"
python testar_gemeo_gemini.py
```

Se a variável não estiver disponível no Prompt interativo, o script pede a chave
com entrada oculta. Cole e pressione Enter: os caracteres não aparecem e a chave
não é salva. Isso permite testar sem configurar a variável novamente.

São três exemplos por padrão: ídolo de clube pequeno, atacante de elite e goleiro
fiel. `--limite 10` testa todos os exemplos; `--caso idolo_pequeno` testa somente
esse caso. O modelo padrão é `gemini-3.8-flash`; se indisponível na sua conta, use
`--modelo CODIGO_DO_MODELO` com um modelo gratuito disponível no AI Studio.
O script não verifica faturamento nem garante gratuidade: cada chamada usa as cotas
e condições do projeto/modelo escolhido. Ele não ativa faturamento.

Resultados ficam em `cache/gemini-gemeos/teste.json` e `relatorio.md`. A chave vai
somente no cabeçalho da requisição, nunca no código, URL ou relatório. Respostas
completas são verificadas quanto ao formato, mas a escolha futebolística ainda
precisa de avaliação humana. A confiança exibida é declarada pela IA, sem calibração.

A IA agora propõe três candidatos identificados, compara posição, trajetória,
nível competitivo e produção, e escolhe um deles com uma justificativa comparativa.
Fidelidade e contexto de clubes pequenos são priorizados antes do volume de gols.
Se não conseguir identificar três nomes com segurança, pode retornar menos para
não forçar invenções. O script rejeita nomes repetidos e escolhas fora da lista;
isso valida o formato, sem comprovar a identidade ou as informações futebolísticas.
As instruções novas geram outra entrada no cache, preservando os testes antigos.

Repetir o comando reutiliza resultados com as mesmas instruções, modelo e carreira.
`--atualizar` faz novas chamadas. Erros interrompem o lote sem repetição automática,
preservando os resultados anteriores. Em 429, confira as cotas; em 404, confira o
modelo disponível. Não é necessário ativar faturamento para diagnosticar esses erros.

Se houver falha de conexão ou demora, execute `python testar_gemeo_gemini.py --diagnostico`.
Ele lista os modelos acessíveis com a chave, sem gerar comparações nem substituir
resultados salvos. Os erros distinguem timeout de conexão/leitura, proxy e TLS,
mantendo a verificação de certificados ativa. Uma listagem bem-sucedida ainda não
comprova cota de geração. Para testar só uma comparação, use `--limite 1`.

### Testar o SportDB antes de integrar

No Prompt de Comando, execute cada linha separadamente. Use uma chave nova se a
anterior tiver sido compartilhada. A variável vale somente nessa janela:

```bat
cd /d C:\Users\nelro\Downloads\Quem_e_o_craque
set "SPORTDB_API_KEY=SUA_CHAVE"
python testar_sportdb.py
```

O teste faz duas consultas: países e pesquisa por Messi. Exibe o status e a estrutura
do JSON, sem imprimir a chave. As respostas ficam em `cache/sportdb/teste.json`;
o jogo e as bases de gêmeos não são alterados. Falhas interrompem o teste sem apagar
respostas anteriores. Não há novas tentativas automáticas que consumam a cota.

Para pesquisar outro nome, use `python testar_sportdb.py --jogador "Rogerio Ceni"`.
Para testar as rotas de perfil, estatísticas e transferências, use
`python testar_sportdb.py --id 5958`. Essa segunda etapa verifica também se os
endpoints estão disponíveis no seu plano; HTTP 404 requer conferir a documentação.
Respostas HTTP 200 comprovam acesso, mas não garantem cobertura da carreira inteira.

```bash
python pegar_gemeos.py                       # 50 aposentados iniciais
python pegar_gemeos.py --ids Q12897 Q47526   # Pelé e Zico
python pegar_gemeos.py --lista jogadores.txt # um ID do Wikidata por linha
python pegar_gemeos.py --atualizar           # atualiza dados já coletados
python pegar_gemeos.py --offline             # usa somente cache local
python pegar_gemeos.py --tm-ids 17121 5958   # IDs do Transfermarkt, mesmo fora do Wikidata
python pegar_gemeos.py --ligas BRA1 --temporadas 2010 --limite 10
python pegar_gemeos.py --sem-transfermarkt   # mantém apenas a coleta original
```

O script usa `requests` e `beautifulsoup4`, já utilizados pelos coletores existentes. Os caminhos
padrão ficam ao lado do script, mesmo quando ele é executado de outra pasta.
Ele grava `gemeos.json`, `gemeos.js` e `gemeos_relatorio.json`, reaproveitando
`cache/gemeos/`. Respostas temporariamente indisponíveis
têm tentativas limitadas. No Transfermarkt, HTTP 202, 403, 405 e 429 suspendem as consultas
de rede ao site até a próxima execução, sem contornar bloqueios. Os registros anteriores
permanecem disponíveis se uma atualização falhar. Execute novamente para retomar
coletas incompletas. Para insistir numa atualização de um registro anterior completo,
use `--atualizar` novamente.

**Esta base ainda não é carregada pelo jogo.** Primeiro confira o relatório e os
dados coletados. Números por passagem podem representar apenas certas competições;
o script não soma esses números como se fossem toda a carreira. `totaisCarreira` e
`titulos` ficam `null` até conferência: prêmios individuais não equivalem a títulos
coletivos. As fotos guardam URL, página de origem, autor e licença para uso com os
créditos necessários. Uma resposta da API não garante que os dados estejam completos.

### Revisão dos registros coletados

```bash
python revisar_gemeos.py             # confere os jogadores, com cache das fontes
python revisar_gemeos.py --offline   # reproduz a revisão já coletada, sem rede
```

O revisor usa `requests` e `beautifulsoup4`, já presentes nos outros coletores.
Ele preserva os dados brutos e gera `gemeos_revisados.json`, `gemeos_revisados.js`
e `REVISAO_GEMEOS.md`. A base revisada separa clubes, reservas, base e seleções,
guarda as revisões consultadas da Wikipédia e distingue estatísticas de liga das
competições incluídas nas tabelas de clubes. Campos em branco não viram zero;
totais inconsistentes, com clubes ausentes ou com critérios conflitantes ficam
pendentes. Algumas conferências adicionais em clubes, federações e RSSSF estão
registradas com seu escopo e fonte. Títulos coletivos não são inferidos de prêmios.
As duas bases ainda não são carregadas automaticamente pelo jogo.

### Coleta e validação automática incorporadas

O comando `python pegar_gemeos.py` também gera `gemeos_validados.json/.js`
(`window.GEMEOS_VALIDADOS`). Ele reaproveita a revisão existente sem executar novamente
as consultas da Wikipédia. `gemeos_revisados.json` permanece intacto; `--revisados`
permite indicar outra referência. Os 50 registros originais continuam na base validada,
mesmo quando a consulta ao Transfermarkt é limitada a alguns jogadores.

Para cada perfil do Transfermarkt são consultados o perfil, a trajetória e o acervo
de partidas utilizado pela tabela do próprio site. O coletor valida a identidade,
elimina partidas repetidas, rejeita duplicatas conflitantes e separa seleção,
equipes fora da trajetória e amistosos identificados por `FS`. Só conta participações
marcadas como jogadas em partidas encerradas. Números ausentes permanecem `null`.
O resultado é agrupado por clube, temporada e competição, com URL, data e hash das
respostas para auditoria. Os downloads dos coletores antigos também são reaproveitados.

**Contagem do acervo não é total completo da carreira.** Clubes sem partidas e
diferenças em relação à revisão geram avisos automáticos. Mesmo quando os números
coincidem, o escopo ainda precisa ser equivalente: o coletor não promove uma soma
parcial a total confiável. As estatísticas revisadas continuam preferidas; títulos
e totais completos novos não são inventados. Isso permite acumular trajetórias úteis
sem exigir revisão manual de todo perfil. Campos que não passaram nas verificações
continuam indisponíveis para comparação numérica.

`--ligas BRA1 GB1 --temporadas 2005 2010` descobre jogadores nos elencos exatos
dessas temporadas, inclusive aposentados e atletas sem artigo no Wikidata. Só aceita
ligas presentes em `dados.js` e suportadas pelo coletor existente. Não troca
silenciosamente um elenco antigo pelo de outro ano. `--limite 10` limita a seleção
e interrompe a descoberta ao encontrar dez IDs únicos; aumentar o limite amplia
esse mesmo conjunto. Sem limite, percorre todos os elencos solicitados.

Perfis completos no cache de saída não são consultados novamente; use `--atualizar`
para forçar a atualização, ou `--atualizar --offline` para recalcular do cache local.
Uma falha de atualização preserva o perfil anterior e aparece em `relatorio.falhas`.
`relatorio.pendentesTransfermarkt` lista candidatos ainda sem coleta. Interromper com
Ctrl+C conserva as respostas recebidas e salva os perfis concluídos. O código de saída
é 0 no sucesso, 1 com falhas de coleta e 130 na interrupção.

Esta etapa prepara os dados; `gemeos_validados.js` ainda não é carregado pelo jogo.

## Publicar uma mudança no jogo

O publicador exige a raiz de um clone na branch `main`, com árvore de trabalho limpa (sem alterações preparadas ou arquivos não rastreados). Se houver trabalho local no clone, ele para antes de copiar; revise e guarde esse trabalho antes de tentar novamente. Ele prepara e commita somente os arquivos previstos, sem `git add -A`. Falhas de add, commit ou push encerram com erro; “Enviado ao GitHub” só aparece após push bem-sucedido e não confirma a conclusão do deploy.

Se apenas o push falhar, repita o mesmo comando: o commit de publicação pode ser reenviado sem criar outro commit, desde que contenha apenas caminhos autorizados e a marca `[skip netlify]`. Commits alheios ou merges pendentes exigem revisão manual. Se add/commit falharem, os arquivos copiados ficam preservados no clone; revise seu estado antes de repetir. O script não descarta alterações nem executa reset, stash ou force push.

`--seco` verifica o plano e os commits pendentes sem copiar, normalizar arquivos, commitar ou enviar. `--incluir` aceita apenas caminhos dentro das pastas de origem e destino.

1. Edite o `index.html` e coloque novas imagens nas subpastas de `assets/`.
2. Dê dois cliques no **`publicar.cmd`** (ou rode `python publicar.py --jogo`). O script inclui o `index.html`, os JavaScripts da carreira e toda a pasta `assets/`, inclusive taças e escudos.
3. Aguarde e confirme o sucesso do deploy na Cloudflare antes de tratar a versão como publicada.

O publicador confirma o envio ao GitHub; ele não consulta o status do deploy na Cloudflare.

### Carregamento e imagens

A tela inicial fica oculta nas aberturas rápidas. Ela só aparece se o jogo ainda estiver inicializando aos 2,5 segundos desde o início da navegação, e desaparece quando a inicialização termina. A espera por desafios compartilhados continua respeitada, com liberação de segurança após 20 segundos.

O conteúdo só é revelado depois que todos os estilos e ajustes finais do layout foram aplicados, no próximo quadro de renderização. Isso evita mostrar no desktop os ícones ampliados e os controles desalinhados de uma versão ainda incompleta da página.

Os troféus ficam em `assets/database/trophies/`, preservando as subpastas `national/` e `international/`. Foram transferidos 72 arquivos sem alteração de conteúdo; os caminhos de exibição, exportação e testes foram atualizados. A publicação com `--jogo` continua incluindo a pasta inteira de assets.

O `dados.js` passou de 9.765.597 para 1.444.554 bytes, mantendo o mesmo bloco de jogadores. Seus 1.125 escudos, bandeiras e logos foram extraídos sem alteração dos bytes para `assets/database/`; no site, o navegador baixa cada imagem conforme ela é usada. `publicar.py` inclui as imagens referenciadas até na publicação só de dados e interrompe se alguma estiver faltando. Em envio manual, não envie apenas `dados.js`: envie também seus arquivos de `assets/database/` e `imagens-offline.js`.

Ao abrir por `file://`, o HTML carrega `imagens-offline.js` antes do restante do jogo. Esse arquivo mantém os dados embutidos necessários para extrair cores dos escudos e exportar imagens em canvas sem bloqueio de origem do navegador. Ele ocupa aproximadamente 8,39 MB e preserva a compatibilidade offline; não há esse download no site HTTP/HTTPS. Os coletores regeneram o arquivo quando atualizam as imagens.

A opção histórica `pegar_dados.py --embutir-imagens` agora salva imagens locais com hash no nome, preservando a abertura por arquivo local e evitando recriar um JavaScript gigante. O cache em `cache/img` continua sendo reaproveitado pelos coletores.

Gols, Copas, histórico e reputações usam URLs estáveis, requisições compartilhadas na mesma página e limite de espera de oito segundos por recurso. A carreira carrega as bases em paralelo; em falha, oferece nova tentativa e permite jogar com os dados disponíveis. A comparação pode ser menos completa enquanto faltarem dados. Reputações usam `reputacao_clubes.js` por `file://`, pois o navegador bloqueia a leitura do JSON por `fetch` nesse modo. `_headers` configura revalidação para escudos e cache longo para bandeiras e logos com hash; valide os cabeçalhos no ambiente publicado após o deploy.

Os 140 escudos de Ypiranga, São Bernardo, Série D e Angola/Taiti foram reunidos em `assets/database/crests/`, preservando subpastas `serie-d-2026/` e `angola-tahiti/` para evitar colisões. As referências do jogo, cadastros e testes foram atualizadas. `assets/database/flags/` continua necessário: `flag()` usa essas imagens como alternativa quando o país não tem SVG mapeado. Na base verificada, esse é o caso de China e Tailândia (409 jogadores); remover a pasta quebraria essa alternativa.

Sete imagens grandes foram convertidas para WebP, mantendo as dimensões, com qualidade 90: 13.099.513 → 1.124.748 bytes. Os originais e o `dados.js` anterior ficam em `_arquivo/otimizacao-2026-11-05/`, com `manifest.json` para identificar os caminhos anteriores e novos. Essa pasta não é enviada pelo publicador e está excluída dos assets da Cloudflare. Versões antigas do HTML que referenciem os nomes anteriores precisam das respectivas imagens originais; os arquivos antigos já existentes no clone de publicação não são apagados automaticamente.

Verificações desta alteração:

```powershell
python -B -m unittest discover -s tests -p 'test_publicar.py'
python -B -m unittest discover -s tests -p 'test_imagens_locais.py'
node tests/data-loading.cjs
node tests/boot-loading.cjs
node tests/performance-browser.cjs
```

Os testes de publicação usam repositórios temporários e remotes locais, sem acesso ao GitHub. O teste de navegador usa o Edge instalado e bloqueia conexões externas.

> Alternativa: subir o arquivo pelo GitHub (Add file → Upload files). Funciona,
> mas aí rode `git -C C:\dev\quem-e-o-craque pull` depois para a cópia local
> não ficar para trás. Se enviar `index.html`, envie também `career-divisions.js`, `motor-copero.js`, `copero-serie-d.js`, `copero-angola-tahiti.js`, `reputacao_clubes.js` e toda a pasta `assets/`, preservando as subpastas.

As mudanças de Angola e Taiti estão incluídas em `publicar.cmd`: ligas, clubes,
escudos e cores, nomes e ordem das ligas, bandeiras e troféus. As imagens novas
ficam em `assets/database/crests/angola-tahiti/`, `assets/database/trophies/national/ANG/`,
`assets/database/trophies/national/TAH/` e `assets/database/trophies/international/CAF/`.
No Taiti, `liga.png` usa a arte dourada aprovada e `copa-polinesia.png` usa a nova
arte prateada. Para conferir o envio sem publicar: `python publicar.py --jogo --seco`.

## Cuidados

- `privacidade.html` e `termos.html` são minutas acessíveis pelo rodapé do jogo, com estilo em `legal.css`. Estão incluídas em `publicar.py --jogo`. Antes de publicar, preencha nome/razão social e e-mail nos dois documentos, confirme condições de retenção, transferência internacional e modalidade da API Gemini, valide as bases legais e os direitos sobre materiais de terceiros. Remova o aviso de minuta e o `noindex` somente após essa revisão. `AUDITORIA.md` registra os problemas encontrados e não deve ser publicado como página do site.

- Arquivo novo (ex.: `modo7.js`) só entra no repositório se estiver na lista do `publicar.py` — publique com `python publicar.py --incluir modo7.js` ou peça para eu adicionar de vez.
- O `pegar_dados.py` tem trava de segurança: se a raspagem voltar vazia (site bloqueando, layout novo) ele **falha sem gravar nada** — o site nunca fica sem jogadores.
- `dados.txt` é o intermediário do `pegar_dados.py` (fonte para `pegar_gols.py`/`pegar_historico.py`); é regenerado automaticamente quando falta.
- `cache/` (Transfermarkt) e `cache_ogol/` (oGol) são caches locais — podem ser apagados, só deixam a próxima raspagem mais lenta.
- O `pegar_dados.py` só enxerga mudança de clube se rodar com `--sem-cache` (o pipeline já faz isso).
- Workflows agendados do GitHub são desativados após 60 dias sem atividade no repositório (qualquer commit reativa).
- A pasta `_rea_copero/` guarda o material do reverse-engineering do site copero.com.ar (bundle baixado, evidências e testes) — é histórico, não entra no site.
