@echo off
rem a pasta é guardada ANTES de trocar a página de código (caminhos com acento, ex.: OneDrive "Área de Trabalho")
set "BASE=%~dp0"
cd /d "%BASE%"
chcp 65001 >nul
if not exist "%BASE%segredos.bat" (
  echo Nao encontrei o segredos.bat na pasta:
  echo   %BASE%
  echo Crie o arquivo segredos.bat a partir do segredos.exemplo.bat nessa pasta.
  pause
  exit /b 1
)
call "%BASE%segredos.bat"
cd /d "%BASE%"
rem planilhas: pasta do OneDrive (opcional) + as enviadas pela aba Cargas do portal (dados\bases)
if not defined DADOS_DIR goto :so_bases
set "DADOS_DIR=%DADOS_DIR%;%BASE%dados\bases"
goto :dados_ok
:so_bases
set "DADOS_DIR=%BASE%dados\bases"
:dados_ok
if not exist "%BASE%dados\bases" mkdir "%BASE%dados\bases"
rem --- usa o Python e o Node portáteis da pasta "ferramentas" (sem instalar nada no Windows) ---
if not exist "%BASE%ferramentas\python\python.exe" goto :sem_portatil
set "PATH=%BASE%ferramentas\python;%BASE%ferramentas\python\Library\bin;%BASE%ferramentas\python\Scripts;%BASE%ferramentas\node;%PATH%"
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONNOUSERSITE=1"
:sem_portatil
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
where python >nul 2>nul || (echo Python nao encontrado. Use a versao portatil ^(pasta ferramentas^) ou instale o Python. & pause & exit /b 1)
where node >nul 2>nul || (echo Node.js nao encontrado. Use a versao portatil ^(pasta ferramentas^) ou instale o Node.js. & pause & exit /b 1)
set "CONFIG_DIR=%BASE%dados\config"
set "SAIDA_DIR=%BASE%dados\saida"
set "SOVI_CACHE=%BASE%dados\sovi_resumos"
set "PASTA_CONFIG=%CONFIG_DIR%"
set "PASTA_SAIDA=%SAIDA_DIR%"
echo [1/3] Trazendo do portal os pesos, supervisores, gerentes e agradecimentos cadastrados...
python supabase\publicar_supabase.py baixar-config || goto erro
echo [2/3] Calculando notas, SOVI, insights e apresentacoes (a primeira vez demora mais)...
python gerador\processar.py || goto erro
echo [3/3] Publicando no Supabase...
python supabase\publicar_supabase.py publicar || goto erro
echo.
echo Portal atualizado com sucesso.
pause
exit /b 0
:erro
echo.
echo ERRO. Veja a mensagem acima e o arquivo dados\saida\status_processamento.json
pause
exit /b 1
