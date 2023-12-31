const fs = require("fs");
const root = "/tmp/tts_output_ogg";

var out = {};

fs.readdir(root, function(err, voices) {
	for(let i in voices) {
		let voice = voices[i];
		out[voice] = [];

		fs.readdir(`${root}/${voice}`, function(err, examples) {
			for(let k in examples) {
				let example = examples[k];

				out[voice].push({
					name: `${example.split(".")[0]}`,
					file: `${voice}/${example}`,
					added: Date.now(),
					author: "Piper TTS"
				});
			}
		});
	}

	setTimeout(function() {
		fs.writeFileSync(`${root}/previewer_db.json`, JSON.stringify(out));
	}, 100);
});