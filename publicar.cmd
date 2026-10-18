@echo off
cd /d "%~dp0"
title Publicar - Quem e o Craque
echo Publicando jogo + dados no repositorio...
echo.
python publicar.py --jogo %*
echo.
echo (o Cloudflare reconstrói o site em ~30 segundos)
pause
