# Portal Execução: passo a passo para colocar no ar

Faça os passos na ordem. As partes 1 a 4 você faz uma vez só. A parte 6 se repete todo mês.

| Parte | O que é | Tempo |
|---|---|---|
| 1 | Preparar a pasta de planilhas no OneDrive | 10 min |
| 2 | Criar o banco no Supabase | 15 min |
| 3 | Subir o projeto no GitHub e publicar o portal | 15 min |
| 4 | Preparar o computador que processa | 20 min |
| 5 | Primeira carga e primeiro acesso | 15 min |
| 6 | Rotina do mês | 5 min + processamento |

---

## Parte 1 · Pasta de planilhas no OneDrive

O processamento lê as planilhas da pasta do OneDrive sincronizada no seu computador **e/ou** das planilhas enviadas pela aba **Cargas** do portal (veja a parte 6). Se você for usar só a aba Cargas, esta parte é opcional. Nada é enviado para a nuvem: só os resultados e as apresentações vão para o Supabase.

### 1.1 Deixar os arquivos disponíveis no computador

O OneDrive guarda arquivos "só na nuvem" (ícone de nuvem ☁). O processamento até consegue ler esses arquivos, mas fica lento, porque o SOVI tem arquivos de 80 MB ou mais. Para evitar isso:

1. Abra o **Explorador de Arquivos** e vá até `OneDrive - Grupo José Alves › Área de Trabalho › Prévia 2026`.
2. Clique com o botão direito na pasta **TABELA_FATO** e escolha **Sempre manter neste dispositivo**.
3. Espere os ícones ficarem com o **✔ verde preenchido**. Isso indica que os arquivos já estão no computador.

### 1.2 Como a pasta deve ficar

As subpastas podem ter qualquer nome: o processamento procura em todas. O que importa é o **nome de cada arquivo**:

```
TABELA_FATO\
├─ FATOS_RED\          FATOS_RED_JAN26.xlsx, FATOS_RED_FEV26.xlsx, …   (um por mês)
├─ FATOS_ICE_LATAM\    FATOS_ICE_JAN26.xlsx, FATOS_ICE_FEV26.xlsx, …   (um por mês)
├─ FATOS_SOVI\         arquivos do SOVI com "26" no nome (ex.: SOVI Setembro-26.xlsx)
├─ TAB_AUX_RP\         Janeiro26.xlsx, Fevereiro26.xlsx, …            (repositor, um por mês)
├─ FATOS_CPI.xlsx
├─ TOM.xlsx
├─ COMPROMISSO_ICE.xlsx
├─ DIM_GERENCIA.xlsx
└─ DIM_SUPERVISOR.xlsx
```

Regras dos arquivos:

- **Formato:** salve sempre como **.xlsx**. Os formatos .xls, .xlsb e .xlsm são ignorados.
- **SOVI:** só entram os arquivos do ano (com "26" no nome). O processamento lê a aba **RED360**.
- **Reenvio de um mês:** se você substituir um arquivo do mesmo mês, vale o mais recente.
- **Abertura no Excel:** feche o Excel antes de processar. Arquivos que começam com `~$` são temporários do Excel e são ignorados.

### 1.3 Copiar o caminho da pasta

1. No Explorador, entre na pasta **TABELA_FATO**.
2. Clique na **barra de endereço** (no alto) e copie o texto. Por exemplo:
   `C:\Users\welde\OneDrive - Grupo José Alves\Área de Trabalho\Prévia 2026\TABELA_FATO`
3. Guarde esse caminho, porque ele vai no `segredos.bat` na parte 4.

---

## Parte 2 · Supabase (banco de dados)

1. Entre em **supabase.com** e crie uma conta (pode ser com o GitHub).
2. Clique em **New project** e preencha:
   - **Name:** `portal-execucao`;
   - **Database password:** crie uma senha forte e guarde;
   - **Region:** *South America (São Paulo)*.
3. Espere o projeto ficar pronto, cerca de 2 minutos.
4. No menu à esquerda, abra **SQL Editor → New query**:
   - abra o arquivo `supabase\schema.sql` no Bloco de Notas;
   - copie tudo, cole no editor e clique em **Run**;
   - deve aparecer "Success. No rows returned".
