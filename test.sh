#!/bin/sh

SAY_STRING='the black parrot'
MODEL_PATH='venv/en_US-libritts-high.onnx'

SPEAKER_ID=500
NOISE_SCALE=0.2
LENGTH_SCALE=1.4
NOISE_WIDTH=0.1
SENTENCE_SILENCE=0.33

echo $SAY_STRING | \
	venv/bin/piper --model $MODEL_PATH \
		-s $SPEAKER_ID \
		--length-scale $LENGTH_SCALE \
		--noise-scale $NOISE_SCALE \
		--noise-w $NOISE_WIDTH \
		--sentence-silence $SENTENCE_SILENCE \
	--output-raw | \
		aplay -r 22050 -f S16_LE -t raw -