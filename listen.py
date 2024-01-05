#! venv/bin/python
import re
import io
import wave
import json
import urllib.parse
import requests
import hashlib
from time import time
from num2words import num2words
from piper import PiperVoice
from http.server import BaseHTTPRequestHandler, HTTPServer

settings = None
with open("settings.json", "r") as settingsFile:
    settings = json.load(settingsFile)

voice = PiperVoice.load(settings['model']['path'], config_path=settings['model']['config'])

pronouns = {}
cache = {}

def getPronouns(user):
    if user in pronouns:
        if time() < pronouns[user][1] + 86400:
            return pronouns[user][0]

    req = requests.get("https://pronouns.alejo.io/api/users/" + user)
    if len(req.text) > 0:
        reqJSON = json.loads(req.text)
        if len(reqJSON) > 0:
            pronouns[user] = [reqJSON[0]["pronoun_id"], time()]
        else:
            pronouns[user] = ["", time()]
    else:
        pronouns[user] = ["", time()]

    return pronouns[user][0]

def cleanCache():
    ts = time()
    hashes = [*cache]

    for _hash in hashes:
        if ts > cache[_hash]['timestamp'] + settings['cache']['expire_after']:
            cache.pop(_hash, None)

def stripNonASCII(string):
    output = ""
    for character in string:
        val = ord(character)
        if val >= 32 and val <= 126:
            output += character
    return output

