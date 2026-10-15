from supabase_client import supabase

# Tenta acessar cada tabela e ver o que acontece
tabelas = ["professores", "disciplinas", "turmas", "perfis", "avaliacoes"]

for t in tabelas:
    try:
        # Pega só 1 linha pra testar (não importa o conteúdo)
        resp = supabase.table(t).select("*").limit(1).execute()
        print(f"✅ {t}: existe ({len(resp.data)} linha(s) retornada(s))")
    except Exception as e:
        print(f"❌ {t}: erro -> {e}")