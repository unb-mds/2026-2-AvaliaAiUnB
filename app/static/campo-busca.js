// Troca cada <select> dentro de .campo-busca por um campo digitável com sugestões
// (comparação de professores e disciplina do perfil).
// O <select> continua no formulário (e funciona sozinho se este script não rodar).
(function () {
    function normalizar(texto) {
        return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
    }

    document.querySelectorAll('.campo-busca').forEach(function (campo) {
        var select = campo.querySelector('select');
        var rotulo = campo.querySelector('label');
        if (!select || !rotulo) { return; }

        var opcoes = Array.prototype.filter.call(select.options, function (o) { return o.value !== ''; })
            .map(function (o) { return { id: o.value, texto: o.textContent.trim(), chave: normalizar(o.textContent) }; });

        var lista = document.createElement('datalist');
        lista.id = select.id + '-opcoes';
        opcoes.forEach(function (o) {
            var item = document.createElement('option');
            item.value = o.texto;
            lista.appendChild(item);
        });

        var entrada = document.createElement('input');
        entrada.type = 'search';
        entrada.id = select.id + '-busca';
        entrada.setAttribute('list', lista.id);
        entrada.autocomplete = 'off';
        var temVazia = Array.prototype.some.call(select.options, function (o) { return o.value === ''; });
        entrada.required = select.required || !temVazia;
        entrada.placeholder = select.getAttribute('data-placeholder') || 'Digite para buscar';
        ['aria-invalid', 'aria-describedby'].forEach(function (atributo) {
            if (select.hasAttribute(atributo)) { entrada.setAttribute(atributo, select.getAttribute(atributo)); }
        });

        var atual = opcoes.filter(function (o) { return o.id === select.value; })[0];
        if (atual) { entrada.value = atual.texto; }

        function localizar() {
            var chave = normalizar(entrada.value);
            if (!chave) { return null; }
            var exata = opcoes.filter(function (o) { return o.chave === chave; })[0];
            if (exata) { return exata; }
            var parecidas = opcoes.filter(function (o) { return o.chave.indexOf(chave) !== -1; });
            return parecidas.length === 1 ? parecidas[0] : null;
        }

        function sincronizar() {
            var achada = localizar();
            select.value = achada ? achada.id : '';
            entrada.setCustomValidity(entrada.value && !achada ? 'Escolha uma opção da lista de sugestões.' : '');
            return achada;
        }

        entrada.addEventListener('input', sincronizar);
        entrada.addEventListener('change', function () {
            var achada = sincronizar();
            if (achada) { entrada.value = achada.texto; }
        });

        select.required = false;
        select.hidden = true;
        rotulo.setAttribute('for', entrada.id);
        select.parentNode.insertBefore(entrada, select);
        select.parentNode.insertBefore(lista, select);
        sincronizar();
    });
})();
