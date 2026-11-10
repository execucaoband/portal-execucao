@echo off
rem Copie este arquivo para "segredos.bat" (que NÃO vai para o GitHub) e preencha.
rem Supabase -> Project Settings -> API
set "SUPABASE_URL=https://SEU-PROJETO.supabase.co"
set "SUPABASE_SERVICE_KEY=COLE_AQUI_A_CHAVE_SERVICE_ROLE"
rem Pasta das planilhas no OneDrive (OPCIONAL se as planilhas forem enviadas pela aba Cargas do portal; para não usar, deixe: set "DADOS_DIR=")
rem Pasta das planilhas no OneDrive (subpastas incluídas: FATOS_RED, FATOS_ICE_LATAM, FATOS_SOVI, TAB_AUX_RP, DIM_...)
rem Copie o caminho da barra de endereço do Explorador. Salve este arquivo em UTF-8. Várias pastas: separe com ;
set "DADOS_DIR=C:\Users\welde\OneDrive - Grupo José Alves\Área de Trabalho\Prévia 2026\TABELA_FATO"
set "ANO=2026"
rem Opcional: força o programa que transforma os slides em imagem (powerpoint ou libreoffice)
rem set "PPT_RENDER=powerpoint"
