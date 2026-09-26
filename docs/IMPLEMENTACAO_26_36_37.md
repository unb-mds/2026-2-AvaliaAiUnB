# Implementação de #26, #36 e #37

Base revisada: `main` em `85f6281`, issues abertas e fechadas, seus comentários,
histórico Git, prints das issues #2 e #8 e o documento de requisitos fornecido.
As issues #32, #34 e #35 estão fechadas, mas o PR #50 ainda estava aberto na revisão.
Os templates `perfil_professor.html` e `avaliacao.html` foram aproveitados daquele
PR (`34d9754`), com integração e ajustes descritos abaixo. Seu banco e arquivos
compilados não foram incorporados. Ao integrar o PR #50, preservar estes ajustes
nos dois templates; não substituir o banco de dados pelos arquivos daquele PR.

## Decisões e compatibilidade

- #26: nome obrigatório após remover espaços externos, e-mail válido e único
  sem diferenciar maiúsculas, senha mínima de oito caracteres e confirmação.
  O mínimo e a confirmação aparecem no print de cadastro da issue #2.
  As senhas continuam usando o hash existente. A senha não é aparada nem
  devolvida no HTML. Clientes de cadastro precisam enviar `confirmar_senha`.
  Formulários recebem mensagens em HTML; clientes existentes sem `Accept`
  continuam recebendo JSON. Validação retorna 400, duplicidade 409; sucesso
  retorna 201 para JSON e 200 para a página HTML de confirmação.
- #36: média aritmética independente para cada critério por professor e disciplina.
  `AVG` é calculado na consulta, de modo que alterações e exclusões no banco
  se refletem imediatamente. Arredondamento só na tela, com uma casa decimal.
  Nenhuma avaliação retorna quantidade zero e médias `None`.
- #37: perfil público em `/professores/<id>?disciplina_id=<id>`, seletor de
  disciplina, cinco indicadores, quantidade e estados vazios. `/perfil` continua
  sendo a conta autenticada do usuário, como na implementação de sessão.
- O documento fornecido define Didática, Organização, Dificuldade,
  Disponibilidade e Avaliação Geral. O PR #50 usava Clareza no lugar de Avaliação
  Geral, e os prints tinham ambos. Foi seguido o documento textual mais recente;
  nenhuma nota de Clareza é convertida em outro critério. Dificuldade não é usada
  para calcular qualidade ou a avaliação geral, que é uma nota independente.
- Migração aditiva em `inicializar_banco()`: mantém `nota` como avaliação geral,
  acrescenta os demais critérios e `disciplina_id`, preserva `comentario` e todos
  os registros antigos. Não inventa disciplina nem critérios para notas legadas.
  Registros incompletos ou com notas fora de 1–5 não entram nos indicadores.
- Índice único por usuário/professor/disciplina e validação no servidor impedem
  duplicatas e notas inválidas. A consulta pública nunca retorna autor ou comentário.
- Integração mínima necessária: catálogo relacional consultável, repositório,
  rota GET/POST `/avaliar/<id>` protegida pelo controlador de sessão existente,
  validação de todos os critérios e da associação professor/disciplina.

## Dependências que permanecem com a equipe

O catálogo real e a busca de professores/disciplinas (#29–#31) não estavam
implementados na `main`. Foram criadas apenas as tabelas e consultas necessárias
ao perfil. A equipe precisa alimentar `professores`, `disciplinas` e
`professor_disciplinas` com dados reais pela importação planejada. Sem catálogo,
um ID desconhecido retorna 404; não são criados professores fictícios em produção.
Não foram implementados ranking, favoritos, importação SIGAA, recuperação de
senha, nem interfaces para editar/excluir avaliações. O login existente ainda
responde JSON após o envio do formulário; sua evolução visual permanece em #27.

## Executar e verificar

Na raiz desta cópia do repositório:

```powershell
python -m pip install -r requirements.txt
python -B -m unittest discover -s app -t . -p "test*.py" -v
python demo.py
```

A demonstração usa banco temporário e dados claramente fictícios, sem alterar
`banco.db`. Abrir `http://localhost:5050/professores/1` e `/cadastro`. A segunda
disciplina permite ver o estado sem avaliações. Para testar envio, criar uma
conta, entrar em `/login` e acessar novamente o perfil no mesmo navegador.
O cookie Secure original foi preservado: usar `localhost` na demonstração e
HTTPS em produção. O comando de produção/desenvolvimento existente é `python run.py`.

Para outra base isolada, usar `create_app({'DATABASE': caminho})`.

## Validação

36 testes passaram, incluindo o teste anterior da equipe. Cobertura: entradas
de cadastro, mensagens HTML/JSON, hash, duplicidade, login/sessão/logout,
migração idempotente sem perda de registros, médias e separação por disciplina,
estado vazio, anonimato e submissão até o perfil com indicadores atualizados.
Os testes usam bancos temporários. `banco.db` versionado permanece intacto.

## Preparar o envio

As alterações estão na branch local `feat/cadastro-medias-indicadores` desta
cópia. Nenhum push ou merge foi realizado. Revisar as dependências acima no PR.

```powershell
git status
git add .gitignore requirements.txt demo.py app/__init__.py app/database.py app/repositorio.py app/validacoes.py app/routes/auth_routes.py app/routes/professor_routes.py app/static/indicadores.css app/templates/cadastro.html app/templates/perfil_professor.html app/templates/avaliacao.html app/test_implementacao.py docs/IMPLEMENTACAO_26_36_37.md
git commit -m "feat: valida cadastro e integra medias por disciplina ao perfil"
git push -u origin feat/cadastro-medias-indicadores
```

Título sugerido do PR: `Valida cadastro e exibe médias por disciplina (#26, #36, #37)`.
Informar no PR que os dois templates incorporam e adaptam o trabalho do PR #50.
