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

from pollinations import Pollinations
import re

from settings import *
from sayAI import *

wiretapping = True


# НАТСРОЙКА ИИ 
client = Pollinations(api_key=apiK)
system_prompt = f"""Голосовой ассистент. Твое имя - {nameAI} Отвечай одним коротким предложением, до 12 слов.
Это озвучка вслух — длинный текст не читай.
Без эмодзи, markdown, списков и пошаговых инструкций.
Обязательно проверяй. Если это чтото без контекста и ты думаешь что случайно включился то пиши только - STOP

Если вопрос требует длинного ответа (рецепт, инструкция):
  1) Сначала ОТВЕТЬ ПО СУТИ — одно предложение с конкретикой, БЕЗ анонсов
     типа "дам рецепт", "сейчас расскажу", "вот кратко". Сразу факты.
     Пример: "Слоёные коржи, крем из сгущёнки и масла, шоколад сверху."
  2) Потом спроси: "Рассказать подробнее?"
  3) Только если пользователь ответил да/ок/давай — ответь ровно: GOOGLE <сам вопрос>
"""

response = requests.get(f"https://wttr.in/{city}?format=3") #погода

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
    # убираем эмодзи и прочие не-буквы/цифры/пунктуацию
    text = re.sub(r"[^\w\s,.!?;:°+\-]", "", text, flags=re.UNICODE)
    # убираем множественные пробелы и запятые
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r",\s*,", ",", text).strip(" ,")
    return text

def look(query):
    
    if "youtube" in query:
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

# Внутри speak() добавь async:
async def speak(text):
    global is_speaking

    is_speaking = True
    try:
        text = clean_for_tts(text)

        print(f"{nameAI} {inp} {text}")
        
        text = text.replace("!", ",").replace(".", ",")
        
        communicate = edge_tts.Communicate(text, "ru-RU-SvetlanaNeural", rate="+5%")
        
        # Собираем все аудио-куски в один буфер
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        # Декодируем MP3 в PCM через miniaudio (без FFmpeg)
        decoded = miniaudio.decode(audio_data, output_format=miniaudio.SampleFormat.SIGNED16)
        
        # Воспроизводим через простой поток
        import pyaudio
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=decoded.nchannels, rate=decoded.sample_rate, output=True)
        stream.write(decoded.samples.tobytes())
        stream.stop_stream()
        stream.close()
        p.terminate()
    finally:
        is_speaking = False

def google(say):
    words = say.split()
    if words:
        query = " ".join(words[1:]).strip()
        
        if query:
            if "ютуби" in query or "youtube" in query:
                query = query.replace("в youtube", "").replace("на youtube", "").strip()
                query = query.replace("в ютуби", "").replace("на ютуби", "").strip()
                subprocess.Popen([chrome_path, f'https://www.youtube.com/results?search_query={query}'])
            else:
                subprocess.Popen([chrome_path, f'https://www.google.com/search?q={query}'])
            
            asyncio.run(speak('Открываю...'))


def com_say(say):
    if 'погод' in say:
        r = requests.get(f"https://wttr.in/{city}?format=3")
        asyncio.run(speak(r.text))
    elif "включи" in say or "открой" in say or "запусти" in say:

        look(say)
        if "discord" in say:
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
    elif "привет" in say:
        asyncio.run(speak("Привет!"))
        
    elif "стоп" in say or "выход" in say or "заткнись" in say:
        asyncio.run(speak("пока!"))
        time.sleep(2)
        stop_event.set()
        stop_listening(wait_for_stop=False)
        return

    elif "пиши" in say:
        query = say.replace("напиши", "").replace("пиши", "").strip()
        
        import pyautogui
        pyautogui.write(query)
        active_window = gw.getActiveWindow()

        if active_window:
            window_title = active_window.title.lower()
                
            if "telegram" in window_title or "discord" in window_title:
                question = 'say_tg'
                asyncio.run(speak("Отправить?"))
    elif any(say.startswith(word) for word in ["вбей", "загугли"]):
        # Удаляем первое слово
        google(query)
    else:
        say_ai(say)

history = []          # список пар {"role","content"}
MAX_PAIRS = 5         # помнить 3 последних обмена

def say_ai(say):
    global history
    global wiretapping

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": say})

    try:
        response = client.chat.completions.create(messages=messages, model="openai")
        reply = response.choices[0].message.content


        
        print(">>> ", reply)

        if "GOOGLE" in reply:
            google(reply)
        elif "STOP" in reply:
            wiretapping = False
        else:
            asyncio.run(speak(reply))

        # сохраняем в историю только реальный диалог
        history.append({"role": "user", "content": say})
        history.append({"role": "assistant", "content": reply})

        # обрезаем до MAX_PAIRS пар (2 сообщения на пару)
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
        text = recognizer.recognize_google(audio, language="ru-RU")
        print(name, inp , text)
        query = text.lower()

        # обработка команд

        if nameAI in query:
            wiretapping = True
        elif query == "":
            wiretapping = False

        if wiretapping:
            print(wiretapping)
            com_say(query.lower())

    except sr.UnknownValueError:
        wiretapping = False
        pass
    except sr.RequestError:
        print("Нет интернета")
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