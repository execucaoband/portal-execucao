-- =====================================================================================
-- Portal de Indicadores de Merchandising – banco no Supabase
-- Rode este arquivo inteiro em: Supabase → SQL Editor → New query → Run
-- As permissões ficam no BANCO (Row Level Security): mesmo quem abrir o HTML e mexer no
-- navegador só recebe as gerências vinculadas e só baixa as apresentações permitidas.
-- =====================================================================================

-- ---------- tabelas ----------
create table if not exists public.perfis (
  id uuid primary key references auth.users(id) on delete cascade,
  nome text not null,
  email text not null,
  genero text not null default '' check (genero in ('', 'M', 'F')),
  perfil text not null default 'usuario' check (perfil in ('admin','usuario')),
  pode_ver boolean not null default true,
  pode_baixar boolean not null default true,
  ativo boolean not null default true,
  trocar_senha boolean not null default true,
  criado_em timestamptz not null default now()
);
create table if not exists public.gerencias (gc text primary key, nome_gerente text not null default '', genero text not null default '' check (genero in ('', 'M', 'F')));
alter table public.perfis add column if not exists genero text not null default '' check (genero in ('', 'M', 'F'));
alter table public.gerencias add column if not exists genero text not null default '' check (genero in ('', 'M', 'F'));   -- encerramento: M = Obrigado, F = Obrigada
create table if not exists public.usuario_gc (
  usuario_id uuid not null references public.perfis(id) on delete cascade,
  gc text not null references public.gerencias(gc) on update cascade,
  primary key (usuario_id, gc)
);
create table if not exists public.config (chave text primary key, valor jsonb);
create table if not exists public.portal_meta (id int primary key default 1, payload jsonb not null, publicado_em timestamptz not null default now());
create table if not exists public.dados_gc (gc text primary key references public.gerencias(gc), payload jsonb not null);
create table if not exists public.dados_empresa (id int primary key default 1, payload jsonb not null);
create table if not exists public.insights (mes text not null, escopo text not null, payload jsonb not null, primary key (mes, escopo));
create table if not exists public.ranking_gc (mes text not null, gc text not null, pts numeric not null, ice numeric, primary key (mes, gc));
create table if not exists public.envios (
  id bigserial primary key, gc text not null references public.gerencias(gc), ref text not null, versao int not null,
  caminho text not null, nome text not null, enviado_em timestamptz not null default now(),
  enviado_por uuid default auth.uid(), enviado_por_nome text, unique (gc, ref, versao)
);
create table if not exists public.auditoria (
  id bigserial primary key, quando timestamptz not null default now(),
  usuario uuid default auth.uid(), acao text not null, detalhe text
);

-- ---------- funções usadas pelas regras (security definer: leem o perfil sem esbarrar na própria RLS) ----------
create or replace function public.eh_admin() returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from perfis where id = auth.uid() and perfil = 'admin' and ativo) $$;
create or replace function public.minhas_gcs() returns setof text language sql stable security definer set search_path = public as $$
  select ug.gc from usuario_gc ug join perfis p on p.id = ug.usuario_id where p.id = auth.uid() and p.ativo $$;
create or replace function public.pode_ver() returns boolean language sql stable security definer set search_path = public as $$
  select coalesce((select pode_ver and ativo from perfis where id = auth.uid()), false) $$;
create or replace function public.pode_baixar() returns boolean language sql stable security definer set search_path = public as $$
  select coalesce((select pode_baixar and ativo from perfis where id = auth.uid()), false) $$;
create or replace function public.ranking_publico() returns boolean language sql stable security definer set search_path = public as $$
  select coalesce((select valor = 'true'::jsonb from config where chave = 'ranking_publico'), true) $$;
create or replace function public.slug_gc(t text) returns text language sql immutable as $$
  select regexp_replace(regexp_replace(t, '\.\s*', '_', 'g'), '\s+', '_', 'g') $$;
