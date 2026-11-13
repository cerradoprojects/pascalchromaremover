@echo off
rem Arraste um video em cima deste arquivo: ele recorta o fundo verde e grava
rem um .MOV ProRes 4444 com transparencia na pasta "output" (pronto para o Premiere).
cd /d "%~dp0"
title Pascal - recorte

set "PY="
if exist "%~dp0python\python.exe" set "PY=%~dp0python\python.exe"
if not defined PY (
  where py >nul 2>nul && set "PY=py -3"
)
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo NAO ACHEI O PYTHON. Veja o README.md.
  pause
  exit /b 1
)

if "%~1"=="" (
  echo.
  echo  Arraste um arquivo de video em cima deste .bat.
  echo.
  pause
  exit /b 1
)

%PY% "%~dp0recorte.py" "%~1" "%~dp0output" --formato prores
echo.
pause

