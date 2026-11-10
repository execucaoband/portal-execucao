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
echo Gerando os SOVI resumidos (a primeira vez demora: cada arquivo bruto tem dezenas de MB)...
python gerador\processar.py --so-sovi || goto erro
echo.
set "ENVIAR=N"
if not "%SUPABASE_URL%"=="" if /i not "%SUPABASE_URL:SEU-PROJETO=%"=="%SUPABASE_URL%" goto fim
if "%SUPABASE_URL%"=="" goto fim
set /p ENVIAR="Enviar os SOVI resumidos para o Supabase agora? (S/N) "
if /i "%ENVIAR%"=="S" python supabase\publicar_supabase.py enviar-sovi || goto erro
:fim
echo.
echo Os SOVI resumidos ficam na pasta dados\sovi_resumido (menos de 1 MB por mes).
pause
exit /b 0
:erro
echo.
echo ERRO. Veja a mensagem acima.
pause
exit /b 1
