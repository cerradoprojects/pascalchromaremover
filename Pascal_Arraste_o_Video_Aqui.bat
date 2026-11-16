@echo off
rem Arraste um video em cima deste arquivo: ele recorta o fundo verde e grava
rem um .MOV ProRes 4444 com transparencia na pasta "output" (pronto para o Premiere).
cd /d "%~dp0"
title Pascal - recorte

call "%~dp0_acha_python.cmd"
if not defined PY (
  echo.
  echo  NAO CONSEGUI ABRIR O PYTHON. Instale o Python 3.13 ou 3.14 de 64 bits
  echo  ^(em computador corporativo: pasta X:\Python^) e tente de novo.
  echo  As bibliotecas ja vem com o Pascal: nao precisa instalar mais nada.
  echo.
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

