
const data = {
    "blocks": {
        "languageVersion": 0,
        "blocks": [
            {
                "type": "tecla_repeat_forever",
                "id": "loop",
                "x": 50,
                "y": 50,
                "inputs": {
                    "DO": {
                        "block": {
                            "type": "tecla_oscillator",
                            "id": "osc",
                            "fields": { "WAVEFORM": "SAWTOOTH" },
                            "inputs": {
                                "FREQUENCY": { "shadow": { "type": "math_number", "fields": { "NUM": "440" } } },
                                "AMPLITUDE": { "shadow": { "type": "math_number", "fields": { "NUM": "127" } } }
                            },
                            "next": {
                                "block": {
                                    "type": "tecla_lfo",
                                    "id": "lfo",
                                    "fields": { "WAVEFORM": "SINE", "TARGET": "PITCH" },
                                    "inputs": {
                                        "RATE": { "shadow": { "type": "math_number", "fields": { "NUM": "5" } } },
                                        "DEPTH": { "shadow": { "type": "math_number", "fields": { "NUM": "80" } } }
                                    },
                                    "next": {
                                        "block": {
                                            "type": "tecla_play_note",
                                            "id": "note1",
                                            "inputs": {
                                                "NOTE": { "shadow": { "type": "math_number", "fields": { "NUM": "50" } } },
                                                "VELOCITY": { "shadow": { "type": "math_number", "fields": { "NUM": "127" } } },
                                                "DURATION": { "shadow": { "type": "math_number", "fields": { "NUM": "0.5" } } }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]
    }
};

console.log(JSON.stringify(data));
