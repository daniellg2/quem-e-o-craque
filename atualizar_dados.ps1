# ============================================================================
#  QUEM É O CRAQUE?  ·  atualização de dados (menu do PC)
#
#  Roda o pipeline_dados.py e o publicar.py numa telinha só.
#  Uso normal: dê dois cliques no "atualizar_dados.cmd".
#  (Este arquivo é UTF-8 com BOM — não regrave sem o BOM.)
# ============================================================================
$pasta = $PSScriptRoot
Set-Location $pasta

try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$env:PYTHONIOENCODING = 'utf-8'

# ---------------------------------------------------------------- cores ----
$AZUL   = 'Cyan'
$VERDE  = 'Green'
$AMAR   = 'Yellow'
$VERM   = 'Red'
$CINZA  = 'DarkGray'
$BRANCO = 'White'

function Escreva([string]$texto, [string]$cor = 'Gray') {
  Write-Host $texto -ForegroundColor $cor
}
function EscrevaSemPular([string]$texto, [string]$cor = 'Gray') {
  Write-Host $texto -ForegroundColor $cor -NoNewline
}
function LinhaFina([string]$rotulo) {
  Write-Host ''
  EscrevaSemPular '   ── ' $CINZA
  EscrevaSemPular $rotulo $AZUL
  EscrevaSemPular ' ' $CINZA
  Escreva ('─' * [Math]::Max(4, 58 - $rotulo.Length)) $CINZA
}
function Item([string]$tecla, [string]$nome, [string]$descricao) {
  EscrevaSemPular ('   ' + $tecla.PadRight(3)) $AMAR
  EscrevaSemPular ($nome.PadRight(12)) $BRANCO
  Escreva $descricao $CINZA
}
function Pausar {
  Write-Host ''
  EscrevaSemPular '   (pressione Enter para voltar ao menu) ' $CINZA
  [void](Read-Host)
}

# ------------------------------------------------------------- ambiente ----
$PY = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PY) { $PY = (Get-Command py -ErrorAction SilentlyContinue).Source }
$GIT = (Get-Command git -ErrorAction SilentlyContinue).Source
if (-not $GIT -and (Test-Path 'C:\Program Files\Git\cmd\git.exe')) {
  $GIT = 'C:\Program Files\Git\cmd\git.exe'
}
$script:ultimoOk = $false

function MostrarCabecalho {
  try { Clear-Host } catch {}
  Write-Host ''
  $titulo = 'QUEM É O CRAQUE?  ·  ATUALIZAÇÃO DE DADOS'
  $largura = 58
  $meio = $titulo.PadLeft([int](($largura + $titulo.Length) / 2)).PadRight($largura)
  Escreva ('  ╔' + ('═' * $largura) + '╗') $AZUL
  Escreva ('  ║' + $meio + '║') $AZUL
  Escreva ('  ╚' + ('═' * $largura) + '╝') $AZUL
  Escreva '   os dados saem do Transfermarkt (o GitHub Actions não consegue' $CINZA
  Escreva '   raspar; por isso a atualização é aqui, manualmente).' $CINZA
  Escreva ('   site: quem-e-o-craque.danielsoqalt.workers.dev  ·  pasta: ' + $pasta) $CINZA
}

function MostrarMenu {
  MostrarCabecalho
  LinhaFina 'DADOS  (Transfermarkt — roda no seu PC)'
  Item '1' 'Clubes'    'baixa todos os elencos + valores e recalcula a fama'
  Item '2' 'Fama'      'recalcula a fama, rápido (não baixa nada)'
  Item '3' 'Gols'      'gols e jogos por jogador (continua de onde parou)'
  Item '4' 'Histórico' 'títulos oficiais e trajetória dos clubes'
  Item '5' 'Tudo'      'clubes + gols + histórico + fama'
  Item '6' 'Reputação' 'notas e divisão dos clubes (títulos fiéis)'
  LinhaFina 'PUBLICAR  (GitHub → Cloudflare Pages)'
  Item '7' 'Dados'     'sobe dados, scripts e reputações'
  Item '8' 'Jogo'      'sobe o index.html, imagens e dados'
  Item '9' 'Tudo'      'jogo + dados numa mensagem só'
  Write-Host ''
  Item 'T' 'Conferir'  'mostra jogo, imagens e dados sem enviar nada'
  Item 'S' 'Status'    'tamanhos, datas e o repositório'
  Item 'Q' 'Sair'
  Write-Host ''
  EscrevaSemPular '   Digite sua opção: ' $AMAR
}

# ---------------------------------------------------------------- ações ----
function Rodar([string]$rotulo, [string[]]$argumentos) {
  $script:ultimoOk = $false
  Write-Host ''
  Escreva ('   » ' + $rotulo) $AZUL
  Escreva ('     > python ' + ($argumentos -join ' ')) $CINZA
  Write-Host ''
  & $PY @argumentos
  $codigo = $LASTEXITCODE
  Write-Host ''
  if ($codigo -ne 0) {
    Escreva ("   ERRO: o comando terminou com código $codigo.") $VERM
    Escreva  '   Nada foi publicado. Leia a mensagem acima antes de tentar de novo.' $VERM
    Pausar
    return
  }
  $script:ultimoOk = $true
  Escreva '   ok — concluído.' $VERDE
}

