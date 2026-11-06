@echo off
cd /d "%~dp0"
title Publicar - Quem e o Craque
echo Publicando jogo + imagens + dados no repositorio...
echo.
python publicar.py --jogo %*
if errorlevel 1 (
  echo A publicacao falhou. Confira o erro acima; o envio nao foi confirmado.
  pause
  exit /b 1
)
echo.
echo Confira acima se houve envio e acompanhe o deploy na Cloudflare.
pause