5. Em **Authentication → Users → Add user → Create new user**, coloque o seu e-mail e uma senha e **marque "Auto Confirm User"**.
6. Volte ao **SQL Editor** e rode o comando abaixo, trocando o e-mail pelo seu, para virar administrador:
   ```sql
   insert into public.perfis (id, nome, email, genero, perfil, trocar_senha)
   select id, 'Welder Silva', email, 'M', 'admin', false
   from auth.users where email = 'welder.silva@rebic.com.br';
   ```
7. Em **Authentication → Sign In / Providers → Email**:
   - deixe o **Email** ligado;
   - **desligue "Confirm email"**. Assim os usuários que você criar no portal entram direto com a senha inicial.
8. Em **Project Settings → API** (ou **Data API / API Keys**), copie três coisas:
   - **Project URL**, por exemplo `https://abcdefgh.supabase.co`;
   - chave **anon / publishable**, que vai no portal;
   - chave **service_role / secret**, que vai **só** no `segredos.bat` e **nunca** no GitHub nem no portal.

---

## Parte 3 · GitHub e publicação do portal

### 3.1 Subir o projeto

1. Entre em **github.com**, clique em **New repository** e configure:
   - **Repository name:** `portal-indicadores-merchandising`;
   - **Visibilidade:** *Public* ou *Private* (veja a observação no 3.2);
   - **não** marque README nem .gitignore, porque o projeto já tem os dois.
2. Instale o **GitHub Desktop** (desktop.github.com) e entre com a sua conta.
3. Descompacte o `portal-indicadores-merchandising.zip` numa pasta **fora do OneDrive**, por exemplo `C:\Projetos\portal-indicadores-merchandising`.
4. No GitHub Desktop, use **File → Add local repository** e escolha a pasta. Ela já tem o histórico de versões.
5. Publique:
   - clique em **Publish repository**, ou em **Repository settings → Remote**;
   - cole o endereço do repositório que você criou;
   - clique em **Push origin**.

Ao subir, confira no site do GitHub que **não** apareceram `segredos.bat`, planilhas nem a pasta `dados\saida`. O projeto já está configurado para nunca enviar esses arquivos.

### 3.2 Publicar o portal

1. Na pasta do projeto, abra o `config.js` no Bloco de Notas e preencha:
   ```js
   SUPABASE_URL: "https://abcdefgh.supabase.co",
   SUPABASE_ANON_KEY: "cole-aqui-a-chave-anon",
   ```
2. No GitHub Desktop, faça **Commit** e depois **Push**.
3. Escolha onde publicar:
   - **Repositório público:** no GitHub, vá em **Settings → Pages**. Em *Source*, escolha *Deploy from a branch*; depois escolha a branch `main` e a pasta `/ (root)` e clique em **Save**. O endereço fica `https://SEU-USUARIO.github.io/portal-indicadores-merchandising/`.
   - **Repositório privado:** entre em **vercel.com** (ou netlify.com) com o GitHub e use **Add New → Project**. Escolha o repositório, clique em **Deploy** e não precisa configurar nada.
4. Volte ao Supabase, em **Authentication → URL Configuration**:
   - em **Site URL**, cole o endereço do portal;
   - assim os links de "esqueci a senha" voltam para o portal.

A chave anon pode ficar pública: quem protege os dados são as regras de acesso do banco.

---

## Parte 4 · Computador que processa (o seu)

### Opção A · Versão portátil (recomendada, não instala nada)

Use o arquivo **Portal_Execucao_portatil.zip**. Ele já traz dentro da pasta `ferramentas` um Python e um Node.js portáteis, com todas as bibliotecas.

- Não aparece nada no Windows nem no "Adicionar ou remover programas".
- Não precisa de senha de administrador.
- Para remover, basta apagar a pasta.

1. Clique com o botão direito no zip, escolha **Extrair tudo** e escolha, por exemplo, `C:\Portal Execucao`.
   - **Use um caminho curto.** Caminhos muito longos ou dentro de muitas subpastas do OneDrive podem passar do limite de caracteres do Windows.
2. Pronto: **não rode o `instalar_dependencias.bat`**. Siga para a Configuração, logo abaixo.

Para gerar as imagens dos slides, a versão portátil usa o **PowerPoint** que já está no seu Office.

### Opção B · Instalação normal

