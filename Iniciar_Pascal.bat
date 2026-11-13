@echo off
rem Pascal - inicia o programa (nao precisa ser administrador).
rem Usa o Python portatil da pasta "python" e o FFmpeg da pasta "bin".
cd /d "%~dp0"
title Pascal

set "PY="
if exist "%~dp0python\python.exe" set "PY=%~dp0python\python.exe"
if not defined PY (
  where py >nul 2>nul && set "PY=py -3"
)
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo.
  echo  NAO ACHEI O PYTHON.
  echo  Siga o README.md: baixe o "Python embeddable" e solte o conteudo na pasta "python".
  echo.
  pause
  exit /b 1
)

if not exist "%~dp0bin\ffmpeg.exe" (
  if not exist "%~dp0bin\bin\ffmpeg.exe" (
    echo.
    echo  AVISO: ffmpeg.exe nao esta na pasta "bin". O programa abre, mas nao consegue processar video.
    echo  Siga o README.md, passo 2.
    echo.
  )
)

%PY% "%~dp0app.py"
if errorlevel 1 (
  echo.
  echo  O programa fechou com erro. Detalhes em: %~dp0cache\app.log
  pause
)

