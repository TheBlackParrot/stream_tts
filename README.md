This is the TTS system my Twitch streams use during ad breaks and while I'm just menuing around in whatever game I'm streaming. It uses [rhasspy's Piper project](https://github.com/rhasspy/piper) as the TTS backend, no data is ever sent "to the cloud".

> [!NOTE]
> You will need to comment out lines that sets audio parameters on `wav_file` in the `synthesize` function in `[venv]/lib/python3.11/site-packages/piper/voice.py`. In my case these were lines 91-93 (`setframerate`, `setsampwidth`, and `setnchannels`)