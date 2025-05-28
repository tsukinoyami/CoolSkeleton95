from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

session_id = input("sessionid: ")

# Configurar Chrome
options = Options()
options.add_argument("--start-maximized")

# Iniciar navegador con Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 1. Ir a instagram.com para habilitar el dominio
driver.get("https://www.instagram.com")
time.sleep(3)  # Esperar a que cargue

# 2. Añadir cookies personalizadas (debes conocer estos valores)
custom_cookies = [
    {"name": "sessionid", "value": "TU_SESSIONID", "domain": ".instagram.com"},
#    {"name": "ds_user_id", "value": "TU_USER_ID", "domain": ".instagram.com"},
#    {"name": "csrftoken", "value": "TU_TOKEN", "domain": ".instagram.com"}
]

for cookie in custom_cookies:
    driver.add_cookie(cookie)

# 3. Recargar para aplicar cookies
driver.get("https://www.instagram.com/accounts/edit/")
time.sleep(5)
