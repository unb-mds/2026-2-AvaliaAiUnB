(() => {
    "use strict";

    const menu = document.querySelector(".menu-editorial");
    const navegacao = document.getElementById("menu-principal");
    function fecharMenu() {
        menu?.setAttribute("aria-expanded", "false");
        navegacao?.classList.remove("open");
        document.querySelector(".mobile-menu-backdrop")?.classList.remove("open");
    }
    menu?.addEventListener("click", () => {
        const aberto = menu.getAttribute("aria-expanded") !== "true";
        menu.setAttribute("aria-expanded", String(aberto));
        navegacao.classList.toggle("open", aberto);
        document.querySelector(".mobile-menu-backdrop")?.classList.toggle("open", aberto);
        if (aberto) navegacao.querySelector("a")?.focus();
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && menu?.getAttribute("aria-expanded") === "true") {
            fecharMenu();
            menu.focus();
        }
    });
    window.addEventListener("resize", fecharMenu);
    document.querySelector(".mobile-menu-backdrop")?.addEventListener("click", fecharMenu);
    for (const botao of document.querySelectorAll("[data-abrir-comparacao]")) {
        botao.addEventListener("click", () => {
            const painel = document.getElementById("opcoes-comparacao");
            if (!painel) return;
            painel.open = true;
            painel.scrollIntoView({ block: "start", behavior: "auto" });
            painel.querySelector("summary")?.focus();
        });
    }
    const barra = document.getElementById("reading-progress");
    const reduzirMovimento = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apontador = window.matchMedia("(hover: hover) and (pointer: fine)");

    let quadro;
    function desenhar() {
        quadro = undefined;
        if (!barra || reduzirMovimento.matches) return;
        const maximo = document.documentElement.scrollHeight - window.innerHeight;
        const progresso = maximo > 0 ? Math.max(0, Math.min(1, window.scrollY / maximo)) : 0;
        barra.style.transform = `scaleX(${progresso})`;
    }

    function agendar() {
        if (barra && !reduzirMovimento.matches && quadro === undefined) {
            quadro = requestAnimationFrame(desenhar);
        }
    }

    window.addEventListener("scroll", agendar, { passive: true });
    window.addEventListener("resize", agendar);
    reduzirMovimento.addEventListener("change", agendar);
    agendar();

    for (const alvo of document.querySelectorAll(".hero, .feature, .teacher, .compare-card")) {
        alvo.addEventListener("pointermove", (evento) => {
            if (reduzirMovimento.matches || !apontador.matches) return;
            const retangulo = alvo.getBoundingClientRect();
            alvo.style.setProperty("--hero-x", Math.round(evento.clientX - retangulo.left) + "px");
            alvo.style.setProperty("--hero-y", Math.round(evento.clientY - retangulo.top) + "px");
            alvo.style.setProperty("--mx", Math.round(evento.clientX - retangulo.left) + "px");
            alvo.style.setProperty("--my", Math.round(evento.clientY - retangulo.top) + "px");
        }, { passive: true });
    }
})();
