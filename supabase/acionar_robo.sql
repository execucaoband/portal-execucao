-- =====================================================================================
-- Aciona o robô (GitHub Actions) NA HORA em que o portal pede: planilha nova na aba Cargas,
-- botão "Processar agora", mudança no Painel ou "Reenviar aviso". Não depende do agendamento do GitHub.
-- Rode uma vez em: Supabase → SQL Editor → New query → Run.
-- A chave do GitHub fica guardada no cofre do Supabase (Vault) com o nome 'github_token'
-- (cadastre à parte: select vault.create_secret('SEU_TOKEN', 'github_token');).
-- =====================================================================================
create extension if not exists pg_net;

create or replace function public.acionar_robo() returns trigger
language plpgsql security definer set search_path = public, extensions as $$
declare tok text;
begin
  -- só quando o pedido acabou de ser feito (de "não" para "sim"): várias planilhas seguidas acionam uma vez
  if new.chave not in ('carga_pendente', 'pendente', 'processar_agora', 'aviso_email_forcar') then return new; end if;
  if new.valor is distinct from 'true'::jsonb then return new; end if;
  if tg_op = 'UPDATE' and old.valor = 'true'::jsonb then return new; end if;
  select decrypted_secret into tok from vault.decrypted_secrets where name = 'github_token' limit 1;
  if tok is null then return new; end if;   -- sem chave: fica para a conferência agendada
  perform net.http_post(
    url := 'https://api.github.com/repos/execucaoband/portal-execucao/actions/workflows/processar.yml/dispatches',
    headers := jsonb_build_object('Authorization', 'Bearer ' || tok, 'Accept', 'application/vnd.github+json',
                                  'X-GitHub-Api-Version', '2022-11-28', 'User-Agent', 'portal-execucao'),
    body := jsonb_build_object('ref', 'main', 'inputs', jsonb_build_object('forcar', 'false', 'origem', 'portal'))
  );
  return new;
end $$;

drop trigger if exists acionar_robo on public.config;
create trigger acionar_robo after insert or update of valor on public.config
  for each row execute function public.acionar_robo();
