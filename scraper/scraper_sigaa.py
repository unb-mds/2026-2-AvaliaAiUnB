import re
import time
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

from supabase_client import supabase
from texto_sigaa import extrair_docentes, normalizar_texto


class SigaaScraper:
    def __init__(self, headless=False, delay=6.0):
        options = uc.ChromeOptions()

        if headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        # 🔥 Desabilita cache do navegador (evita enviar página antiga)
        options.add_argument("--disable-application-cache")
        options.add_argument("--disk-cache-size=0")

        self.driver = uc.Chrome(options=options)

        self.wait = WebDriverWait(self.driver, 30)
        self.url = "https://sigaa.unb.br/sigaa/public/turmas/listar.jsf"
        self.delay = delay

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

    def _limpar_cache(self):
        """Limpa o cache do navegador via CDP."""
        try:
            self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
            print("[*] Cache do navegador limpo.")
        except Exception as e:
            print(f"[!] Não consegui limpar cache: {e}")

    def _aguardar_estabilidade(self, segundos=1.0):
        time.sleep(segundos)

    def _sessao_viva(self) -> bool:
        try:
            _ = self.driver.current_url
            return True
        except (InvalidSessionIdException, WebDriverException):
            return False

    def _pagina_mudou(self, url_antes: str) -> bool:
        try:
            return self.driver.current_url != url_antes
        except Exception:
            return False

    def _salvar_debug(self, motivo: str = "falha"):
        """Salva screenshot + HTML da página atual para debug."""
        try:
            pasta = Path("debug")
            pasta.mkdir(exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            # Tenta fechar alerta primeiro pra poder acessar a página
            self._fechar_alertas()

            caminho_png = pasta / f"{motivo}_{timestamp}.png"
            try:
                self.driver.save_screenshot(str(caminho_png))
                print(f"[DEBUG] Screenshot: {caminho_png.resolve()}")
            except Exception:
                pass

            caminho_html = pasta / f"{motivo}_{timestamp}.html"
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

    @staticmethod
    def _extrair_departamento(texto: str) -> str | None:
        if not texto:
            return None
        texto = texto.strip()
        match = re.match(r"([A-Za-z]+)\s*-", texto)
        if match:
            return match.group(1).upper()
        return texto or None

    # ---------- busca (wrapper com retry completo) ----------

    def buscar_professores_graduacao(self, ano, periodo, unidade_value, tentativas=3):
        """
        Tenta a busca N vezes. Se qualquer tentativa falhar por alerta
        (sessão do servidor expirada), reinicia TODO o fluxo do zero.
        """
        for i in range(1, tentativas + 1):
            print(f"\n{'='*55}")
            print(f"[*] TENTATIVA {i}/{tentativas}")
            print(f"{'='*55}")

            # Garante que não há alerta pendente de tentativa anterior
            self._fechar_alertas()

            # Limpa cache antes de começar (evita enviar página velha)
            if i > 1:
                self._limpar_cache()

            professores, disciplinas, turmas = self._buscar(
                ano, periodo, unidade_value
            )

            if professores or disciplinas:
                print(f"[*] Tentativa {i} bem-sucedida!")
                return professores, disciplinas, turmas

            print(f"[!] Tentativa {i} voltou vazia.")

            if i < tentativas:
                print("[*] Aguardando 5s antes de tentar de novo...")
                time.sleep(5)

                # Se a sessão morreu, recria o driver
                if not self._sessao_viva():
                    print("[*] Sessão morreu. Recriando driver...")
                    try:
                        self.driver.quit()
                    except Exception:
                        pass
                    self.__init__(headless=False, delay=self.delay)

        print("[!] Todas as tentativas falharam.")
        return [], [], []

    def _buscar(self, ano, periodo, unidade_value=None):
        """
        Wrapper: captura qualquer exceção, fecha alerta primeiro,
        e retorna listas vazias pra o retry acontecer no nível de cima.
        """
        try:
            return self._buscar_interno(ano, periodo, unidade_value)

        except UnexpectedAlertPresentException as e:
            # 🔥 PRIMEIRA coisa: fechar o alerta
            print("[!] Alerta inesperado detectado. Fechando...")
            self._fechar_alertas()
            try:
                print(f"[!] Texto do alerta: {e.alert_text}")
            except Exception:
                pass
            # Salva evidência
            self._salvar_debug("alerta_sessao")
            return [], [], []

        except InvalidSessionIdException:
            print("[!] Sessão do navegador caiu.")
            return [], [], []

        except WebDriverException as e:
            # Pode ser alerta disfarçado — tenta fechar
            print(f"[!] Erro do WebDriver: {e}")
            self._fechar_alertas()
            return [], [], []

        except Exception as e:
            print(f"[!] Erro inesperado: {e}")
            self._fechar_alertas()
            return [], [], []

    def _buscar_interno(self, ano, periodo, unidade_value=None):
        print(f"[*] Acessando {self.url}...")
        self.driver.get(self.url)

        try:
            self.wait.until(
                EC.presence_of_element_located((By.ID, "formTurma:inputNivel"))
            )
        except TimeoutException:
            print("[!] Não conseguiu carregar o formulário.")
            self._salvar_debug("form_nao_carregou")
            return [], [], []

        self._aguardar_estabilidade(self.delay)
        self._fechar_alertas()

        url_inicial = self.driver.current_url

        # 1. Nível: Graduação
        try:
            nivel_select = Select(
                self.driver.find_element(By.ID, "formTurma:inputNivel")
            )
            nivel_select.select_by_value("G")
            print("[*] Nível selecionado: Graduação")
        except StaleElementReferenceException:
            print("[!] Elemento 'Nível' stale. Recarregando...")
            self.driver.get(self.url)
            self._aguardar_estabilidade(self.delay * 2)
            nivel_select = Select(
                self.driver.find_element(By.ID, "formTurma:inputNivel")
            )
            nivel_select.select_by_value("G")

        self._aguardar_estabilidade(self.delay * 2)
        self._fechar_alertas()

        # 2. Unidade
        if unidade_value:
            try:
                self.wait.until(
                    lambda d: len(
                        Select(d.find_element(By.ID, "formTurma:inputDepto")).options
                    ) > 1
                )
                self._aguardar_estabilidade(self.delay)

                depto_select = Select(
                    self.driver.find_element(By.ID, "formTurma:inputDepto")
                )

                # Tenta pelo value; se falhar, tenta pelo texto
                try:
                    depto_select.select_by_value(unidade_value)
                    print(f"[*] Unidade selecionada por value: {unidade_value}")
                except Exception:
                    print(f"[!] Value '{unidade_value}' não existe. Tentando pelo texto...")
                    encontrou = False
                    for opt in depto_select.options:
                        txt = opt.text.upper()
                        if "FCTE" in txt or "GAMA" in txt:
                            depto_select.select_by_visible_text(opt.text)
                            print(f"[*] Unidade por texto: {opt.text} (value={opt.get_attribute('value')})")
                            encontrou = True
                            break
                    if not encontrou:
                        print("[!] Nenhuma unidade com FCTE/GAMA. Abortando.")
                        self._salvar_debug("unidade_nao_encontrada")
                        return [], [], []

                self._aguardar_estabilidade(self.delay)
                self._fechar_alertas()
            except TimeoutException:
                print("[!] Timeout ao carregar unidades. Continuando...")

        # 3. Ano e período
        try:
            ano_input = self.driver.find_element(By.ID, "formTurma:inputAno")
            ano_input.clear()
            ano_input.send_keys(ano)

            periodo_select = Select(
                self.driver.find_element(By.ID, "formTurma:inputPeriodo")
            )
            periodo_select.select_by_value(periodo)
            print(f"[*] Ano/Período: {ano}/{periodo}")
        except StaleElementReferenceException:
            print("[!] Campos stale. Recarregando...")
            self.driver.get(self.url)
            self._aguardar_estabilidade(self.delay * 2)
            return [], [], []

        self._aguardar_estabilidade(self.delay)
        self._fechar_alertas()

        # 4. Buscar
        try:
            botao_buscar = self.driver.find_element(
                By.XPATH, "//input[@value='Buscar']"
            )
            botao_buscar.click()
            print("[*] Clique em Buscar enviado. Aguardando...")
        except Exception as e:
            print(f"[!] Erro ao clicar em Buscar: {e}")
            return [], [], []

        self._aguardar_estabilidade(self.delay * 2)

        # 🔥 Aqui é onde o alerta costuma aparecer. Checa ANTES de qualquer coisa.
        self._fechar_alertas()

        if not self._sessao_viva():
            print("[!] Navegador fechou após o clique.")
            return [], [], []

        if self._pagina_mudou(url_inicial):
            print(f"[*] Página redirecionou para: {self.driver.current_url}")

        # 5. Esperar linhas de turma
        try:
            self.wait.until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, "tr.linhaPar, tr.linhaImpar")
                ) > 0
            )
        except UnexpectedAlertPresentException:
            # Já tratado no wrapper, mas por segurança:
            print("[!] Alerta ao esperar resultados.")
            self._fechar_alertas()
            return [], [], []
        except InvalidSessionIdException:
            print("[!] Sessão morreu esperando resultados.")
            return [], [], []
        except TimeoutException:
            # Antes de declarar vazio, checa se tem alerta
            if self._fechar_alertas():
                print("[!] Havia alerta escondido. Sessão expirou.")
                return [], [], []
            print("[!] Nenhuma turma encontrada para esse filtro.")
            self._salvar_debug("sem_resultado")
            return [], [], []

        self._aguardar_estabilidade(self.delay)

        # 6. Extrair
        professores, disciplinas, turmas = self._extrair_tudo(ano, periodo)
        print(
            f"[*] Encontrados: {len(professores)} professores, "
            f"{len(disciplinas)} disciplinas, {len(turmas)} turmas."
        )
        return professores, disciplinas, turmas

    # ---------- extração ----------

    def _extrair_tudo(self, ano: str, periodo: str):
        professores_dict = {}
        disciplinas_dict = {}
        turmas_list = []
        disciplina_atual = None

        try:
            linhas = self.driver.find_elements(
                By.CSS_SELECTOR, "tr.agrupador, tr.linhaPar, tr.linhaImpar"
            )
        except Exception as e:
            print(f"[!] Erro ao buscar linhas: {e}")
            return [], [], []

        for linha in linhas:
            try:
                classes = linha.get_attribute("class") or ""
            except StaleElementReferenceException:
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
                continue

            if "linhaPar" not in classes and "linhaImpar" not in classes:
                continue

            try:
                tds = linha.find_elements(By.TAG_NAME, "td")
                if len(tds) < 8:
                    continue

                # Uma célula pode ter vários docentes; "A DEFINIR DOCENTE"
                # não gera professor nem turma (a disciplina já foi registrada).
                docentes = extrair_docentes(tds[2].text)
                if not docentes:
                    continue

                departamento = self._extrair_departamento(tds[7].text)

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
                            }
                        )
            except StaleElementReferenceException:
                continue
            except Exception as e:
                print(f"[!] Erro ao processar linha: {e}")
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


