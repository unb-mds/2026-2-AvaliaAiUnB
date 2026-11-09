// Menu do topo: fecha ao clicar fora ou ao apertar Esc (o <details> já funciona sem JavaScript).
(function () {
    var menu = document.querySelector('.topo .menu');
    if (!menu) { return; }

    document.addEventListener('click', function (evento) {
        if (menu.open && !menu.contains(evento.target)) { menu.open = false; }
    });

    document.addEventListener('keydown', function (evento) {
        if (evento.key === 'Escape' && menu.open) {
            menu.open = false;
            menu.querySelector('summary').focus();
        }
    });
})();
