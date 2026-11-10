# Portal Execução · Indicadores de Merchandising 2026

Portal web (HTML) com login, permissões por gerência e download das apresentações. Os dados ficam no **Supabase**. O cálculo é feito na máquina de processamento, a partir das planilhas da pasta TABELA_FATO.

```
planilhas (sua máquina) ──► atualizar_portal.bat ──► Supabase (banco + apresentações) ◄── index.html (GitHub Pages)
```

| Arquivo | Para que serve |
|---|---|
| `index.html` | O portal. Não leva dados dentro: tudo vem do Supabase depois do login. |
| `config.js` | URL do Supabase e chave **anon**. É o único arquivo que você edita para ligar o portal. |
| `supabase/schema.sql` | Cria as tabelas, as regras de acesso (RLS) e o bucket privado das apresentações. |
| `supabase/publicar_supabase.py` | Envia ao Supabase os resultados calculados na sua máquina. |
| Aba **Cargas** do portal | O administrador envia as planilhas do mês pelo navegador. Elas ficam na pasta privada `BASES/` do Supabase e o `atualizar_portal.bat` baixa sozinho. O OneDrive passa a ser opcional. |
| `reduzir_sovi.bat` | Gera o SOVI resumido de cada mês (menos de 1 MB, mesmo resultado) e envia ao Supabase, para outras máquinas não precisarem dos brutos. |
| `conferir_pasta.bat` | Confere se a pasta do OneDrive tem todas as planilhas, com o nome certo e baixadas no computador. |
| `atualizar_portal.bat` | A atualização mensal faz três passos: <br>1. traz a configuração do portal; <br>2. calcula os resultados (inclusive o SOVI bruto); <br>3. publica no Supabase. |
| `segredos.exemplo.bat` | Modelo do `segredos.bat`, que guarda a chave **service_role** e a pasta das planilhas. O `segredos.bat` não vai para o GitHub. |
| `gerador/` | Regras de cálculo validadas contra o Power BI e geração das apresentações (PPT). |
| `dados/config/` | Configuração inicial: pesos, supervisores, gerentes comerciais e agradecimentos (Obrigado/Obrigada). Depois da primeira carga, quem manda é o Painel Gerencial. |

> **Para colocar no ar, siga o [PASSO_A_PASSO.md](PASSO_A_PASSO.md).** Ele cobre OneDrive, Supabase, GitHub, computador de processamento e rotina do mês.

## 1. Supabase (uma vez)

1. Crie o projeto em [supabase.com](https://supabase.com). O plano free atende.
2. Vá em **SQL Editor → New query**, cole o conteúdo de `supabase/schema.sql` e clique em **Run**. Pode rodar de novo sempre que atualizar o arquivo, porque ele não apaga nada.
3. Crie o seu usuário em **Authentication → Users → Add user**: e-mail e senha, com **Auto Confirm User** marcado.
4. Torne esse usuário administrador. No SQL Editor, troque o e-mail e rode:
   ```sql
   insert into public.perfis (id, nome, email, genero, perfil, trocar_senha)
   select id, 'Seu Nome', email, 'M', 'admin', false from auth.users where email = 'seu.email@empresa.com.br';
   ```
5. Em **Authentication → Sign In / Providers → Email**:
   - deixe o provedor Email ativo;
   - desmarque **Confirm email**.

   Quem cria os usuários é o administrador, e o e-mail padrão do Supabase só envia poucas mensagens por hora. Assim o usuário já entra com a senha inicial.
6. Configure as URLs em **Authentication → URL Configuration**. Em **Site URL**, coloque o endereço do portal no GitHub Pages (passo 3), que é para onde vão os links de confirmação e de troca de senha.
7. Pegue as chaves em **Project Settings → API**:
   - **Project URL** e chave **anon public**: vão no `config.js`.
   - **Project URL** e chave **service_role**: vão no `segredos.bat`, na máquina de processamento. Nunca coloque a service_role no HTML nem no GitHub.

## 2. Máquina de processamento (uma vez)

1. Instale o Python 3.11 ou mais novo (marque "Add to PATH") e o Node.js LTS.
2. Clone ou baixe este repositório.
3. Rode `instalar_dependencias.bat`.
4. Copie `segredos.exemplo.bat` para `segredos.bat` e preencha o arquivo.

## 3. Publicar o portal no GitHub Pages

1. Edite o `config.js` com a URL e a chave anon e faça o commit.
2. No GitHub, vá em **Settings → Pages → Build and deployment**. Em Source, escolha **Deploy from a branch**; depois escolha a branch `main` e a pasta `/ (root)`.
3. O endereço fica `https://SEU-USUARIO.github.io/portal-indicadores-merchandising/`.

GitHub Pages em repositório **privado** exige um plano pago do GitHub. Sem plano pago, há duas saídas:
- deixar o repositório público: nele só há código e configuração, sem dados nem senhas, porque os resultados ficam no Supabase protegidos por login;
- publicar o mesmo `index.html` + `config.js` na Vercel, na Netlify ou no Cloudflare Pages, que hospedam de graça a partir de um repositório privado.

## Todo mês

1. Coloque as planilhas nas pastas de sempre.
2. Rode `atualizar_portal.bat`.

As planilhas brutas, inclusive as do SOVI, não sobem para a nuvem: só os resultados e as apresentações.

## Apresentações sem edição dos dados

Nas apresentações exportadas, gráficos, tabelas e números são salvos **como imagem**:
- ninguém altera os valores;
- ninguém abre a planilha que o PowerPoint guarda dentro dos gráficos, porque ela é apagada do arquivo.

Os slides **Plano de ação** continuam editáveis, para a gerência preencher.

As imagens são geradas pelo **PowerPoint** instalado no Windows, com a aparência idêntica. Sem PowerPoint, o gerador usa o **LibreOffice**, que precisa estar instalado. Para forçar um dos dois, use `set "PPT_RENDER=powerpoint"` ou `set "PPT_RENDER=libreoffice"` no `segredos.bat`.

## Usuários e permissões

Os usuários são criados no próprio portal, em **Painel Gerencial → Criar usuário**:

1. Informe o nome, o e-mail e o agradecimento: **Obrigado** (homem) ou **Obrigada** (mulher).
2. Escolha o nível de acesso.
3. Marque as gerências.
4. Defina as permissões.

O usuário entra com o e-mail e a senha inicial definida no cadastro e, no primeiro acesso, troca a senha.

O nome e o agradecimento do usuário passam a valer para as gerências vinculadas. Isso afeta:
- a capa e a tela final das apresentações;
- o ranking.

O agradecimento do resumo executivo da empresa fica em **Configurações**.

As regras ficam no banco (RLS), e não no HTML:
- **Usuário:** lê só as gerências vinculadas. Só baixa do Storage as pastas dessas gerências, e só se tiver a permissão "Baixar apresentações". Com duas ou mais gerências, baixa tudo num único .zip.
- **Administrador:** lê tudo, baixa o resumo executivo e todas as gerências (.zip), e é o único que grava usuários, gerentes, pesos, supervisores e configurações.

As mudanças feitas no Painel (nomes, Obrigado/Obrigada, pesos, supervisores) entram nas apresentações na próxima execução do `atualizar_portal.bat`.
