I had to add a try/except clause to a part of the `synthesize` class function in Piper's `voice.py` so a wave file buffer would be maintained through splitting sentences apart. I've included the part to replace as a diff against the original.
If upstream ever changes, add a `try` clause before the wave options are set, and just have it `pass` if setting the options fail (as you can only set settings on wave buffers once).

`voice.py` is located in `(venv)/lib/python3.11/site-packages/piper`