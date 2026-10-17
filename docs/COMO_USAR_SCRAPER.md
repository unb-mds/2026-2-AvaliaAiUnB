# 🚀 Como Usar o Projeto

Este documento centraliza as instruções para configurar o ambiente, subir o banco de dados e executar o scraper.

## 1. Instalação de Dependências

Com o ambiente virtual (venv) ativado, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt

2. Credenciais do Supabase
Acesse o painel do Supabase e vá em Project Settings > API.

Copie a Project URL (ex: https://xxxx.supabase.co).

Copie a chave service_role.

Crie um arquivo .env na pasta raiz do projeto, e coloque as credenciais dessa fora:

SUPABASE_URL=credencial1
SUPABASE_SERVICE_KEY=credencial2
