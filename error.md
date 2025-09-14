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
                "HH",
                "IY",
                "W",
                "AA",
                "Z",
                "HH",
                "AE",
                "P",
                "IY",
                "."
            ]
        },
        "align": {
            "ops_raw": [
                {
                    "op": "D",
                    "g": ".",
                    "p": null,
                    "i": 9,
                    "j": 9
                }
            ],
            "per_strict": 10.0
        },
        "sle": {
            "ops_after_rules": [
                {
                    "op": "D",
                    "g": ".",
                    "p": null,
                    "i": 9,
                    "j": 9
                }
            ],
            "dropped_by_rules": [],
            "per_sle": 10.0
        }
    },
    "grammar": {
        "id": "utt_b46af085",
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
            "latency_ms": 1048
        }
    }
}

from unidecode import unidecode
import re, inflect
NUM = inflect.engine()

def norm_text(s: str) -> str:
    s = unidecode((s or "")).lower()                                    # ASCII fold + lowercase
    s = re.sub(r"\d+", lambda m: NUM.number_to_words(m.group()).replace("-", " "), s)  # 123 -> "one two three"
    s = re.sub(r"[^a-z' ]+", " ", s)                                    # drop everything except a–z, space, apostrophe
    s = re.sub(r"\s+", " ", s).strip()                                  # collapse spaces
    return s
