import speech_recognition as sr
import win32com.client
import threading
import time
import requests
import asyncio, edge_tts, os
import pygetwindow as gw
import subprocess

from playsound3 import playsound
import miniaudio

from piper import PiperVoice, SynthesisConfig
import sounddevice as sd

from pollinations import Pollinations
import re

from settings import *
from sayAI import *

import io
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

print("Загружаю whisper...")
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
print("Whisper загружен")

wiretapping = True
last = ''

# НАТСРОЙКА ИИ
client = Pollinations(api_key=apiK)
system_prompt = f"""Голосовой ассистент. Твое имя - {nameAI} Отвечай одним коротким предложением, до 12 слов.
Это озвучка вслух — длинный текст не читай.
Без эмодзи, markdown, списков и пошаговых инструкций.
Обязательно проверяй. Если это чтото без контекста и ты думаешь что случайно включился то пиши только - STOP. Исключение, если к тебе не обралисись по имени {nameAI}

Если вопрос требует длинного ответа (рецепт, инструкция):
  1) Сначала ОТВЕТЬ ПО СУТИ — одно предложение с конкретикой, БЕЗ анонсов
     типа "дам рецепт", "сейчас расскажу", "вот кратко". Сразу факты.
     Пример: "Слоёные коржи, крем из сгущёнки и масла, шоколад сверху."
  2) Потом спроси: "Рассказать подробнее?" или чета подобное (Если реально надо подробнее)
  3) Только если пользователь ответил да/ок/давай — ответь ровно: GOOGLE <сам вопрос> (обязательно болщими GOOGLE)

  Если тебя просят сразу загуглить, то: GOOGLE <сам вопрос> (обязательно большими GOOGLE)
  Если найти на ютубе, то: YOUTUBE <сам вопрос> (обязательно большими YOUTUBE)
  Если тебя просят чтото написть, то SAAY <что просили> (обязательно большими SAAY)(Тут можешь не мелочится в потолок 12 слов)(Если просят тебя чтото типа напиши поздравления то подумай и пиши: SAAY <что ты придумал>)
  Обычно пользователи пишут с ошибками, не уточнаяй и просто пиши додумавя кто это(пример Каранапалеон = Напалеон)
"""

response = requests.get(f"https://wttr.in/{city}?format=3")  # погода

# Распознаватель речи
sr_recognizer = sr.Recognizer()
sr_recognizer.energy_threshold = 300
sr_recognizer.dynamic_energy_threshold = True

MIC_INDEX = 1

# Флаг для управления состоянием (чтобы не перебивать самих себя)
is_speaking = False

# Флаг для корректного выхода из главного цикла
stop_event = threading.Event()


