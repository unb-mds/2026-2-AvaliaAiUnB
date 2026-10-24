import re
import sys
import time
from collections import namedtuple
from pathlib import Path

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    UnexpectedAlertPresentException,
    StaleElementReferenceException,
    InvalidSessionIdException,
    WebDriverException,
)

from cli_sigaa import montar_parser
from persistencia_sigaa import (
    salvar_disciplinas,
    salvar_professores,
    salvar_turmas,
)
from resumo_sigaa import Resumo
from texto_sigaa import (
    UnidadeInvalidaError,
    contar_a_definir,
    extrair_docentes,
    professores_em_varias_unidades,
    validar_unidade,
)
from turmas_sigaa import montar_payload_turmas

# Status de uma busca por unidade
OK = "ok"
VAZIO = "vazio"  # o SIGAA respondeu, mas sem turmas: não é falha, não repete
FALHA = "falha"  # erro técnico (alerta, timeout, sessão): vale tentar de novo

Resultado = namedtuple(
    "Resultado",
    "status motivo professores disciplinas turmas resumo",
    defaults=("", (), (), (), None),
)

SELETOR_LINHAS = "tr.linhaPar, tr.linhaImpar"
# Trechos (em minúsculas) das mensagens de "nenhum resultado" do SIGAA
# Possíveis controles de paginação (a listagem hoje vem inteira em uma página)
SELETOR_PAGINACAO = (
    ".rich-datascr, .paginacao, a[title*='róxima' i], a[title*='next' i]"
)
MENSAGENS_SEM_RESULTADO = (
    "nenhum resultado",
    "nenhuma turma",
    "não foram encontrad",
    "nao foram encontrad",
)


