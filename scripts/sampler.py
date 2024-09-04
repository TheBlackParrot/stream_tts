#! venv/bin/python
import os
import json
import wave
from piper import PiperVoice

settings = None
with open("settings.json", "r") as settingsFile:
    settings = json.load(settingsFile)
voiceArgs = None
with open("tts_voices.json", "r") as voiceArgsFile:
    voiceArgs = json.load(voiceArgsFile)

voices = []
for modelSettings in settings['models']:
    print("loading model %s" % modelSettings['path'])
    voices.append(PiperVoice.load(modelSettings['path'], config_path=modelSettings['config']))

examplePrompts = []
examplePromptFiles = [
    "prompts/barbie.txt",
    "prompts/goteth_caught.txt",
    "prompts/submarine_is_kill.txt",
    "prompts/flareon.txt",
    "prompts/mid.txt",
    "prompts/among_us_banned.txt",
    "prompts/furries_short.txt",
    "prompts/can_you_believe_it_guys.txt"
]

for filename in examplePromptFiles:
    with open(filename, 'r') as promptFile:
        examplePrompts.append({"text": promptFile.read(), "title": os.path.basename(filename).split(".")[0]})

for promptData in examplePrompts:
    for pitch in voiceArgs:
        for voiceData in voiceArgs[pitch]:     
            activeModel = voiceData['model']
            filename = f"/tmp/tts_output/{pitch}-{voiceData['speaker_id']}-{activeModel}/{promptData['title']}.wav"

            if not os.path.isdir(os.path.dirname(filename)):
                os.mkdir(os.path.dirname(filename))

            with wave.open(filename, "wb") as waveFile:
                print(f"synthesizing prompt {promptData['title']} with voice {pitch}-{voiceData['speaker_id']} using model {activeModel}");
                voiceDataFixed = dict(voiceData)
                del voiceDataFixed['model']
                voices[activeModel].synthesize(text=promptData['text'], wav_file=waveFile, **voiceDataFixed)