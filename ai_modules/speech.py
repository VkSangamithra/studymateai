import speech_recognition as sr

def audio_to_text(audio_path):

    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:

        audio = recognizer.record(source)

    text = recognizer.recognize_google(audio)

    return text