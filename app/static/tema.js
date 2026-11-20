/*
 * Alternância de tema. O escuro é o padrão (sem data-theme); o claro usa
 * <html data-theme="light">. A escolha fica em localStorage ("tema": "claro" ou
 * "escuro"). Este script é carregado no <head>, sem defer, para aplicar o tema
 * antes de a página aparecer e evitar o flash do tema errado. O clique usa
 * delegação de evento porque o botão ainda não existe quando o script roda.
 */
(function () {
    "use strict";

    var CHAVE = "tema";
    var raiz = document.documentElement;

    function lerEscolha() {
        try {
            return window.localStorage.getItem(CHAVE);
        } catch (erro) {
            return null;
        }
    }

    function salvarEscolha(valor) {
        try {
            window.localStorage.setItem(CHAVE, valor);
        } catch (erro) {
            // Armazenamento indisponível: a escolha vale só nesta página.
        }
    }

    function temaClaro() {
        return raiz.getAttribute("data-theme") === "light";
    }

    function aplicar(claro) {
        if (claro) {
            raiz.setAttribute("data-theme", "light");
        } else {
            raiz.removeAttribute("data-theme");
        }
    }

    function sincronizarBotoes() {
        var claro = temaClaro();
        var botoes = document.querySelectorAll(".botao-tema");
        for (var i = 0; i < botoes.length; i++) {
            botoes[i].setAttribute("aria-pressed", claro ? "true" : "false");
        }
    }

    // Roda já: "claro" ativa o tema claro; "escuro" ou ausência mantêm o padrão escuro.
    aplicar(lerEscolha() === "claro");

    document.addEventListener("click", function (evento) {
        var alvo = evento.target;
        var botao = alvo && alvo.closest ? alvo.closest(".botao-tema") : null;
        if (!botao) {
            return;
        }
        var claro = !temaClaro();
        raiz.classList.add("tema-interagido");
        aplicar(claro);
        salvarEscolha(claro ? "claro" : "escuro");
        sincronizarBotoes();
    });

    document.addEventListener("DOMContentLoaded", sincronizarBotoes);
})();