class SigaaScraper:
    def __init__(self, headless=False, pausa=1.0):
        self.headless = headless
        self.pausa = pausa
        self.url = "https://sigaa.unb.br/sigaa/public/turmas/listar.jsf"
        self.unidade_atual = ""
        self._criar_driver()

    def _criar_driver(self):
        options = uc.ChromeOptions()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        # 🔥 Desabilita cache do navegador (evita enviar página antiga)
        options.add_argument("--disable-application-cache")
        options.add_argument("--disk-cache-size=0")

        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)

    # ---------- utilidades ----------

    def _fechar_alertas(self):
        """Fecha qualquer alerta aberto. SEMPRE chamado primeiro em excepts."""
        try:
            alert = self.driver.switch_to.alert
            print(f"[!] Alerta detectado: {alert.text}")
            alert.accept()
            return True
        except Exception:
            return False

    def _ha_alerta(self) -> bool:
        """Só verifica se há alerta aberto (sem fechá-lo)."""
        try:
            _ = self.driver.switch_to.alert.text
            return True
        except Exception:
            return False

    def _limpar_cache(self):
        """Limpa o cache do navegador via CDP."""
        try:
            self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
            print("[*] Cache do navegador limpo.")
        except Exception as e:
            print(f"[!] Não consegui limpar cache: {e}")

    def _sessao_viva(self) -> bool:
        try:
            _ = self.driver.current_url
            return True
        except (InvalidSessionIdException, WebDriverException):
            return False

    def _salvar_debug(self, motivo: str = "falha"):
        """Salva screenshot + HTML da página atual para debug (pasta debug/)."""
        try:
            pasta = Path("debug")
            pasta.mkdir(exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            unidade = re.sub(r"\W+", "_", self.unidade_atual).strip("_")
            nome = f"{motivo}_{unidade}_{timestamp}" if unidade else f"{motivo}_{timestamp}"

            # Tenta fechar alerta primeiro pra poder acessar a página
            self._fechar_alertas()

            caminho_png = pasta / f"{nome}.png"
            try:
                self.driver.save_screenshot(str(caminho_png))
                print(f"[DEBUG] Screenshot: {caminho_png.resolve()}")
            except Exception:
                pass

            caminho_html = pasta / f"{nome}.html"
            try:
                with open(caminho_html, "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print(f"[DEBUG] HTML: {caminho_html.resolve()}")
            except Exception:
                pass

            try:
                print(f"[DEBUG] URL atual: {self.driver.current_url}")
                print(f"[DEBUG] Título: {self.driver.title}")
            except Exception:
                pass
        except Exception as e:
            print(f"[!] Erro ao salvar debug: {e}")

    # ---------- formulário ----------

    def _select_depto(self) -> Select:
        return Select(self.driver.find_element(By.ID, "formTurma:inputDepto"))

    def _abrir_formulario(self):
        """Abre o formulário já com Graduação selecionada e as unidades carregadas."""
        print(f"[*] Acessando {self.url}...")
        self.driver.get(self.url)

        self.wait.until(
            EC.element_to_be_clickable((By.ID, "formTurma:inputNivel"))
        )
        self._fechar_alertas()

        Select(
            self.driver.find_element(By.ID, "formTurma:inputNivel")
        ).select_by_value("G")
        print("[*] Nível selecionado: Graduação")

        # A troca de nível recarrega a lista de unidades via AJAX
        self.wait.until(lambda d: len(self._select_depto().options) > 1)

    def listar_unidades(self, tentativas=3):
        """Unidades de graduação do formulário, como [(value, texto)]."""
        for i in range(1, tentativas + 1):
            self._fechar_alertas()
            try:
                self._abrir_formulario()
                unidades = []
                for opt in self._select_depto().options:
                    valor = (opt.get_attribute("value") or "").strip()
                    if not valor:
                        continue
                    try:
                        unidades.append((valor, validar_unidade(opt.text)))
                    except UnidadeInvalidaError:
                        continue  # placeholder "-- SELECIONE --"
                print(f"[*] {len(unidades)} unidades de graduação no formulário.")
                return unidades
            except Exception as e:
                print(f"[!] Falha ao listar unidades (tentativa {i}/{tentativas}): {e}")
                self._salvar_debug("listar_unidades")
                if i < tentativas:
                    self._reiniciar_se_preciso()
        return []

    def _reiniciar_se_preciso(self):
        time.sleep(3)
        if not self._sessao_viva():
            print("[*] Sessão morreu. Recriando driver...")
            try:
                self.driver.quit()
            except Exception:
                pass
            self._criar_driver()

    # ---------- busca por unidade ----------

    def buscar_unidade(self, ano, periodo, unidade_value, unidade_texto="", tentativas=3):
        """
        Busca uma unidade. Falha técnica reinicia TODO o fluxo (até N vezes);
        resposta sem turmas não repete. Unidade inexistente propaga
        UnidadeInvalidaError sem retry.
        """
        self.unidade_atual = unidade_texto or unidade_value
        resultado = Resultado(FALHA, "sem tentativas")

        for i in range(1, tentativas + 1):
            print(f"\n{'='*55}")
            print(f"[*] {self.unidade_atual} — TENTATIVA {i}/{tentativas}")
            print(f"{'='*55}")

            self._fechar_alertas()
            if i > 1:
                self._limpar_cache()

            resultado = self._buscar(ano, periodo, unidade_value)
            if resultado.status != FALHA:
                return resultado

            print(f"[!] Tentativa {i} falhou: {resultado.motivo}")
            if i < tentativas:
                self._reiniciar_se_preciso()

        print("[!] Todas as tentativas falharam.")
        return resultado

    def _buscar(self, ano, periodo, unidade_value):
        """Converte qualquer exceção em Resultado(FALHA) para o retry de cima."""
        try:
            return self._buscar_interno(ano, periodo, unidade_value)

        except UnidadeInvalidaError:
            self._fechar_alertas()
            raise

        except UnexpectedAlertPresentException:
            # 🔥 PRIMEIRA coisa: fechar o alerta
            self._fechar_alertas()
            self._salvar_debug("alerta_sessao")
            return Resultado(FALHA, "alerta inesperado (sessão do servidor expirada)")

        except InvalidSessionIdException:
            return Resultado(FALHA, "sessão do navegador caiu")

        except TimeoutException:
            self._fechar_alertas()
            self._salvar_debug("timeout")
            return Resultado(FALHA, "timeout esperando a página")

        except WebDriverException as e:
            self._fechar_alertas()
            return Resultado(FALHA, f"erro do WebDriver: {str(e).splitlines()[0]}")

        except Exception as e:
            self._fechar_alertas()
            return Resultado(FALHA, f"erro inesperado: {e}")

    def _buscar_interno(self, ano, periodo, unidade_value):
        if not unidade_value:
            raise UnidadeInvalidaError("Nenhuma unidade informada para a busca.")

        # 1. Nível: Graduação (e lista de unidades carregada)
        self._abrir_formulario()

        # 2. Unidade (o departamento gravado vem do texto da opção selecionada)
        try:
            self._select_depto().select_by_value(unidade_value)
        except NoSuchElementException:
            self._salvar_debug("unidade_nao_encontrada")
            raise UnidadeInvalidaError(
                f"Unidade com value {unidade_value!r} não existe no formulário."
            )
        print(f"[*] Unidade selecionada por value: {unidade_value}")

        # O JSF pode re-renderizar o select: espera a seleção se firmar
        self.wait.until(
            lambda d: self._select_depto().first_selected_option.get_attribute("value")
            == unidade_value
        )
        departamento = validar_unidade(self._select_depto().first_selected_option.text)
        print(f"[*] Departamento (unidade selecionada): {departamento}")

        # 3. Ano e período
        ano_input = self.driver.find_element(By.ID, "formTurma:inputAno")
        ano_input.clear()
        ano_input.send_keys(ano)
        Select(
            self.driver.find_element(By.ID, "formTurma:inputPeriodo")
        ).select_by_value(periodo)
        print(f"[*] Ano/Período: {ano}/{periodo}")
        self._fechar_alertas()

        # 4. Buscar
        botao_buscar = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='Buscar']"))
        )
        botao_buscar.click()
        print("[*] Clique em Buscar enviado. Aguardando resultado...")

        # 5. Uma espera só por: linhas de turma, mensagem de "nenhum resultado" ou alerta
        resposta = self.wait.until(self._resposta_da_busca)

        if resposta == "alerta":
            self._fechar_alertas()
            return Resultado(FALHA, "alerta após Buscar (sessão do servidor expirada)")
        if resposta == "vazio":
            print("[*] O SIGAA respondeu sem turmas para esta unidade.")
            return Resultado(VAZIO, "sem turmas")

        self._avisar_se_paginada()

        # 6. Extrair
        parcial = Resumo()
        professores, disciplinas, turmas = self._extrair_tudo(
            ano, periodo, departamento, parcial
        )
        if not professores and not disciplinas:
            self._salvar_debug("extracao_vazia")
            return Resultado(FALHA, "linhas presentes, mas nada foi extraído")

        print(
            f"[*] Encontrados: {len(professores)} professores, "
            f"{len(disciplinas)} disciplinas, {len(turmas)} turmas."
        )
        return Resultado(OK, "", professores, disciplinas, turmas, parcial)

    def _resposta_da_busca(self, driver):
        """Condição de espera: 'alerta', 'linhas', 'vazio' ou False (ainda carregando)."""
        if self._ha_alerta():
            return "alerta"
        if driver.find_elements(By.CSS_SELECTOR, SELETOR_LINHAS):
            return "linhas"
        corpo = driver.find_element(By.TAG_NAME, "body").text.lower()
        if any(msg in corpo for msg in MENSAGENS_SEM_RESULTADO):
            return "vazio"
        return False

    def _avisar_se_paginada(self):
        """Só registra no log se achar algum controle de paginação."""
        try:
            controles = self.driver.find_elements(By.CSS_SELECTOR, SELETOR_PAGINACAO)
        except WebDriverException:
            return
        if controles:
            print(
                f"[!] Possível paginação ({len(controles)} controle(s) encontrado(s)): "
                "a extração lê só a página atual. Confira o HTML em debug/."
            )
            self._salvar_debug("paginacao")

    # ---------- extração ----------

    def _extrair_tudo(self, ano: str, periodo: str, departamento: str, resumo: Resumo):
        professores_dict = {}
        disciplinas_dict = {}
        turmas_list = []
        disciplina_atual = None

        linhas = self.driver.find_elements(
            By.CSS_SELECTOR, "tr.agrupador, tr.linhaPar, tr.linhaImpar"
        )

        for linha in linhas:
            try:
                classes = linha.get_attribute("class") or ""
            except StaleElementReferenceException:
                resumo.registrar_linha_pulada("stale")
                continue

            if "agrupador" in classes:
                try:
                    span = linha.find_element(By.CSS_SELECTOR, "span.tituloDisciplina")
                    texto = span.text.strip()
                    if " - " in texto:
                        codigo, nome = texto.split(" - ", 1)
                        disciplina_atual = {
                            "codigo": codigo.strip(),
                            "nome": nome.strip(),
                        }
                        disciplinas_dict[disciplina_atual["codigo"]] = disciplina_atual
                except (NoSuchElementException, StaleElementReferenceException):
                    disciplina_atual = None
                    resumo.registrar_linha_pulada("stale")
                continue

            if "linhaPar" not in classes and "linhaImpar" not in classes:
                continue

            try:
                tds = linha.find_elements(By.TAG_NAME, "td")
                if len(tds) < 8:
                    resumo.registrar_linha_pulada("menos_de_8_celulas")
                    continue

                # Uma célula pode ter vários docentes; "A DEFINIR DOCENTE"
                # não gera professor nem turma (a disciplina já foi registrada).
                docentes_brutos = tds[2].text
                resumo.a_definir_ignorados += contar_a_definir(docentes_brutos)
                docentes = extrair_docentes(docentes_brutos)
                if not docentes:
                    continue

                if not disciplina_atual:
                    resumo.registrar_linha_pulada("sem_disciplina")

                for nome_prof in docentes:
                    chave_prof = (nome_prof, departamento)
                    if chave_prof not in professores_dict:
                        professores_dict[chave_prof] = {
                            "nome": nome_prof,
                            "departamento": departamento,
                        }

                    if disciplina_atual:
                        turmas_list.append(
                            {
                                "disciplina_codigo": disciplina_atual["codigo"],
                                "professor_nome": nome_prof,
                                "professor_departamento": departamento,
                                "ano": int(ano),
                                "periodo": int(periodo),
                                "docentes_brutos": docentes_brutos,
                            }
                        )
            except StaleElementReferenceException:
                resumo.registrar_linha_pulada("stale")
                continue
            except Exception as e:
                print(f"[!] Erro ao processar linha: {e}")
                resumo.registrar_linha_pulada("erro")
                continue

        return (
            list(professores_dict.values()),
            list(disciplinas_dict.values()),
            turmas_list,
        )

    def fechar(self):
        try:
            self.driver.quit()
        except OSError:
            pass
        except Exception:
            pass


