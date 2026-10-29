name = 'Slava'
nameAI = 'антон'
inp = ">"

apiK = 'sk_UDB2W9U0WmttTyB7hiGU3G3gnvm6W2IH'

city = 'Воронеж'
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

from piper import PiperVoice, SynthesisConfig
voice = PiperVoice.load(
    "ru/ru_RU/ruslan/medium/ru_RU-ruslan-medium.onnx",
    config_path="ru/ru_RU/ruslan/medium/ru_RU-ruslan-medium.onnx.json"
)