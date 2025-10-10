{
    "input": {
        "text": "He was happy.",
        "has_audio": true,
        "transcribed_text": "He was happy."
    },
    "phoneme": {
        "pred_phones": [
            "HH",
            "IY",
            "W",
            "AA",
            "Z",
            "HH",
            "AE",
            "P",
            "IY"
        ],
        "ref": {
            "text": "He was happy.",
            "phones": [
                "'",
                "HH",
                "IY",
                "'",
                "'",
                "W",
                "AA",
                "Z",
                "'",
                "'",
                "HH",
                "AE",
                "P",
                "IY",
                "'"
            ],
            "words": [
                {
                    "word": "he",
                    "phones": [
                        "'",
                        "HH",
                        "IY",
                        "'"
                    ]
                },
                {
                    "word": "was",
                    "phones": [
                        "'",
                        "W",
                        "AA",
                        "Z",
                        "'"
                    ]
                },
                {
                    "word": "happy",
                    "phones": [
                        "'",
                        "HH",
                        "AE",
                        "P",
                        "IY",
                        "'"
                    ]
                }
            ]
        },
        "align": {
            "ops_raw": [
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 0,
                    "j": 0
                },
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 3,
                    "j": 2
                },
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 4,
                    "j": 2
                },
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 8,
                    "j": 5
                },
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 9,
                    "j": 5
                },
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 14,
                    "j": 9
                }
            ],
            "per_strict": 40
        },
        "sle": {
            "ops_after_rules": [
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 0,
                    "j": 0
                },
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 3,
                    "j": 2
                },
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 4,
                    "j": 2
                },
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 8,
                    "j": 5
                },
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 9,
                    "j": 5
                },
                {
                    "op": "D",
                    "g": "'",
                    "p": null,
                    "i": 14,
                    "j": 9
                }
            ],
            "dropped_by_rules": [],
            "per_sle": 40
        },
        "wer": 100,
        "word_analysis": [
            {
                "word": "he",
                "is_correct": false,
                "phoneme_errors": [
                    {
                        "op": "D",
                        "g": "'",
                        "p": null,
                        "i": 0,
                        "j": 0
                    },
                    {
                        "op": "D",
                        "g": "'",
                        "p": null,
                        "i": 3,
                        "j": 2
                    }
                ]
            },
            {
                "word": "was",
                "is_correct": false,
                "phoneme_errors": [
                    {
                        "op": "D",
                        "g": "'",
                        "p": null,
                        "i": 4,
                        "j": 2
                    },
                    {
                        "op": "D",
                        "g": "'",
                        "p": null,
                        "i": 8,
                        "j": 5
                    }
                ]
            },
            {
                "word": "happy",
                "is_correct": false,
                "phoneme_errors": [
                    {
                        "op": "D",
                        "g": "'",
                        "p": null,
                        "i": 9,
                        "j": 5
                    },
                    {
                        "op": "D",
                        "g": "'",
                        "p": null,
                        "i": 14,
                        "j": 9
                    }
                ]
            }
        ],
        "weakness_categories": []
    },
    "grammar": {
        "id": "utt_8dfcaf83",
        "input": "He was happy.",
        "model": {
            "hf_id": "vennify/t5-base-grammar-correction",
            "device": "cpu"
        },
        "gec": {
            "raw_corrected": "He was happy.",
            "edits": [],
            "final_text": "He was happy."
        },
        "guardrails": [],
        "metrics": {
            "latency_ms": 1772
        }
    }
}