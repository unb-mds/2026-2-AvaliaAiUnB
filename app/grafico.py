"""Geometria do gráfico de evolução das notas por semestre (issue #224).

O SVG é desenhado pelo template (perfil_professor.html) a partir das coordenadas
calculadas aqui, sem JavaScript nem `style` inline, para respeitar a CSP. As
coordenadas estão no sistema do viewBox (LARGURA x ALTURA); o CSS só escala.
"""

LARGURA = 320
ALTURA = 200
MARGEM_ESQUERDA = 30
MARGEM_DIREITA = 22
MARGEM_TOPO = 14
MARGEM_BASE = 34
NOTA_MINIMA = 1
NOTA_MAXIMA = 5
MAXIMO_SEMESTRES_GRAFICO = 6   # a tabela mostra todos; o gráfico, os mais recentes


def _arredondar(valor):
    return round(valor, 1)


def _y(nota):
    """Posição vertical de uma nota (1 embaixo, 5 em cima)."""
    altura_util = ALTURA - MARGEM_TOPO - MARGEM_BASE
    fracao = (nota - NOTA_MINIMA) / (NOTA_MAXIMA - NOTA_MINIMA)
    return _arredondar(ALTURA - MARGEM_BASE - fracao * altura_util)


def _x(indice, total):
    """Semestres igualmente espaçados; um só fica no centro."""
    largura_util = LARGURA - MARGEM_ESQUERDA - MARGEM_DIREITA
    if total == 1:
        return _arredondar(MARGEM_ESQUERDA + largura_util / 2)
    return _arredondar(MARGEM_ESQUERDA + indice * largura_util / (total - 1))


def montar_grafico(pontos):
    """Coordenadas do gráfico de linha.

    `pontos` é uma lista ordenada de dicts com 'rotulo' (ex.: '2026/1'), 'valor'
    (nota de 1 a 5) e 'quantidade'. Pontos sem valor são ignorados e só os
    MAXIMO_SEMESTRES_GRAFICO mais recentes entram. Devolve None sem pontos.
    """
    pontos = [p for p in pontos if p.get('valor') is not None][-MAXIMO_SEMESTRES_GRAFICO:]
    if not pontos:
        return None
    total = len(pontos)
    marcados = [{**p, 'x': _x(i, total), 'y': _y(p['valor'])} for i, p in enumerate(pontos)]
    caminho = ' '.join(f"{'M' if i == 0 else 'L'}{p['x']},{p['y']}"
                       for i, p in enumerate(marcados))
    grade = [{'nota': n, 'y': _y(n)} for n in range(NOTA_MINIMA, NOTA_MAXIMA + 1)]
    return {
        'largura': LARGURA, 'altura': ALTURA,
        'x_inicio': MARGEM_ESQUERDA, 'x_fim': LARGURA - MARGEM_DIREITA,
        'y_rotulos': ALTURA - MARGEM_BASE + 20,
        'pontos': marcados, 'caminho': caminho, 'grade': grade,
    }
