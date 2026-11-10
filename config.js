// Configuração do portal (Supabase → Project Settings → API).
// A chave "anon" (pública) pode ficar aqui: quem protege os dados são as regras de acesso (RLS) do supabase/schema.sql.
// NUNCA coloque aqui a chave "service_role" — ela fica só no segredos.bat da máquina de processamento.
window.PORTAL_CONFIG = {
  SUPABASE_URL: "https://edcyzjpmgonkicbyfurb.supabase.co",
  SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVkY3l6anBtZ29ua2ljYnlmdXJiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQyNDE4MzUsImV4cCI6MjEwOTgxNzgzNX0.LtGXI0n1R6_y5WTM0hDyv6Lh4NHTbOhGz4NYhuyUT_8",
  BUCKET: "apresentacoes",
};
