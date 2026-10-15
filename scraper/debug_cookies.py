import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


URL = "https://sigaa.unb.br/sigaa/public/turmas/listar.jsf"
ANO = "2026"
PERIODO = "2"
UNIDADE_VALUE = "673"


def dump_cookies(driver, etapa: str):
    """Imprime todos os cookies de forma legível."""
    print(f"\n{'='*60}")
    print(f"[COOKIES] Etapa: {etapa}")
    print(f"{'='*60}")
    print(f"URL atual: {driver.current_url}")
    print(f"Título: {driver.title}")

    cookies = driver.get_cookies()
    if not cookies:
        print("  (nenhum cookie encontrado)")
    else:
        for c in cookies:
            nome = c.get("name")
            valor = c.get("value", "")
            dominio = c.get("domain")
            path = c.get("path")
            # Trunca o valor pra não poluir
            valor_curto = valor[:40] + "..." if len(valor) > 40 else valor
            print(f"  {nome} = {valor_curto}")
            print(f"      domínio={dominio}  path={path}")

    # Mostra também o tamanho do page_source (pra ver se a página veio mesmo)
    try:
        tamanho = len(driver.page_source)
        print(f"Tamanho do HTML: {tamanho} chars")
    except Exception:
        print("Não consegui medir o HTML")


def main():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    try:
        # ----- Etapa 1: Acessar a home -----
        print(f"[*] Acessando {URL}...")
        driver.get(URL)
        wait.until(EC.presence_of_element_located((By.ID, "formTurma:inputNivel")))
        time.sleep(3)
        dump_cookies(driver, "1. Após carregar a home")

        # ----- Etapa 2: Selecionar Graduação -----
        print("\n[*] Selecionando Graduação...")
        Select(driver.find_element(By.ID, "formTurma:inputNivel")).select_by_value("G")
        time.sleep(4)
        dump_cookies(driver, "2. Após selecionar Graduação")

        # ----- Etapa 3: Selecionar Unidade -----
        print("\n[*] Selecionando unidade...")
        wait.until(
            lambda d: len(Select(d.find_element(By.ID, "formTurma:inputDepto")).options) > 1
        )
        time.sleep(2)
        depto_select = Select(driver.find_element(By.ID, "formTurma:inputDepto"))

        try:
            depto_select.select_by_value(UNIDADE_VALUE)
            print(f"    Unidade selecionada por value: {UNIDADE_VALUE}")
        except Exception:
            print(f"    Value {UNIDADE_VALUE} não existe. Tentando por texto...")
            for opt in depto_select.options:
                txt = opt.text.upper()
                if "FCTE" in txt or "GAMA" in txt:
                    depto_select.select_by_visible_text(opt.text)
                    print(f"    Unidade por texto: {opt.text}")
                    break

        time.sleep(4)
        dump_cookies(driver, "3. Após selecionar Unidade")

        # ----- Etapa 4: Preencher Ano/Período -----
        print("\n[*] Preenchendo ano/período...")
        ano_input = driver.find_element(By.ID, "formTurma:inputAno")
        ano_input.clear()
        ano_input.send_keys(ANO)
        Select(driver.find_element(By.ID, "formTurma:inputPeriodo")).select_by_value(PERIODO)
        time.sleep(3)
        dump_cookies(driver, "4. Após preencher ano/período")

        # ----- Etapa 5: Clicar em Buscar -----
        print("\n[*] Clicando em Buscar...")
        driver.find_element(By.XPATH, "//input[@value='Buscar']").click()
        time.sleep(6)
        dump_cookies(driver, "5. Após clicar em Buscar (6s)")

        # ----- Etapa 6: Verificar se há alerta -----
        try:
            alert = driver.switch_to.alert
            print(f"\n[!] ALERTA PRESENTE: {alert.text}")
            alert.accept()
            time.sleep(2)
            dump_cookies(driver, "6. Após fechar o alerta")
        except Exception:
            print("\n[*] Nenhum alerta presente.")

        # ----- Etapa 7: Verificar se há linhas de turma -----
        linhas = driver.find_elements(By.CSS_SELECTOR, "tr.linhaPar, tr.linhaImpar")
        print(f"\n[*] Linhas de turma encontradas: {len(linhas)}")

        # ----- Etapa 8: Salvar HTML final -----
        with open("debug_final.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("[*] HTML final salvo em debug_final.html")

        # Deixa o navegador aberto pra inspeção manual
        print("\n[*] Navegador aberto. Pressione Enter no terminal pra fechar.")
        input()

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()