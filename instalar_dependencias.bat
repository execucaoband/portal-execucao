@echo off
set "BASE=%~dp0"
cd /d "%BASE%"
chcp 65001 >nul
if exist "ferramentas\python\python.exe" if exist "gerador\node_modules\pptxgenjs" (
  echo Versao portatil: Python, Node.js e bibliotecas ja estao na pasta "ferramentas". Nada a instalar.
  pause
  exit /b 0
)
echo Instalando bibliotecas no Python e no Node.js instalados no computador...
python -m pip install -r requirements.txt || goto erro
cd gerador
call npm install || goto erro
echo Pronto.
pause
exit /b 0
:erro
echo ERRO na instalacao. Se nao puder instalar programas, use a versao portatil.
pause
exit /b 1