# ---------- integração com Supabase ----------

def salvar_professores(professores: list) -> dict:
    if not professores:
        print("[!] Nenhum professor para salvar.")
        return {}
    try:
        response = (
            supabase.table("professores")
            .upsert(professores, on_conflict="nome,departamento")
            .execute()
        )
        print(f"[*] {len(response.data)} professores upsertados.")
        return {(p["nome"], p.get("departamento")): p["id"] for p in response.data}
    except Exception as e:
        print(f"[!] Erro ao salvar professores: {e}")
        return {}


def salvar_disciplinas(disciplinas: list) -> dict:
    if not disciplinas:
        return {}
    try:
        response = (
            supabase.table("disciplinas")
            .upsert(disciplinas, on_conflict="codigo")
            .execute()
        )
        print(f"[*] {len(response.data)} disciplinas upsertadas.")
        return {d["codigo"]: d["id"] for d in response.data}
    except Exception as e:
        print(f"[!] Erro ao salvar disciplinas: {e}")
        return {}


def salvar_turmas(turmas: list, mapa_prof: dict, mapa_disc: dict):
    if not turmas:
        return

    # 🔥 Deduplica turmas pela chave única (professor, disciplina, ano, periodo)
    vistos = set()
    payload = []

    for t in turmas:
        prof_id = mapa_prof.get((t["professor_nome"], t["professor_departamento"]))
        disc_id = mapa_disc.get(t["disciplina_codigo"])

        if not prof_id or not disc_id:
            continue

        chave = (prof_id, disc_id, t["ano"], t["periodo"])

        if chave in vistos:
            # Já adicionamos essa combinação; pula
            continue

        vistos.add(chave)
        payload.append({
            "professor_id": prof_id,
            "disciplina_id": disc_id,
            "ano": t["ano"],
            "periodo": t["periodo"],
        })

    if not payload:
        print("[!] Nenhuma turma única para salvar.")
        return

    print(f"[*] Turmas únicas após deduplicação: {len(payload)} (de {len(turmas)} originais)")

    try:
        response = (
            supabase.table("turmas")
            .upsert(payload, on_conflict="professor_id,disciplina_id,ano,periodo")
            .execute()
        )
        print(f"[*] {len(response.data)} turmas upsertadas.")
    except Exception as e:
        print(f"[!] Erro ao salvar turmas: {e}")


# ---------- execução ----------

if __name__ == "__main__":
    ANO = "2026"
    PERIODO = "2"
    UNIDADE_VALUE = "673"  # FCTE - Gama (ajuste se necessário)

    scraper = SigaaScraper(headless=False, delay=6.0)
    try:
        professores, disciplinas, turmas = scraper.buscar_professores_graduacao(
            ANO, PERIODO, UNIDADE_VALUE, tentativas=3
        )

        print("\n--- AMOSTRA DE PROFESSORES ---")
        for p in professores[:10]:
            print(p)

        print("\n--- AMOSTRA DE DISCIPLINAS ---")
        for d in disciplinas[:5]:
            print(d)

        if professores and disciplinas:
            mapa_prof = salvar_professores(professores)
            mapa_disc = salvar_disciplinas(disciplinas)
            salvar_turmas(turmas, mapa_prof, mapa_disc)
        else:
            print("[!] Nada para subir (lista vazia).")
    finally:
        scraper.fechar()