# ---------- execução ----------

def imprimir_dry_run(professores, disciplinas, turmas, a_definir_ignorados):
    """Mostra o que seria gravado, sem tocar no banco (ids simulados)."""
    mapa_prof = {
        (p["nome"], p["departamento"]): i for i, p in enumerate(professores, 1)
    }
    mapa_disc = {d["codigo"]: i for i, d in enumerate(disciplinas, 1)}
    payload = montar_payload_turmas(turmas, mapa_prof, mapa_disc)

    nome_por_id = {i: chave for chave, i in mapa_prof.items()}
    codigo_por_id = {i: codigo for codigo, i in mapa_disc.items()}
    bruto_por_turma = {}
    for t in turmas:
        bruto_por_turma.setdefault(
            (t["professor_nome"], t["disciplina_codigo"]), t["docentes_brutos"]
        )

    departamentos = sorted({p["departamento"] for p in professores})

    print("\n" + "=" * 55)
    print("[DRY-RUN] Nada será gravado no banco.")
    print("=" * 55)
    print(f"Unidade/departamento: {', '.join(departamentos) or '(nenhum)'}")
    print(f"Professores: {len(professores)}")
    print(f"Disciplinas: {len(disciplinas)}")
    print(f"Turmas únicas: {len(payload)} (de {len(turmas)} extraídas)")
    print(f"'A DEFINIR DOCENTE' ignorados: {a_definir_ignorados}")

    em_varias = professores_em_varias_unidades(professores)
    print(f"Professores em mais de uma unidade: {len(em_varias)}")

    print("\n--- PROFESSORES (nome | departamento) ---")
    for p in professores:
        print(f"{p['nome']} | {p['departamento']}")

    print("\n--- PROFESSORES EM MAIS DE UMA UNIDADE (nome | unidades) ---")
    for nome, unidades in em_varias.items():
        print(f"{nome} | {' ; '.join(unidades)}")
    if not em_varias:
        print("(nenhum)")

    print("\n--- DISCIPLINAS (codigo | nome) ---")
    for d in disciplinas:
        print(f"{d['codigo']} | {d['nome']}")

    print("\n--- TURMAS (disciplina | ano/periodo | professor | célula bruta) ---")
    for t in payload:
        nome, _ = nome_por_id[t["professor_id"]]
        codigo = codigo_por_id[t["disciplina_id"]]
        bruto = bruto_por_turma.get((nome, codigo), "")
        print(
            f"{codigo} | {t['ano']}/{t['periodo']} | {nome} | "
            f"bruto={bruto!r}"
        )


