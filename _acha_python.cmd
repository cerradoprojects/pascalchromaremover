@echo off
rem Usado pelos .bat do Pascal (nao precisa abrir este arquivo).
rem Acha um Python que funcione e guarda o comando em PY. Ordem:
rem   1. o Python que vem com o Pascal (pasta python);
rem   2. se o computador bloquear esse, um Python instalado: pasta X:\Python (computador corporativo),
rem      instalador do python.org (por usuario ou para todos), gerenciador de Pythons, py, python.
rem As bibliotecas do recorte avancado (numpy, onnxruntime) ja vem com o Pascal para Python 3.12, 3.13 e 3.14:
rem nao precisa instalar nada alem do proprio Python.
set "PY="
set "PY_FORA="
call :testa "%~dp0python\python.exe"
if defined PY goto :eof
set "PY_FORA=1"
if exist "X:\Python\python.exe" call :testa "X:\Python\python.exe"
if not defined PY for /d %%D in ("X:\Python\*") do if not defined PY if exist "%%~D\python.exe" call :testa "%%~D\python.exe"
if not defined PY for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-3.*") do if not defined PY if exist "%%~D\python.exe" call :testa "%%~D\python.exe"
if not defined PY for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if not defined PY if exist "%%~D\python.exe" call :testa "%%~D\python.exe"
if not defined PY for /d %%D in ("%ProgramFiles%\Python3*") do if not defined PY if exist "%%~D\python.exe" call :testa "%%~D\python.exe"
if not defined PY for /d %%D in ("C:\Python3*") do if not defined PY if exist "%%~D\python.exe" call :testa "%%~D\python.exe"
if not defined PY for /f "delims=" %%W in ('where py 2^>nul') do if not defined PY call :testa "%%W" -3
if not defined PY for /f "delims=" %%W in ('where python 2^>nul ^| findstr /v /i "WindowsApps"') do if not defined PY call :testa "%%W"
goto :eof

:testa
rem o Pascal precisa de Python 3.10 ou mais novo
%1 %2 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 3)" >nul 2>nul
if not errorlevel 1 set PY=%1 %2
goto :eof
