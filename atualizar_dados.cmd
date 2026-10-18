@echo off
rem Atalho do menu de atualizacao de dados (abre o atualizar_dados.ps1)
chcp 65001 >nul
mode con: cols=104 lines=42 >nul 2>&1
cd /d "%~dp0"
title Quem e o Craque - Atualizacao de dados
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0atualizar_dados.ps1"
if errorlevel 1 pause
