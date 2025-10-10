{
    "input": {
        "text": "as mentioned previously.",
        "has_audio": true,
        "transcribed_text": "as mentioned previously."
    },
    "phoneme": {
        "pred_phones": [
            "AE",
            "Z",
            "M",
            "EH",
            "N",
            "CH",
            "JH",
            "AH",
            "N",
            "P",
            "R",
            "IY",
            "V",
            "IY",
            "AH",
            "S",
            "L",
            "IY"
        ],
        "phoneme_error_rate": 11.11111111111111,
        "word_analysis": [
            {
                "word": "as",
                "phoneme_errors": [],
                "weakness_categories": []
            },
            {
                "word": "mentioned",
                "phoneme_errors": [
                    {
                        "op": "I",
                        "g": null,
                        "p": "CH",
                        "i": 5,
                        "j": 5
                    },
                    {
                        "op": "S",
                        "g": "SH",
                        "p": "JH",
                        "i": 5,
                        "j": 6
                    }
                ],
                "weakness_categories": []
            },
            {
                "word": "previously",
                "phoneme_errors": [],
                "weakness_categories": []
            }
        ],
        "weakness_categories": []
    },
    "grammar": {
        "input": "as mentioned previously.",
        "gec": {
            "raw_corrected": "As mentioned previously.",
            "edits": [
                {
                    "type": "ORTH",
                    "span_src": {
                        "start_tok": 0,
                        "end_tok": 1,
                        "text": "as"
                    },
                    "replacement": "As"
                }
            ],
            "final_text": "As mentioned previously."
        },
        "guardrails": [],
        "weakness_categories": [
            "capitalization"
        ]
    }
}