function PerguntarPublicar {
  Write-Host ''
  EscrevaSemPular '   Publicar os dados agora? (S/n) ' $AMAR
  $r = (Read-Host).Trim().ToLower()
  if ($r -like 'n*') { return }
  Rodar 'Publicando os dados no GitHub...' @('publicar.py')
  if ($script:ultimoOk) { Pausar }
}

function FluxoDados([string]$rotulo, [string[]]$argumentos) {
  Rodar $rotulo $argumentos
  if ($script:ultimoOk) { PerguntarPublicar }
}

function MostrarStatus {
  MostrarCabecalho
  LinhaFina 'ARQUIVOS DO JOGO'
  $arquivos = @('dados.js', 'dados.txt', 'gols.js', 'gols.json', 'historico.js',
                'historico.json', 'copas.json', 'copero-times.js',
                'reputacao_clubes.json', 'index.html')
  foreach ($arq in $arquivos) {
    $p = Join-Path $pasta $arq
    EscrevaSemPular ('   ' + $arq.PadRight(26)) $BRANCO
    if (Test-Path $p) {
      $i = Get-Item $p
      $kb = [Math]::Round($i.Length / 1KB)
      EscrevaSemPular (($kb.ToString() + ' KB').PadLeft(10)) $CINZA
      Escreva ('   ' + $i.LastWriteTime.ToString('dd/MM/yyyy HH:mm')) $CINZA
    } else {
      Escreva '   ausente' $VERM
    }
  }
  $arqRep = Join-Path $pasta 'reputacao_clubes.json'
  if (Test-Path $arqRep) {
    try {
      $d = Get-Content $arqRep -Raw -Encoding UTF8 | ConvertFrom-Json
      Escreva ('   reputação: ' + @($d.PSObject.Properties).Count + ' clubes casados (chave nome|liga)') $VERDE
    } catch {
      Escreva '   reputação: não consegui ler o arquivo' $VERM
    }
  }
  LinhaFina 'REPOSITÓRIO (GitHub)'
  $alvo = 'C:\dev\quem-e-o-craque'
  if ($GIT -and (Test-Path (Join-Path $alvo '.git'))) {
    $linha = (& $GIT -C $alvo log -1 --date=short --format='%h  %ad  %s' 2>$null)
    if ($linha) { Escreva ('   último commit: ' + $linha) $CINZA }
    $st = @(& $GIT -C $alvo status --porcelain 2>$null | Where-Object { $_ -ne '' })
    if ($st.Count -gt 0) {
      Escreva ('   ' + $st.Count + ' arquivo(s) diferente(s) do repositório — use Publicar') $AMAR
    } else {
      Escreva '   tudo igual ao repositório' $VERDE
    }
  } else {
    Escreva ('   clone não encontrado em ' + $alvo) $VERM
  }
  Pausar
}

# ---------------------------------------------------------------- início ----
if (-not $PY) {
  MostrarCabecalho
  Escreva '   Python não encontrado no PATH.' $VERM
  Escreva '   Instale o Python (python.org) e rode este menu de novo.' $VERM
  Write-Host ''
  EscrevaSemPular '   (pressione Enter para fechar) ' $CINZA
  [void](Read-Host)
  exit 1
}

$sair = $false
while (-not $sair) {
  MostrarMenu
  $op = (Read-Host).Trim().ToUpper()
  switch ($op) {
    '1' { FluxoDados 'Clubes: baixando elencos, valores e fama... (pode demorar)' @('pipeline_dados.py', '--escopo', 'clubes') }
    '2' { FluxoDados 'Fama: recalculando (rápido)...' @('pipeline_dados.py', '--escopo', 'fama') }
    '3' { FluxoDados 'Gols: atualizando gols e jogos por jogador...' @('pipeline_dados.py', '--escopo', 'gols') }
    '4' { FluxoDados 'Histórico: atualizando títulos e trajetórias...' @('pipeline_dados.py', '--escopo', 'historico') }
    '5' { FluxoDados 'Tudo: clubes + gols + histórico + fama...' @('pipeline_dados.py', '--escopo', 'tudo') }
    '6' { FluxoDados 'Reputação: recalculando os clubes pela base do Copero...' @('pipeline_dados.py', '--escopo', 'reputacao') }
    '7' { Rodar 'Publicando os dados no GitHub...' @('publicar.py');        if ($script:ultimoOk) { Pausar } }
    '8' { Rodar 'Publicando o jogo + dados no GitHub...' @('publicar.py', '--jogo'); if ($script:ultimoOk) { Pausar } }
    '9' { Rodar 'Publicando tudo (jogo + dados)...' @('publicar.py', '--jogo', '-m', 'atualização completa (jogo + dados)'); if ($script:ultimoOk) { Pausar } }
    'T' { Rodar 'Conferindo o que mudaria (sem enviar)...' @('publicar.py', '--jogo', '--seco'); if ($script:ultimoOk) { Pausar } }
    'S' { MostrarStatus }
    'Q' { $sair = $true }
    default {
      Write-Host ''
      Escreva '   Opção inválida. Use 1-9, T, S ou Q.' $VERM
      Start-Sleep -Seconds 1
    }
  }
}

MostrarCabecalho
Escreva '   Feito! Até a próxima. ⚽' $VERDE
Write-Host ''
EscrevaSemPular '   (pressione Enter para fechar) ' $CINZA
[void](Read-Host)