1. Instale os programas abaixo e reinicie o computador no final:
   - **Python 3.12**, de python.org. Na primeira tela da instalação, **marque "Add python.exe to PATH"**.
   - **Node.js LTS**, de nodejs.org.
   - O **PowerPoint**, que já vem no Office, é usado para transformar os slides em imagem. Se não tiver PowerPoint, instale o **LibreOffice** (libreoffice.org).
2. Na pasta do projeto, dê dois cliques em **`instalar_dependencias.bat`** e espere aparecer "Pronto.".

### Configuração (nas duas opções)

1. Copie o **`segredos.exemplo.bat`** e renomeie a cópia para **`segredos.bat`**. Abra no Bloco de Notas e preencha:
   ```bat
   set "SUPABASE_URL=https://abcdefgh.supabase.co"
   set "SUPABASE_SERVICE_KEY=cole-aqui-a-chave-service_role"
   set "DADOS_DIR=C:\Users\welde\OneDrive - Grupo José Alves\Área de Trabalho\Prévia 2026\TABELA_FATO"
   set "ANO=2026"
   ```
   - **Encoding:** salve o arquivo em UTF-8. No Bloco de Notas, use *Salvar como → Codificação: UTF-8*, por causa dos acentos do caminho.
   - **Várias pastas:** separe os caminhos com `;` (ponto e vírgula).
2. Dê dois cliques em **`conferir_pasta.bat`**. Ele mostra, item por item, o que encontrou na pasta do OneDrive:
   - **[OK]:** encontrado;
   - **[FALTA]:** a planilha obrigatória não está na pasta ou o nome está diferente do esperado;
   - **[AVISO] … só na nuvem:** faltou o passo 1.1 ("Sempre manter neste dispositivo").

---

## Parte 5 · Primeira carga e primeiro acesso

1. Dê dois cliques em **`atualizar_portal.bat`**. Na primeira vez demora mais, de 10 a 20 minutos, porque resume todo o SOVI do ano. Ele faz três passos:
   - **[1/3]** traz as configurações do portal;
   - **[2/3]** calcula as notas e gera as apresentações em imagem;
   - **[3/3]** publica no Supabase.
2. Abra o endereço do portal e entre com o seu e-mail e senha da parte 2.
3. Em **Painel Gerencial → Criar usuário**, cadastre cada gerente comercial:
   - nome, e-mail e senha inicial;
   - Obrigado ou Obrigada;
   - gerências e permissões.
   O gerente troca a senha no primeiro acesso.
4. Rode o **`atualizar_portal.bat`** de novo. Isso faz os nomes e o Obrigado/Obrigada entrarem nas apresentações.

---

## Parte 6 · Todo mês

### Opção recomendada · Enviar as planilhas pelo portal (aba Cargas)

1. **SOVI:** se tiver o SOVI bruto do mês, rode o **`reduzir_sovi.bat`**. Ele gera o `SOVI_RESUMIDO_<mês>.xlsx` (menos de 1 MB) na pasta `dados\sovi_resumido`.
2. **Envio:** no portal, abra **Painel Gerencial → ⬆ Cargas e processamento**. Há um quadro para cada base: **Subir RED**, **Subir ICE Latam**, **Subir Repositor**, **Subir CPI**, **Subir TOM**, **Subir SOVI resumido**, **Subir Compromisso de ICE** e **Subir Cadastros (DIM)**.
   - Escolha o **mês** (nas bases mensais) e clique em **Escolher arquivo e subir**.
   - O arquivo pode ter **qualquer nome**: o portal salva com o **nome padrão** (ex.: `FATOS_RED_OUT26.xlsx`, `Outubro26.xlsx`, `TOM.xlsx`), mostrado no quadro antes de subir.
   - O portal confere se é a planilha certa (ex.: a do repositor precisa ter a aba "Base Atendimento Repositor") e recusa o SOVI bruto.

   Se os arquivos já estiverem com o nome padrão, dá para enviar vários de uma vez em **"Enviar vários arquivos de uma vez"**:
   - `FATOS_RED_OUT26.xlsx`, `FATOS_ICE_OUT26.xlsx`, `Outubro26.xlsx` (repositor);
   - `FATOS_CPI.xlsx`, `TOM.xlsx` e, se mudaram, `COMPROMISSO_ICE.xlsx` e as `DIM_…xlsx`;
   - `SOVI_RESUMIDO_Outubro-26.xlsx`.

   O portal reconhece cada planilha pelo nome e mostra numa grade quais meses de cada base já estão lá. Nomes fora do padrão, arquivos acima de 50 MB e o SOVI bruto são recusados, com o motivo.
