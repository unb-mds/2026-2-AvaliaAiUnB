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

// Busca unificada (professor, disciplina ou departamento) com autocompletar.
// Segue o padrão "combobox com listbox" da WAI-ARIA: setas navegam, Enter abre a
// sugestão ativa, Esc fecha; uma região "status" anuncia quantas sugestões há.
// Sem JavaScript o formulário continua funcionando (envia o termo para a Consulta).
(function () {
    var ESPERA_MS = 200;
    var MINIMO = 2;

    function urlInterna(url) {
        return typeof url === 'string' && url.charAt(0) === '/' && url.charAt(1) !== '/' &&
            url.charAt(1) !== '\\';
    }

    document.querySelectorAll('.campo-sugestoes').forEach(function (campo, indice) {
        var entrada = campo.querySelector('input');
        var endereco = campo.getAttribute('data-sugestoes');
        if (!entrada || !endereco || !window.fetch) { return; }
        var contexto = campo.getAttribute('data-contexto') || 'consulta';
        var base = entrada.id || ('busca-unificada-' + indice);

        var lista = document.createElement('ul');
        lista.id = base + '-sugestoes';
        lista.className = 'lista-sugestoes';
        lista.setAttribute('role', 'listbox');
        lista.setAttribute('aria-label', 'Sugestões');
        lista.hidden = true;

        var aviso = document.createElement('p');
        aviso.className = 'sr-only';
        aviso.setAttribute('role', 'status');
        aviso.setAttribute('aria-live', 'polite');

        entrada.setAttribute('role', 'combobox');
        entrada.setAttribute('aria-autocomplete', 'list');
        entrada.setAttribute('aria-expanded', 'false');
        entrada.setAttribute('aria-controls', lista.id);
        entrada.autocomplete = 'off';
        entrada.parentNode.insertBefore(lista, entrada.nextSibling);
        campo.appendChild(aviso);

        var sugestoes = [], ativa = -1, temporizador = null, pedido = 0, controle = null;

        function opcoes() { return lista.querySelectorAll('[role="option"]'); }

        function marcar(novo) {
            var itens = opcoes();
            if (itens[ativa]) { itens[ativa].setAttribute('aria-selected', 'false'); }
            ativa = novo;
            if (itens[ativa]) {
                itens[ativa].setAttribute('aria-selected', 'true');
                entrada.setAttribute('aria-activedescendant', itens[ativa].id);
                if (itens[ativa].scrollIntoView) { itens[ativa].scrollIntoView({ block: 'nearest' }); }
            } else {
                entrada.removeAttribute('aria-activedescendant');
            }
        }

        function fechar() {
            marcar(-1);
            lista.hidden = true;
            entrada.setAttribute('aria-expanded', 'false');
        }

        function abrir(sugestao) {
            if (sugestao && urlInterna(sugestao.url)) { window.location.assign(sugestao.url); }
        }

        function mostrar(novas, termo) {
            sugestoes = novas;
            ativa = -1;
            entrada.removeAttribute('aria-activedescendant');
            lista.textContent = '';
            novas.forEach(function (s, i) {
                var item = document.createElement('li');
                item.id = lista.id + '-' + i;
                item.className = 'sugestao';
                item.setAttribute('role', 'option');
                item.setAttribute('aria-selected', 'false');

                var tipo = document.createElement('span');
                tipo.className = 'sugestao-tipo sugestao-tipo-' + s.tipo;
                tipo.textContent = s.tipo_rotulo;
                var texto = document.createElement('span');
                texto.className = 'sugestao-texto';
                texto.textContent = s.texto;
                item.appendChild(tipo);
                item.appendChild(texto);
                if (s.detalhe) {
                    var detalhe = document.createElement('span');
                    detalhe.className = 'sugestao-detalhe';
                    detalhe.textContent = s.detalhe;
                    item.appendChild(detalhe);
                }
                // Lido pelo leitor de tela como "Professor: NOME, DEPARTAMENTO".
                item.setAttribute('aria-label', s.tipo_rotulo + ': ' + s.texto +
                    (s.detalhe ? ', ' + s.detalhe : ''));
                // mousedown não tira o foco do campo; o clique abre a sugestão.
                item.addEventListener('mousedown', function (evento) { evento.preventDefault(); });
                item.addEventListener('click', function () { abrir(s); });
                lista.appendChild(item);
            });
            if (novas.length) {
                lista.hidden = false;
                entrada.setAttribute('aria-expanded', 'true');
                aviso.textContent = novas.length + (novas.length === 1 ? ' sugestão' : ' sugestões') +
                    '. Use as setas para navegar e Enter para abrir.';
            } else {
                fechar();
                aviso.textContent = termo ? 'Nenhuma sugestão. Pressione Enter para buscar.' : '';
            }
        }

        function buscar() {
            var termo = entrada.value.trim();
            var numero = ++pedido;
            if (controle) { controle.abort(); controle = null; }
            if (termo.replace(/\s+/g, '').length < MINIMO) { mostrar([], ''); return; }
            controle = window.AbortController ? new AbortController() : null;
            var url = endereco + '?q=' + encodeURIComponent(termo) +
                '&contexto=' + encodeURIComponent(contexto);
            fetch(url, { headers: { Accept: 'application/json' }, credentials: 'same-origin',
                         signal: controle ? controle.signal : undefined })
                .then(function (resposta) { return resposta.ok ? resposta.json() : { sugestoes: [] }; })
                .then(function (dados) {
                    // Respostas antigas (de teclas anteriores) são descartadas.
                    if (numero === pedido && document.activeElement === entrada) {
                        mostrar(dados.sugestoes || [], termo);
                    }
                })
                .catch(function () { /* abortada ou sem rede: o formulário continua valendo */ });
        }

        entrada.addEventListener('input', function () {
            clearTimeout(temporizador);
            temporizador = setTimeout(buscar, ESPERA_MS);
        });

        entrada.addEventListener('keydown', function (evento) {
            var total = sugestoes.length;
            if (evento.key === 'ArrowDown' || evento.key === 'ArrowUp') {
                if (!total) { return; }
                evento.preventDefault();
                if (lista.hidden) {
                    lista.hidden = false;
                    entrada.setAttribute('aria-expanded', 'true');
                }
                var passo = evento.key === 'ArrowDown' ? 1 : -1;
                marcar(ativa === -1 ? (passo > 0 ? 0 : total - 1) : (ativa + passo + total) % total);
            } else if (evento.key === 'Enter') {
                if (!lista.hidden && ativa >= 0) {
                    evento.preventDefault();
                    abrir(sugestoes[ativa]);
                }
            } else if (evento.key === 'Escape') {
                if (!lista.hidden) {
                    evento.preventDefault();
                    fechar();
                }
            } else if (evento.key === 'Tab') {
                fechar();
            }
        });

        entrada.addEventListener('blur', fechar);
        entrada.addEventListener('focus', function () {
            if (sugestoes.length && entrada.value.trim()) {
                lista.hidden = false;
                entrada.setAttribute('aria-expanded', 'true');
            }
        });
    });
})();
