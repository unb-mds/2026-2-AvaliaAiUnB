/*
 * Fundo animado da home: manchas azuis suaves e uma rede de pontos ligados por
 * linhas finas, em canvas 2D, sem bibliotecas. As cores vêm das variáveis CSS do
 * tema (base.css). Respeita prefers-reduced-motion (um único quadro parado),
 * pausa quando a aba está oculta ou o canvas sai da tela, e os pontos reagem
 * ao mouse apenas dentro da área do .hero (nunca em telas de toque).
 */
(function () {
    "use strict";

    var canvas = document.querySelector(".fundo-animado");
    if (!canvas || !canvas.getContext) {
        return;
    }
    var ctx = canvas.getContext("2d");
    if (!ctx) {
        return;
    }
    // Área de interação do mouse: o cabeçalho da página.
    var hero = document.querySelector(".hero") ||
        document.querySelector(".cabecalho-pagina") ||
        document.querySelector("main h1") ||
        document.querySelector("h1");
    // "normal" (home) ou "leve" (demais telas): menos pontos, linhas e opacidade.
    var leve = canvas.getAttribute("data-densidade") === "leve";

    var TOKEN_PONTOS = "--cor-principal";
    var TOKENS_MANCHAS = ["--cor-principal", "--cor-principal-fundo", "--cor-principal-hover"];
    var TOKEN_FUNDO = "--cor-fundo-suave";

    var ALFA_MANCHA = leve ? 0.18 : 0.35;  // opacidade máxima das manchas
    var ALFA_LINHA = leve ? 0.2 : 0.3;     // opacidade máxima das linhas (distância zero)
    var ALFA_PONTO = leve ? 0.5 : 0.65;
    var INTERVALO_QUADRO = 1000 / 30 - 4; // ~30 quadros por segundo
    var RAIO_MOUSE = 130;         // alcance da interação, em px
    var DESLOCAMENTO_MAX = 55;    // quanto um ponto é empurrado, em px
    var SUAVIDADE = 0.12;         // quão rápido o ponto acompanha o alvo

    // Cada mancha: posição média (0..1), raio relativo à largura, velocidade, fase e cor.
    var MANCHAS = [
        { x: 0.12, y: 0.35, raio: 0.4, vx: 0.045, vy: 0.06, fase: 0.0, cor: 0, alfa: 1.0 },
        { x: 0.5, y: 0.2, raio: 0.5, vx: 0.035, vy: 0.05, fase: 1.7, cor: 1, alfa: 1.0 },
        { x: 0.85, y: 0.4, raio: 0.42, vx: 0.05, vy: 0.04, fase: 3.1, cor: 2, alfa: 0.8 },
        { x: 0.3, y: 0.8, raio: 0.34, vx: 0.04, vy: 0.055, fase: 4.6, cor: 0, alfa: 0.8 },
        { x: 0.7, y: 0.85, raio: 0.36, vx: 0.055, vy: 0.04, fase: 5.5, cor: 1, alfa: 0.8 }
    ];

    var consultaMovimento = window.matchMedia
        ? window.matchMedia("(prefers-reduced-motion: reduce)")
        : null;
    var consultaMouse = window.matchMedia
        ? window.matchMedia("(hover: hover) and (pointer: fine)")
        : null;

    var coresManchas = [];
    var corPontos = null;
    var escalaAlfa = 1;
    var pontos = [];
    var largura = 0;
    var altura = 0;
    var naTela = true;
    var quadro = null;
    var ultimoQuadro = 0;
    var ultimoInstante = null;
    var tempo = 0; // segundos de animação acumulados
    var mouse = { ativo: false, x: 0, y: 0 };

    function reduzirMovimento() {
        return !!(consultaMovimento && consultaMovimento.matches);
    }

    function interacaoPermitida() {
        return !reduzirMovimento() && !!(consultaMouse && consultaMouse.matches);
    }

    // Converte "#rrggbb", "#rgb" ou "rgb(r g b / a)" em [r, g, b]; null se não entender.
    function lerCor(texto) {
        texto = (texto || "").trim();
        var m;
        if ((m = /^#([0-9a-f]{3})$/i.exec(texto))) {
            return [0, 1, 2].map(function (i) {
                return parseInt(m[1].charAt(i) + m[1].charAt(i), 16);
            });
        }
        if ((m = /^#([0-9a-f]{6})/i.exec(texto))) {
            return [0, 2, 4].map(function (i) {
                return parseInt(m[1].substr(i, 2), 16);
            });
        }
        if ((m = /^rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)/i.exec(texto))) {
            return [Number(m[1]), Number(m[2]), Number(m[3])];
        }
        return null;
    }

    function luminancia(rgb) {
        var c = rgb.map(function (v) {
            v = v / 255;
            return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
    }

    function atualizarCores() {
        var estilo = getComputedStyle(document.documentElement);
        coresManchas = TOKENS_MANCHAS.map(function (token) {
            return lerCor(estilo.getPropertyValue(token));
        }).filter(Boolean);
        corPontos = lerCor(estilo.getPropertyValue(TOKEN_PONTOS));
        // Em fundo claro, reduz a intensidade para não comprometer o contraste do texto.
        var fundo = lerCor(estilo.getPropertyValue(TOKEN_FUNDO));
        escalaAlfa = fundo && luminancia(fundo) > 0.5 ? 0.55 : 1;
    }

    function quantidadePontos() {
        if (largura < 600) {
            return leve ? 20 : 40;
        }
        if (largura < 1000) {
            return leve ? 25 : 55;
        }
        return leve ? 30 : 70;
    }

    function novoPonto() {
        var angulo = Math.random() * Math.PI * 2;
        var velocidade = 6 + Math.random() * 10; // px por segundo
        return {
            x: Math.random() * largura,
            y: Math.random() * altura,
            vx: Math.cos(angulo) * velocidade,
            vy: Math.sin(angulo) * velocidade,
            ox: 0,
            oy: 0,
            r: 1.1 + Math.random() * 1.2
        };
    }

    function ajustarPontos() {
        var alvo = quantidadePontos();
        while (pontos.length < alvo) {
            pontos.push(novoPonto());
        }
        if (pontos.length > alvo) {
            pontos.length = alvo;
        }
    }

    function ajustarTamanho() {
        var larguraAnterior = largura;
        var alturaAnterior = altura;
        var larguraTela = window.innerWidth || document.documentElement.clientWidth || 0;
        var dpr = Math.min(window.devicePixelRatio || 1, larguraTela < 600 ? 1.5 : 2);
        largura = canvas.clientWidth;
        altura = canvas.clientHeight;
        canvas.width = Math.max(1, Math.round(largura * dpr));
        canvas.height = Math.max(1, Math.round(altura * dpr));
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        if (larguraAnterior && alturaAnterior) {
            for (var i = 0; i < pontos.length; i++) {
                pontos[i].x *= largura / larguraAnterior;
                pontos[i].y *= altura / alturaAnterior;
            }
        }
        ajustarPontos();
    }

    function desenharManchas() {
        if (!coresManchas.length) {
            return;
        }
        var base = largura;
        for (var i = 0; i < MANCHAS.length; i++) {
            var m = MANCHAS[i];
            var cx = (m.x + 0.08 * Math.sin(tempo * m.vx * 2 + m.fase)) * largura;
            var cy = (m.y + 0.12 * Math.cos(tempo * m.vy * 2 + m.fase)) * altura;
            var raio = m.raio * base;
            var rgb = coresManchas[m.cor % coresManchas.length].join(",");
            var alfa = ALFA_MANCHA * m.alfa * escalaAlfa;
            var gradiente = ctx.createRadialGradient(cx, cy, 0, cx, cy, raio);
            gradiente.addColorStop(0, "rgba(" + rgb + "," + alfa + ")");
            gradiente.addColorStop(1, "rgba(" + rgb + ",0)");
            ctx.fillStyle = gradiente;
            ctx.fillRect(0, 0, largura, altura);
        }
    }

    function desenharRede() {
        if (!corPontos || !pontos.length) {
            return;
        }
        var rgb = corPontos.join(",");
        var limite = Math.min(150, Math.max(90, largura * 0.12));
        var limiteQuadrado = limite * limite;
        var maxLinhas = largura < 600 ? (leve ? 30 : 70) : (leve ? 60 : 140);
        var linhas = 0;

        ctx.lineWidth = 1;
        for (var i = 0; i < pontos.length && linhas < maxLinhas; i++) {
            var a = pontos[i];
            var ax = a.x + a.ox;
            var ay = a.y + a.oy;
            for (var j = i + 1; j < pontos.length && linhas < maxLinhas; j++) {
                var b = pontos[j];
                var dx = ax - (b.x + b.ox);
                var dy = ay - (b.y + b.oy);
                var d2 = dx * dx + dy * dy;
                if (d2 < limiteQuadrado) {
                    var alfa = ALFA_LINHA * escalaAlfa * (1 - Math.sqrt(d2) / limite);
                    ctx.strokeStyle = "rgba(" + rgb + "," + alfa.toFixed(3) + ")";
                    ctx.beginPath();
                    ctx.moveTo(ax, ay);
                    ctx.lineTo(b.x + b.ox, b.y + b.oy);
                    ctx.stroke();
                    linhas++;
                }
            }
        }

        ctx.fillStyle = "rgba(" + rgb + "," + (ALFA_PONTO * escalaAlfa).toFixed(3) + ")";
        for (var k = 0; k < pontos.length; k++) {
            var p = pontos[k];
            ctx.beginPath();
            ctx.arc(p.x + p.ox, p.y + p.oy, p.r, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function desenhar() {
        ctx.clearRect(0, 0, largura, altura);
        if (!largura || !altura) {
            return;
        }
        desenharManchas();
        desenharRede();
    }

    function atualizarPontos(dt) {
        var usaMouse = mouse.ativo && interacaoPermitida();
        for (var i = 0; i < pontos.length; i++) {
            var p = pontos[i];
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            if (p.x < 0 || p.x > largura) {
                p.vx = -p.vx;
                p.x = Math.min(Math.max(p.x, 0), largura);
            }
            if (p.y < 0 || p.y > altura) {
                p.vy = -p.vy;
                p.y = Math.min(Math.max(p.y, 0), altura);
            }

            var alvoX = 0;
            var alvoY = 0;
            if (usaMouse) {
                var dx = p.x - mouse.x;
                var dy = p.y - mouse.y;
                var d = Math.sqrt(dx * dx + dy * dy);
                if (d < RAIO_MOUSE && d > 0.01) {
                    var forca = 1 - d / RAIO_MOUSE;
                    forca = forca * forca * DESLOCAMENTO_MAX;
                    alvoX = (dx / d) * forca;
                    alvoY = (dy / d) * forca;
                }
            }
            p.ox += (alvoX - p.ox) * SUAVIDADE;
            p.oy += (alvoY - p.oy) * SUAVIDADE;
        }
    }

    function deveAnimar() {
        return naTela && document.visibilityState !== "hidden" && !reduzirMovimento();
    }

    function passo(agora) {
        quadro = null;
        if (!deveAnimar()) {
            return;
        }
        quadro = window.requestAnimationFrame(passo);
        if (agora - ultimoQuadro < INTERVALO_QUADRO) {
            return;
        }
        ultimoQuadro = agora;
        var dt = ultimoInstante === null ? 0 : Math.min((agora - ultimoInstante) / 1000, 0.1);
        ultimoInstante = agora;
        tempo += dt;
        atualizarPontos(dt);
        desenhar();
    }

    function iniciar() {
        if (quadro === null && deveAnimar()) {
            ultimoInstante = null; // retoma sem salto
            quadro = window.requestAnimationFrame(passo);
        }
    }

    function parar() {
        if (quadro !== null) {
            window.cancelAnimationFrame(quadro);
            quadro = null;
        }
    }

    function atualizarEstado() {
        if (deveAnimar()) {
            iniciar();
        } else {
            parar();
            if (reduzirMovimento()) {
                // Quadro estático: sem deslocamento causado pelo mouse.
                for (var i = 0; i < pontos.length; i++) {
                    pontos[i].ox = 0;
                    pontos[i].oy = 0;
                }
            }
            desenhar();
        }
    }

    // Mouse: só vale dentro do .hero e só com ponteiro fino (não em telas de toque).
    window.addEventListener("pointermove", function (evento) {
        if (evento.pointerType !== "mouse" || !hero || !interacaoPermitida()) {
            mouse.ativo = false;
            return;
        }
        var areaHero = hero.getBoundingClientRect();
        var dentro = evento.clientX >= areaHero.left && evento.clientX <= areaHero.right &&
            evento.clientY >= areaHero.top && evento.clientY <= areaHero.bottom;
        if (!dentro) {
            mouse.ativo = false;
            return;
        }
        var areaCanvas = canvas.getBoundingClientRect();
        mouse.x = evento.clientX - areaCanvas.left;
        mouse.y = evento.clientY - areaCanvas.top;
        mouse.ativo = true;
    }, { passive: true });

    document.documentElement.addEventListener("mouseleave", function () {
        mouse.ativo = false;
    });

    var redimensionando = false;
    window.addEventListener("resize", function () {
        if (redimensionando) {
            return;
        }
        redimensionando = true;
        window.requestAnimationFrame(function () {
            redimensionando = false;
            ajustarTamanho();
            if (quadro === null) {
                desenhar();
            }
        });
    });

    document.addEventListener("visibilitychange", atualizarEstado);

    if (consultaMovimento) {
        consultaMovimento.addEventListener("change", atualizarEstado);
    }

    if ("IntersectionObserver" in window) {
        new IntersectionObserver(function (entradas) {
            naTela = entradas[entradas.length - 1].isIntersecting;
            atualizarEstado();
        }).observe(canvas);
    }

    // Acompanha a troca de tema (atributo data-theme no <html>).
    if ("MutationObserver" in window) {
        new MutationObserver(function () {
            atualizarCores();
            if (quadro === null) {
                desenhar();
            }
        }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    }

    atualizarCores();
    ajustarTamanho();
    desenhar();
    atualizarEstado();
})();
