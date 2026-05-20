const data = {
  "blocks": {
    "languageVersion": 0,
    "blocks": [
      {
        "type": "tecla_repeat_forever",
        "id": "gen_loop",
        "x": 50,
        "y": 50,
        "inputs": {
          "DO": {
            "block": {
              "type": "tecla_play_note",
              "id": "rand_note",
              "inputs": {
                "NOTE": {
                  "shadow": {
                    "type": "math_number",
                    "fields": { "NUM": "60" }
                  },
                  "block": {
                    "type": "tecla_math_random_int",
                    "id": "rand_val",
                    "inputs": {
                      "FROM": {
                        "shadow": {
                          "type": "math_number",
                          "fields": { "NUM": "48" }
                        }
                      },
                      "TO": {
                        "shadow": {
                          "type": "math_number",
                          "fields": { "NUM": "84" }
                        }
                      }
                    }
                  }
                },
                "VELOCITY": {
                  "shadow": {
                    "type": "math_number",
                    "fields": { "NUM": "100" }
                  }
                },
                "DURATION": {
                  "shadow": {
                    "type": "math_number",
                    "fields": { "NUM": "0.2" }
                  }
                }
              },
              "next": {
                "block": {
                  "type": "tecla_wait",
                  "id": "wait_rand",
                  "inputs": {
                    "TIME": {
                      "shadow": {
                        "type": "math_number",
                        "fields": { "NUM": "0.1" }
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
