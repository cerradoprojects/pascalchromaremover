@echo off
rem Pascal - testes do recorte avancado. Nao precisa ser administrador. Grava cache\teste_python.txt
cd /d "%~dp0"
title Pascal - testes
echo.
echo  Testando o recorte avancado deste computador. Pode levar alguns minutos.
echo  Nao feche esta janela.
echo.
call "%~dp0_acha_python.cmd"
if not defined PY (
  echo  Nenhum Python abriu. Instale o Python 3.13 ou 3.14 de 64 bits e rode este arquivo de novo.
  pause
  exit /b 1
)
%PY% "%~dp0_testes_python.py"
echo.
pause