-- prazo de envio das apresentações finais: config 'prazo_envio' {abre, fecha} ou reabertura da gerência em config 'reabertas' {gc: até}
create or replace function public.prazo_aberto(g text) returns boolean language sql stable security definer set search_path = public as $$
  select coalesce((select now() between (valor->>'abre')::timestamptz and (valor->>'fecha')::timestamptz from config where chave = 'prazo_envio'), false)
      or coalesce((select now() <= (valor->>g)::timestamptz from config where chave = 'reabertas' and valor ? g), false) $$;
create or replace function public.pode_enviar(g text) returns boolean language sql stable security definer set search_path = public as $$
  select public.pode_baixar() and g in (select public.minhas_gcs()) and public.prazo_aberto(g) $$;
-- o próprio usuário só consegue desligar o aviso de "trocar senha" (não consegue mudar perfil nem permissões)
create or replace function public.senha_trocada() returns void language sql security definer set search_path = public as $$
  update perfis set trocar_senha = false where id = auth.uid() $$;

-- ---------- acesso da API (o Supabase às vezes não expõe tabelas novas automaticamente; a RLS abaixo é quem filtra) ----------
grant usage on schema public to anon, authenticated, service_role;
grant select, insert, update, delete on all tables in schema public to authenticated, service_role;
grant usage, select on all sequences in schema public to authenticated, service_role;
grant execute on all functions in schema public to authenticated, service_role;

-- ---------- RLS ----------
alter table public.perfis enable row level security;
alter table public.gerencias enable row level security;
alter table public.usuario_gc enable row level security;
alter table public.config enable row level security;
alter table public.portal_meta enable row level security;
alter table public.dados_gc enable row level security;
alter table public.dados_empresa enable row level security;
alter table public.insights enable row level security;
alter table public.ranking_gc enable row level security;
alter table public.auditoria enable row level security;
alter table public.envios enable row level security;

drop policy if exists perfis_ler on public.perfis;            create policy perfis_ler on public.perfis for select to authenticated using (id = auth.uid() or public.eh_admin());
drop policy if exists perfis_criar on public.perfis;          create policy perfis_criar on public.perfis for insert to authenticated with check (public.eh_admin());
drop policy if exists perfis_editar on public.perfis;         create policy perfis_editar on public.perfis for update to authenticated using (public.eh_admin()) with check (public.eh_admin());
drop policy if exists perfis_excluir on public.perfis;        create policy perfis_excluir on public.perfis for delete to authenticated using (public.eh_admin() and id <> auth.uid());

drop policy if exists ger_ler on public.gerencias;            create policy ger_ler on public.gerencias for select to authenticated using (true);
drop policy if exists ger_editar on public.gerencias;         create policy ger_editar on public.gerencias for update to authenticated using (public.eh_admin()) with check (public.eh_admin());

drop policy if exists ugc_ler on public.usuario_gc;           create policy ugc_ler on public.usuario_gc for select to authenticated using (usuario_id = auth.uid() or public.eh_admin());
drop policy if exists ugc_criar on public.usuario_gc;         create policy ugc_criar on public.usuario_gc for insert to authenticated with check (public.eh_admin());
drop policy if exists ugc_excluir on public.usuario_gc;       create policy ugc_excluir on public.usuario_gc for delete to authenticated using (public.eh_admin());

drop policy if exists cfg_ler on public.config;               create policy cfg_ler on public.config for select to authenticated using (public.eh_admin() or chave in ('ranking_publico', 'prazo_envio', 'reabertas'));
drop policy if exists cfg_criar on public.config;             create policy cfg_criar on public.config for insert to authenticated with check (public.eh_admin());
drop policy if exists cfg_editar on public.config;            create policy cfg_editar on public.config for update to authenticated using (public.eh_admin()) with check (public.eh_admin());

drop policy if exists meta_ler on public.portal_meta;         create policy meta_ler on public.portal_meta for select to authenticated using (true);
drop policy if exists dgc_ler on public.dados_gc;             create policy dgc_ler on public.dados_gc for select to authenticated
  using (public.eh_admin() or (public.pode_ver() and gc in (select public.minhas_gcs())));
