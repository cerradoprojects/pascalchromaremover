@echo off
rem Pascal - inicia o programa (nao precisa ser administrador).
rem Usa o Python portatil da pasta "python" (ou, se o computador bloquear, um Python instalado) e o FFmpeg da pasta "bin".
cd /d "%~dp0"
title Pascal

echo  Abrindo o Pascal...
call "%~dp0_acha_python.cmd"
if not defined PY (
  echo.
  echo  ============================================================
  echo   NAO CONSEGUI ABRIR O PYTHON
  echo  ============================================================
  echo   O Python que vem com o Pascal foi bloqueado por este computador
  echo   e nao achei outro Python instalado.
  echo.
  echo   Resolva assim, uma vez so:
  echo    1. Instale o Python 3.13 ou 3.14 de 64 bits.
  echo       Em computador corporativo, o instalador costuma ficar na pasta X:\Python.
  echo    2. Abra o Pascal de novo.
  echo.
  echo   Nao precisa instalar mais nada: as bibliotecas ja vem com o Pascal.
  echo.
  if exist "X:\Python\" (
    echo   Aperte qualquer tecla para abrir a pasta X:\Python.
    pause >nul
    start "" explorer "X:\Python"
  ) else (
    pause
  )
  exit /b 1
)
if defined PY_FORA echo  Usando o Python instalado neste computador: %PY%

if not exist "%~dp0bin\ffmpeg.exe" (
  if not exist "%~dp0bin\bin\ffmpeg.exe" (
    echo.
    echo  AVISO: ffmpeg.exe nao esta na pasta "bin". O programa abre, mas nao consegue processar video.
    echo  Baixe o Pascal.zip completo da pagina Releases do GitHub.
    echo.
  )
)

%PY% "%~dp0app.py"
if errorlevel 1 (
  echo.
  echo  O programa fechou com erro. Detalhes em: %~dp0cache\app.log
  pause
)
