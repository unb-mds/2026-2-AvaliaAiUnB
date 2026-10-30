"""Lógica de professores e avaliações: resolve o que as rotas exibem e registra avaliações."""
from flask import abort, request

from app.repositorio import MINIMO_AVALIACOES_RANKING, repositorios
from app.validacoes import CRITERIOS, validar_avaliacao


def criterios():
    return CRITERIOS


def catalogo(nome='', disciplina='', departamento=''):
    """Lista [(professor, disciplinas)] ordenada pela quantidade de avaliações."""
    return repositorios().professores.catalogo(nome, disciplina, departamento)


def departamentos():
    """Opções do filtro de departamento, vindas dos dados."""
    return repositorios().professores.listar_departamentos()


def carregar_ranking():
    return repositorios().professores.ranking(), MINIMO_AVALIACOES_RANKING


def carregar_perfil(professor_id):
    professores = repositorios().professores
    professor = professores.buscar_por_id(professor_id)
    if professor is None:
        abort(404)
    disciplinas = professores.listar_disciplinas(professor_id)
    origem = request.form if request.method == 'POST' else request.args
    identificador = origem.get('disciplina_id')
    if identificador is None:
        if request.method == 'POST':
            abort(400, description='Informe a disciplina avaliada.')
        disciplina = disciplinas[0] if disciplinas else None
    else:
        try:
            disciplina_id = int(identificador)
        except (ValueError, TypeError):
            abort(400, description='Disciplina inválida.')
        disciplina = next((d for d in disciplinas if d['id'] == disciplina_id), None)
        if disciplina is None:
            abort(404, description='Disciplina não vinculada ao professor.')
    return professor, disciplinas, disciplina


def indicadores(professor_id, disciplina_id):
    return repositorios().avaliacoes.calcular_medias(professor_id, disciplina_id)


def validar_notas(dados):
    return validar_avaliacao(dados, CRITERIOS)


def registrar_avaliacao(usuario, professor_id, disciplina_id, notas):
    """Grava a avaliação do usuário logado. False se ele já avaliou este par."""
    repos = repositorios()
    salvou = repos.avaliacoes.salvar(usuario['id'], professor_id, disciplina_id, notas)
    if salvou:
        repos.professores.invalidar_cache()   # a listagem ordena por total de avaliações
    return salvou


def listar_avaliacoes_usuario(usuario):
    return repositorios().avaliacoes.listar_por_usuario(usuario['id'])


def carregar_avaliacao_do_usuario(avaliacao_id, usuario):
    avaliacao = repositorios().avaliacoes.buscar_por_id_e_usuario(avaliacao_id, usuario['id'])
    if avaliacao is None:
        abort(404, description='Avaliação não encontrada.')
    return avaliacao


def editar_avaliacao(avaliacao_id, usuario, notas):
    repos = repositorios()
    atualizou = repos.avaliacoes.atualizar(avaliacao_id, usuario['id'], notas)
    if not atualizou:
        abort(404, description='Avaliação não encontrada.')
    repos.professores.invalidar_cache()
    return True


def excluir_avaliacao(avaliacao_id, usuario):
    repos = repositorios()
    excluiu = repos.avaliacoes.excluir(avaliacao_id, usuario['id'])
    if not excluiu:
        abort(404, description='Avaliação não encontrada.')
    repos.professores.invalidar_cache()
    return True