3. **Processamento:** rode o **`atualizar_portal.bat`**. Ele baixa as planilhas do portal (não precisa do OneDrive), calcula e publica.
4. **Prazo:** no portal, em **Reunião → Prazo de envio**, defina quando o envio abre e fecha.
5. **Gerentes:** cada um entra em **Minha apresentação**, baixa a base, preenche os planos de ação e envia a versão final até o prazo.
6. **Reunião:** em **Reunião**, clique em **Apresentar a partir da 1ª** (tela cheia, gerência a gerência) ou use **Baixar todas as finais (.zip)**.

Com as planilhas no portal, **outra pessoa consegue atualizar** só com a pasta portátil e o `segredos.bat`, sem acesso ao seu OneDrive.

### Alternativa · Pasta do OneDrive

Coloque as planilhas na pasta do `DADOS_DIR` e rode o `atualizar_portal.bat`. As duas fontes podem ser usadas juntas. Se o mesmo arquivo estiver nas duas, vale o mais recente, e um mês reenviado substitui o anterior, sem somar em dobro.

## SOVI resumido (arquivos pequenos para o Supabase)

Os arquivos brutos do SOVI têm de 80 a 134 MB por mês. O **`reduzir_sovi.bat`** gera, para cada mês, um **SOVI resumido de menos de 1 MB**, com o mesmo resultado. Ele fica só com refrigerante e suco e soma as frentes por gerência, supervisor, canal, sabor, fabricante, área e ponto de contato.

- **Onde ficam:** os resumidos ficam em `dados\sovi_resumido`.
- **O que o bat faz:** gera os resumidos e pergunta se você quer enviá-los ao Supabase (pasta privada `BASES/SOVI`, que só o administrador acessa).
- **Envio automático:** o `atualizar_portal.bat` também gera e envia os resumidos sozinho.
- **Outra pessoa atualizando:** no computador dela, o `atualizar_portal.bat` **baixa os SOVI resumidos do Supabase**. Ela **não precisa dos arquivos brutos do SOVI**, só das outras planilhas (RED, ICE, repositor, CPI, TOM…).
- **Mês repetido:** se o mesmo mês aparecer em dois arquivos, vale o mais recente. O processamento nunca soma em dobro.

## Problemas comuns

| Mensagem ou sintoma | O que fazer |
|---|---|
| `Python nao encontrado` / `'python' não é reconhecido` | Na versão portátil, confira se existe a pasta `ferramentas\python` ao lado do `atualizar_portal.bat`. Na instalação normal, reinstale o Python marcando "Add python.exe to PATH" |
| Windows avisa "O Windows protegeu o computador" ao abrir o .bat | Clique em **Mais informações → Executar assim mesmo**. Isso aparece porque o arquivo veio da internet |
| `Pasta não encontrada` | Copie de novo o caminho da barra de endereço e cole no `segredos.bat`, salvo em UTF-8 |
| `[FALTA] …` no conferir_pasta | Confira o nome do arquivo (ex.: `FATOS_RED_OUT26.xlsx`) e se está em .xlsx. Se as DIM_, o TOM ou o CPI ficam fora da TABELA_FATO, aponte o `DADOS_DIR` para a pasta `Prévia 2026` (a de cima) |
| Processamento muito lento | Faltou o "Sempre manter neste dispositivo" na pasta TABELA_FATO |
| `Não foi possível transformar as apresentações em imagem` | Instale o LibreOffice, ou rode com o PowerPoint fechado |
| `Defina SUPABASE_URL e SUPABASE_SERVICE_KEY` | Preencha o `segredos.bat` (parte 4, Configuração, passo 1) |
| Portal mostra "Portal sem conexão configurada" | Preencha o `config.js` e faça o Push de novo (parte 3.2) |
| Portal abre, mas diz "Ainda não há dados publicados" | Rode o `atualizar_portal.bat` |
| Gerente não consegue enviar | Confira o prazo em **Reunião**, e se o usuário tem a gerência marcada e a permissão "Baixar apresentações" |
| Projeto do Supabase "Paused" | No plano gratuito, o projeto pausa após cerca de 1 semana sem acesso. Entre no supabase.com e clique em **Restore**; nenhum dado é perdido |