def clean_for_tts(text):
    text = re.sub(r"[^\w\s,.!?;:°+\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r",\s*,", ",", text).strip(" ,")
    return text


def look(query):
    if "youtube" in query or "ютуб" in query:
        if "в" in query or "на" in query:
            say_ai(query)
        else:
            subprocess.Popen([chrome_path, 'https://www.youtube.com/'])
        query = query.replace("youtube", "").strip()
    elif "рик и морти" in query or "рика" in query:
        subprocess.Popen([chrome_path, 'https://rick-i-morty.net/'])
        query = query.replace("рик", "").strip()
    elif "твич" in query or "twitch" in query:
        subprocess.Popen([chrome_path, 'https://www.twitch.tv/?lang=ru'])
        query = query.replace("твич", "").replace("twitch", "").strip()
    elif "диксика" in query or "диксик" in query:
        subprocess.Popen([chrome_path, 'https://chat.deepseek.com/'])
        query = query.replace("диксика", "").replace("диксик", "").strip()
    elif "хост" in query or "хостинг" in query:
        subprocess.Popen([chrome_path, 'https://panel.gamely.pro/'])
        query = query.replace("хост", "").replace("хостинг", "").strip()


async def speak(text):
    global is_speaking

    is_speaking = True
    try:
        print(f"{nameAI} {inp} {text}")
        audio_data = []
        syn_config = SynthesisConfig(length_scale=1)
        
        for chunk in voice.synthesize(text, syn_config=syn_config):
            if hasattr(chunk, 'audio_int16_bytes'):
                audio_data.append(chunk.audio_int16_bytes)
            elif hasattr(chunk, 'audio_float_array'):
                float_data = chunk.audio_float_array
                int16_data = (float_data * 32767).astype(np.int16)
                audio_data.append(int16_data.tobytes())
        
        full_audio = b"".join(audio_data)
        audio_array = np.frombuffer(full_audio, dtype=np.int16)

        
        samplerate = 22050
        silence_samples = int(0.3 * samplerate) # +0.3 секунды в конце
        silence = np.zeros(silence_samples, dtype=np.int16)
        audio_array = np.concatenate([audio_array, silence])
        
        sd.play(audio_array, samplerate=samplerate)
        sd.wait()
    finally:
        is_speaking = False


def google(say):
    words = say.split()
    if words:
        query = " ".join(words[1:]).strip()

        if query:
            subprocess.Popen([chrome_path, f'https://www.google.com/search?q={query}'])

            asyncio.run(speak('Открываю...'))
            

def youtube(query):
    words = query.split()
    if words:
        query = " ".join(words[1:]).strip()

        if query:
            subprocess.Popen([chrome_path, f'https://www.youtube.com/results?search_query={query}'])
            asyncio.run(speak('Открываю...'))

def saay(query):

    import time
    import pyperclip
    import pyautogui
    import pyperclip

    words = query.split()
    if len(words) > 1:
        # Берем все слова, КРОМЕ первого
        query = " ".join(words[1:])

    pyperclip.copy(query)
    time.sleep(0.2)

    pyautogui.hotkey('ctrl', 'v', interval=0.1)

    active_window = gw.getActiveWindow()
    if active_window:
        window_title = active_window.title.lower()
        if "telegram" in window_title or "discord" in window_title:
            asyncio.run(speak("Отправить?"))
            last = "say_tg"

def com_say(say):
    global last

    if 'погод' in say:
        r = requests.get(f"https://wttr.in/{city}?format=3")
        asyncio.run(speak(r.text))
    elif "включи" in say or "открой" in say or "запусти" in say or "найд" in say:

        look(say)
        if "discord" in say or "дискорд" in say:
            os.startfile(r"C:\Users\User\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Discord Inc\Discord")
            say = say.replace("discord", "").strip()
        elif "блокнот" in say:
            os.startfile(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Accessories\Notepad.lnk")
            say = say.replace("блокнот", "").strip()
        elif "minecraft" in say:
            os.startfile(r"C:\Users\User\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Modrinth App.lnk")
            say = say.replace("minecraft", "").strip()
        elif "музыку" in say:
            os.startfile(r"C:\Users\User\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Яндекс Музыка.lnk")
            say = say.replace("музыку", "").strip()
        elif "vs code" in say:
            os.startfile(r"C:\Users\User\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Visual Studio Code\Visual Studio Code.lnk")
            say = say.replace("vs code", "").strip()
        elif "telegram" in say or "телегу" in say:
            os.startfile(r"C:\Users\User\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Telegram Desktop\Telegram.lnk")
            say = say.replace("telegram", "").replace("телегу", "").strip()
        elif "прокси" in say:
            os.startfile(r"C:\Users\User\Desktop\TgWsProxy_windows (3).exe")
            say = say.replace("прокси", "").strip()
        elif "стим" in say or "steam" in say:
            os.startfile(r"C:\Users\User\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Steam\Steam.lnk")
            say = say.replace("стим", "").replace("steam", "").strip()
        elif "запрет" in say:
            os.startfile(r"E:\zapret\zapret-discord-youtube-1.10.0\general (ALT).bat")
            say = say.replace("запрет", "").replace("запретку", "").strip()

    elif "стоп" in say or "выход" in say or "заткнись" in say:
        asyncio.run(speak("пока!"))
        time.sleep(2)
        stop_event.set()
        stop_listening(wait_for_stop=False)
        return
    elif "да" in say or "давай" in say:
        
        if last == "say_tg":
            last = ''

            import pyperclip
            import pyautogui
            import pyperclip

            pyautogui.press('enter')
        else:
            say_ai(say)
            
    
    elif any(say.startswith(word) for word in ["вбей", "загугли"]):
        google(say)
    else:
        say_ai(say)


history = []
MAX_PAIRS = 5


def say_ai(say):
    global history
    global wiretapping

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": say})

    try:
        response = client.chat.completions.create(messages=messages, model="openai")
        reply = response.choices[0].message.content

        # print(">>> ", reply)

        if "GOOGLE" in reply:
            google(reply)
        elif "YOUTUBE" in reply:
            youtube(reply)
        elif "SAAY" in reply:
            saay(reply)
        elif "STOP" in reply:
            wiretapping = False
        else:
            asyncio.run(speak(reply))

        history.append({"role": "user", "content": say})
        history.append({"role": "assistant", "content": reply})

        if len(history) > MAX_PAIRS * 2:
            history = history[-MAX_PAIRS * 2:]

    except Exception as e:
        asyncio.run(speak(f"Ошибка AI: {e}"))


def callback(recognizer, audio):
    """Эта функция вызывается фоновым потоком, когда слышна речь."""

    global wiretapping

    if is_speaking:
        return

    try:
        audio_data = audio.get_wav_data()

        # Декодируем WAV-байты в numpy float32
        wav_io = io.BytesIO(audio_data)
        samples, sr_rate = sf.read(wav_io, dtype="float32")

        # faster-whisper ожидает 16 кГц моно
        if sr_rate != 16000:
            import librosa
            samples = librosa.resample(samples, orig_sr=sr_rate, target_sr=16000)

        segments, _ = whisper_model.transcribe(samples, language="ru", beam_size=1, vad_filter=True)
        text = "".join(seg.text for seg in segments).strip()

        print(name, inp, text)
        query = text.lower()

        if not text:
            wiretapping = False
            return

        if nameAI in query:
            wiretapping = True
        elif query == "":
            wiretapping = False

        if wiretapping:
            # print(wiretapping)
            com_say(query.lower())

    except Exception as e:
        print("Ошибка в callback:", e)


# Калибровка микрофона (делается один раз перед запуском)
with sr.Microphone(device_index=MIC_INDEX) as source:
    sr_recognizer.adjust_for_ambient_noise(source, duration=0.5)

# Запускаем фоновое прослушивание.
stop_listening = sr_recognizer.listen_in_background(
    sr.Microphone(device_index=MIC_INDEX),
    callback
)

asyncio.run(speak("Привет!"))
try:
    while not stop_event.is_set():
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Завершение...")
finally:
    stop_listening(wait_for_stop=False)