class MyServer(BaseHTTPRequestHandler):
    def writeAudio(self, audio):
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", len(audio))
        self.end_headers()
        self.wfile.write(audio)

    def do_GET(self):
        dictReplace = None
        with open("dict.json", "r") as dictFile:
            dictReplace = json.load(dictFile)
        faceReplace = None
        with open("faces.json", "r") as facesFile:
            faceReplace = json.load(facesFile)
        symReplace = None
        with open("symbols.json", "r") as symFile:
            symReplace = json.load(symFile)
        voiceArgs = None
        with open("tts_voices.json", "r") as voiceArgsFile:
            voiceArgs = json.load(voiceArgsFile)
        ttsStuff = None
        with open("viewer_data.json", "r") as ttsStuffFile:
            ttsStuff = json.load(ttsStuffFile)
        soundList = None
        with open("sounds.json", "r") as soundListFile:
            soundList = json.load(soundListFile)

        main_url = "http://" + settings["http"]["ip"] + ":" + str(settings["http"]["port"]) + self.path
        url_parts = urllib.parse.urlparse(main_url)
        query_parts = urllib.parse.parse_qs(url_parts.query)

        path_parts = self.path[1:].split("/")[:-1]

        _type = path_parts[0].lower()
        _nameCaps = stripNonASCII(urllib.parse.unquote(path_parts[1]))
        _name = urllib.parse.unquote(path_parts[1]).lower()
        _data = " ".join([urllib.parse.unquote(str(item)) for item in path_parts[2:]])
        md5hash = hashlib.md5((_name + _data).encode("utf-8")).hexdigest()

        if md5hash in cache:
            cache[md5hash]['timestamp'] = time()
            self.writeAudio(cache[md5hash]['audio'])
            cleanCache()
            return

        currentTTSData = {
            "say": _data,
        }
        voiceOpts = []
        synthesizeArgs = settings['tts']['name_voice']
        userPronouns = ""

        if _type == "name":
            if _name in ttsStuff:
                currentTTSData["say"] = ttsStuff[_name]["pronunciation"]
            else:
                number_amount = 0
                name_fixed = ""
                name_parts = []
                for character in _nameCaps:
                    try:
                        int(character)
                    except ValueError:
                        name_fixed = name_fixed + character
                    else:
                        if len(name_fixed) > 0:
                            name_parts.append(name_fixed)
                        if number_amount < 4:
                            name_parts.append(num2words(int(character)))
                            number_amount += 1
                        name_fixed = ""
                name_parts.append(name_fixed)

                name_parts_spaced = []
                for item in name_parts:
                    name_parts_spaced.append(" ".join(re.split('(?<=.)(?=[A-Z])', item)).lower())

                currentTTSData["say"] = " ".join([str(item) for item in name_parts_spaced])
        if _type == "msg":
            userPronouns = getPronouns(_name)

            for face in faceReplace:
                _data = _data.replace(face, faceReplace[face])

            for sym in symReplace:
                _data = _data.replace(sym, symReplace[sym])

            print(_data)

            all_words = _data.split(' ')
            all_wordsA = []
            all_wordsB = []

            for word in all_words:
                try:
                    float(word)
                except ValueError:
                    all_wordsA.append(word)
                else:
                    parts = word.split(".")
                    whole = int(parts[0])
                    print("word is number: %f" % whole)
                    if whole < 0:
                        all_wordsA.append("negative")
                        whole = whole * -1

                    all_wordsA.append(num2words(whole))

                    if len(parts) == 2:
                        if parts[1] != "0":
                            try:
                                fractional = int(str(parts[1]).strip("0"))
                            except ValueError:
                                print("word is not a fractional more than likely")
                            else:
                                all_wordsA.append("point")
                                print(fractional)

                                all_wordsA.append(num2words(fractional))

            for word in all_wordsA:
                for dash_part in word.split('-'):
                    for sym in symReplace:
                        dash_part = dash_part.replace(sym, ",")

                    if dash_part.lower() in dictReplace:
                        all_wordsB.append(dictReplace[dash_part.lower()])
                    else:
                        all_wordsB.append(dash_part)

            currentTTSData['say'] = " ".join([str(item) for item in all_wordsB])

            if userPronouns != "hehim" and userPronouns != "hethem":
                print("pronouns not he")
                for item in voiceArgs['high']:
                    voiceOpts.append(item)
            if userPronouns != "sheher" and userPronouns != "shethem":
                print("pronouns not she")
                for item in voiceArgs['low']:
                    voiceOpts.append(item)
            if userPronouns != "hehim" and userPronouns != "sheher":
                for item in voiceArgs['medium']:
                    voiceOpts.append(item)

            synthesizeArgs = voiceOpts[int.from_bytes(bytes(_name.encode("utf-8")), byteorder='big') % len(voiceOpts)]

            if _name in ttsStuff:
                if "voice" in ttsStuff[_name]:
                    pitch = ttsStuff[_name]["voice"][0]
                    speaker = ttsStuff[_name]["voice"][1]

                    for voiceData in voiceArgs[pitch]:
                        if voiceData["speaker_id"] == speaker:
                            print("forcing speaker to " + pitch + "-" + str(voiceData["speaker_id"]))
                            synthesizeArgs = voiceData

        print(currentTTSData["say"])
        if currentTTSData['say'] == "":
            print("... nothing to say? wtf")
            return

        with io.BytesIO() as wavIO:
            with wave.open(wavIO, "wb") as audio_bytes:
                try:
                    audio_bytes.setframerate(22050)
                    audio_bytes.setsampwidth(2)
                    audio_bytes.setnchannels(1)
                except:
                    pass

                for sentence in currentTTSData['say'].split("."):
                    if sentence == "":
                        continue

                    output = []
                    outputPart = {"data": [], "type": "tts"}
                    words = sentence.split(" ")
                    for word in words:
                        if word in soundList:
                            if outputPart["data"] != "":
                                output.append(outputPart)
                            output.append({"data": soundList[word], "type": "sound"})
                            outputPart = {"data": [], "type": "tts"}
                        else:
                            outputPart["data"].append(word)
                    output.append(outputPart)

                    for part in output:
                        if part["type"] == "sound":
                            with wave.open(part["data"], "rb") as sound_data:
                                audio_bytes.writeframes(bytes(sound_data.readframes(sound_data.getnframes())))
                        else:
                            synthesizeData = " ".join(part["data"])
                            if synthesizeData.strip() == "":
                                continue
                            print("synthesizing " + synthesizeData)
                            voice.synthesize(text=synthesizeData, wav_file=audio_bytes, **synthesizeArgs)

                    silenceLength = int(synthesizeArgs['sentence_silence'] * 11025)
                    silenceBuffer = bytes(bytearray([0x00, 0x00]) * silenceLength)
                    audio_bytes.writeframes(silenceBuffer)

            cache[md5hash] = {
                "audio": wavIO.getvalue(),
                "timestamp": time()
            }
            self.writeAudio(wavIO.getvalue())
            cleanCache()

if __name__ == "__main__":        
    webServer = HTTPServer((settings["http"]["ip"], settings["http"]["port"]), MyServer)
    print("Server started http://%s:%s" % (settings["http"]["ip"], settings["http"]["port"]))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")