drop policy if exists demp_ler on public.dados_empresa;       create policy demp_ler on public.dados_empresa for select to authenticated using (public.eh_admin());
drop policy if exists ins_ler on public.insights;             create policy ins_ler on public.insights for select to authenticated
  using (public.eh_admin() or (public.pode_ver() and escopo in (select public.minhas_gcs())));
drop policy if exists rk_ler on public.ranking_gc;            create policy rk_ler on public.ranking_gc for select to authenticated
  using (public.eh_admin() or (public.ranking_publico() and public.pode_ver()));
drop policy if exists aud_criar on public.auditoria;          create policy aud_criar on public.auditoria for insert to authenticated with check (usuario = auth.uid());
drop policy if exists aud_ler on public.auditoria;            create policy aud_ler on public.auditoria for select to authenticated using (public.eh_admin());
drop policy if exists env_ler on public.envios;              create policy env_ler on public.envios for select to authenticated using (public.eh_admin() or gc in (select public.minhas_gcs()));
drop policy if exists env_criar on public.envios;            create policy env_criar on public.envios for insert to authenticated with check (enviado_por = auth.uid() and public.pode_enviar(gc));
-- portal_meta, dados_gc, dados_empresa, insights e ranking_gc só recebem gravação da chave service_role (publicar_supabase.py)

-- ---------- apresentações (Storage privado) ----------
-- caminhos: EMPRESA/Resultado_Geral_SET26.pptx  ·  GC_AN/Merchandising_GCAN_SET26.pptx
insert into storage.buckets (id, name, public) values ('apresentacoes', 'apresentacoes', false) on conflict (id) do nothing;
drop policy if exists apres_baixar on storage.objects;
create policy apres_baixar on storage.objects for select to authenticated using (
  bucket_id = 'apresentacoes' and (
    public.eh_admin()
    or (public.pode_baixar() and (storage.foldername(name))[1] in (select public.slug_gc(g) from public.minhas_gcs() as g))
    or ((storage.foldername(name))[1] = 'FINAL' and (storage.foldername(name))[2] in (select public.slug_gc(g) from public.minhas_gcs() as g))
  ));
-- versões finais: FINAL/GC_AN/SET26_v2.pptx · o gerente só grava na pasta da sua gerência e só dentro do prazo (sem sobrescrever)
drop policy if exists apres_enviar on storage.objects;
create policy apres_enviar on storage.objects for insert to authenticated with check (
  bucket_id = 'apresentacoes' and (storage.foldername(name))[1] = 'FINAL'
  and exists (select 1 from public.minhas_gcs() as g where public.slug_gc(g) = (storage.foldername(name))[2] and public.pode_enviar(g))
);


-- planilhas do mês (aba Cargas): BASES/<tipo>/arquivo.xlsx · só administrador envia, substitui e exclui
drop policy if exists bases_criar on storage.objects;
create policy bases_criar on storage.objects for insert to authenticated with check (bucket_id = 'apresentacoes' and (storage.foldername(name))[1] = 'BASES' and public.eh_admin());
drop policy if exists bases_editar on storage.objects;
create policy bases_editar on storage.objects for update to authenticated using (bucket_id = 'apresentacoes' and (storage.foldername(name))[1] = 'BASES' and public.eh_admin()) with check (bucket_id = 'apresentacoes' and (storage.foldername(name))[1] = 'BASES' and public.eh_admin());
drop policy if exists bases_excluir on storage.objects;
create policy bases_excluir on storage.objects for delete to authenticated using (bucket_id = 'apresentacoes' and (storage.foldername(name))[1] = 'BASES' and public.eh_admin());

-- =====================================================================================
-- PRIMEIRO ADMINISTRADOR
-- 1) Supabase → Authentication → Users → Add user (e-mail + senha, marque "Auto Confirm User")
-- 2) troque o e-mail abaixo e rode:
--    insert into public.perfis (id, nome, email, perfil, trocar_senha)
--    select id, 'Administrador', email, 'admin', false from auth.users where email = 'seu.email@empresa.com.br';
-- Os demais usuários são criados pelo próprio portal (Painel Gerencial → Criar usuário).
-- =====================================================================================