def _escolher_unidades(disponiveis, pedidas, resumo):
    """Cruza as unidades pedidas (values) com as do formulário.

    Sem pedidas, devolve todas. Value inexistente vira unidade pulada.
    """
    if not pedidas:
        return disponiveis

    por_value = dict(disponiveis)
    escolhidas = []
    for valor in dict.fromkeys(pedidas):  # sem repetidos, mantendo a ordem
        if valor in por_value:
            escolhidas.append((valor, por_value[valor]))
        else:
            resumo.registrar_unidade_pulada(valor, "não existe no formulário")
    return escolhidas


def main(
    ano: str = "2026",
    periodo: str = "2",
    unidades=None,
    dry_run: bool = False,
    headless: bool = False,
    pausa: float = 1.0,
) -> int:
    resumo = Resumo()
    scraper = SigaaScraper(headless=headless, pausa=pausa)
    try:
        disponiveis = scraper.listar_unidades()
        if not disponiveis:
            print("[!] Não consegui obter a lista de unidades.")
            return 1

        escolhidas = _escolher_unidades(disponiveis, unidades, resumo)
        print(f"[*] Unidades a processar: {len(escolhidas)} ({ano}/{periodo})")

        professores_dict = {}
        disciplinas_dict = {}
        turmas = []

        for n, (valor, texto) in enumerate(escolhidas):
            if n:
                time.sleep(pausa)
            try:
                r = scraper.buscar_unidade(ano, periodo, valor, texto)
            except UnidadeInvalidaError as e:
                resumo.registrar_unidade_pulada(texto, str(e))
                continue

            if r.status == FALHA:
                resumo.registrar_unidade_pulada(texto, r.motivo)
            elif r.status == VAZIO:
                resumo.registrar_sem_turmas(texto)
            else:
                resumo.registrar_ok(texto)
                resumo.incorporar(r.resumo)
                for p in r.professores:
                    professores_dict.setdefault((p["nome"], p["departamento"]), p)
                for d in r.disciplinas:
                    disciplinas_dict.setdefault(d["codigo"], d)
                turmas.extend(r.turmas)

        professores = list(professores_dict.values())
        disciplinas = list(disciplinas_dict.values())

        if dry_run:
            imprimir_dry_run(professores, disciplinas, turmas, resumo.a_definir_ignorados)
        elif professores and disciplinas:
            mapa_prof = salvar_professores(professores)
            mapa_disc = salvar_disciplinas(disciplinas)
            salvar_turmas(turmas, mapa_prof, mapa_disc)
        else:
            print("[!] Nada para subir (lista vazia).")

        resumo.imprimir()
        return resumo.codigo_saida()
    finally:
        scraper.fechar()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    args = montar_parser().parse_args()

    sys.exit(
        main(
            ano=args.ano,
            periodo=args.periodo,
            unidades=args.unidade,
            dry_run=args.dry_run,
            headless=args.headless,
            pausa=args.pausa,
        )
    )
