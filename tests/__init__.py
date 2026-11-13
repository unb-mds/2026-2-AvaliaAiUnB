import os

# Configura variáveis de ambiente globais para o ambiente de testes
os.environ.setdefault('SECRET_KEY', 'chave-secreta-super-segura-e-com-mais-de-32-caracteres-para-passar-na-validacao')
os.environ.setdefault('SUPABASE_URL', 'https://mock.supabase.co')
os.environ.setdefault('SUPABASE_SERVICE_KEY', 'mock-service-key')