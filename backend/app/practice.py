"""
Practice sentence selection logic for pronunciation training.
Analyzes user weaknesses and selects targeted practice sentences.
"""

from __future__ import annotations
import json
import random
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

from . import db


# Cache for sentence bank (load once)
_sentence_bank = None


def load_sentence_bank() -> Dict[str, Any]:
    """Load practice sentences with phoneme data from JSON file."""
    global _sentence_bank
    
    if _sentence_bank is not None:
        return _sentence_bank
    
    json_path = Path(__file__).parent / "practice_sentences_with_phonemes.json"
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Organize by level for faster lookup
    organized = {
        "BEGINNER": [],
        "INTERMEDIATE": [],
        "ADVANCED": []
    }
    
    for sent in data.get("sentences", []):
        level = sent["level"].upper()
        if level in organized:
            organized[level].append(sent)
    
    _sentence_bank = organized
    return _sentence_bank


async def analyze_user_weaknesses(user_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Analyze user's pronunciation weaknesses from recent phoneme results.
    
    Returns:
        {
            "weak_phonemes": ["P", "TH", "R"],  # Top problematic phonemes
            "phoneme_error_counts": {"P": 15, "TH": 12, "R": 8},
            "error_type_distribution": {"Deletion": 45, "Insertion": 30, "Substitution": 25},
            "avg_per_sle": 17.5,
            "total_attempts": 50
        }
    """
    
    # Get recent phoneme results
    results = await db.get_phoneme_results_last_n_days(user_id, days=30)
    
    if not results:
        # No history, return empty
        return {
            "weak_phonemes": [],
            "phoneme_error_counts": {},
            "error_type_distribution": {},
            "avg_per_sle": None,
            "total_attempts": 0
        }
    
    phoneme_errors = Counter()
    error_types = Counter()
    per_scores = []
    
    for row in results:
        # Parse ops_raw (phoneme operations)
        ops = row.ops_raw
        if isinstance(ops, str):
            try:
                ops = json.loads(ops)
            except json.JSONDecodeError:
                continue
        
        if not ops:
            continue
        
        for op in ops:
            op_type = op.get("op")
            
            if op_type == "D":  # Deletion
                phoneme = op.get("g")  # Gold/correct phoneme that was deleted
                if phoneme:
                    phoneme_errors[phoneme] += 1
                    error_types["Deletion"] += 1
                    
            elif op_type == "S":  # Substitution
                phoneme = op.get("g")  # Gold phoneme that was replaced
                if phoneme:
                    phoneme_errors[phoneme] += 1
                    error_types["Substitution"] += 1
                    
            elif op_type == "I":  # Insertion
                phoneme = op.get("p")  # Predicted phoneme that was inserted
                if phoneme:
                    phoneme_errors[phoneme] += 1
                    error_types["Insertion"] += 1
        
        # Track PER scores
        if row.per_sle is not None:
            per_scores.append(row.per_sle)
    
    # Get top 10 problematic phonemes
    weak_phonemes = [p for p, count in phoneme_errors.most_common(10)]
    
    # Calculate average PER
    avg_per = sum(per_scores) / len(per_scores) if per_scores else None
    
    return {
        "weak_phonemes": weak_phonemes,
        "phoneme_error_counts": dict(phoneme_errors),
        "error_type_distribution": dict(error_types),
        "avg_per_sle": avg_per,
        "total_attempts": len(results)
    }


def score_sentence_for_user(
    sentence: Dict[str, Any],
    weak_phonemes: List[str]
) -> float:
    """
    Score a sentence based on how many weak phonemes it contains.
    Higher score = better match for user's weaknesses.
    
    Args:
        sentence: Sentence dict with 'phoneme_counts' field
        weak_phonemes: List of phonemes the user struggles with
        
    Returns:
        Relevance score (0.0 to infinity, higher is better)
    """
    
    phoneme_counts = sentence.get("phoneme_counts", {})
    
    score = 0.0
    
    # Weight by position in weakness list (first = most important)
    for i, weak_phoneme in enumerate(weak_phonemes[:5]):  # Top 5 weaknesses
        weight = 5 - i  # 5, 4, 3, 2, 1
        count = phoneme_counts.get(weak_phoneme, 0)
        score += count * weight
    
    return score


async def select_practice_sentences(
    user_id: str,
    count: int = 5,
    user_level: str = "BEGINNER"
) -> List[Dict[str, Any]]:
    """
    Select practice sentences for a user based on their weaknesses.
    
    Args:
        user_id: User identifier
        count: Number of sentences to return (default 5)
        user_level: User's proficiency level (BEGINNER, INTERMEDIATE, ADVANCED)
        
    Returns:
        List of selected sentences with relevance scores
    """
    
    # Load sentence bank
    sentence_bank = load_sentence_bank()
    
    # Get sentences for user's level
    level_sentences = sentence_bank.get(user_level.upper(), [])
    
    if not level_sentences:
        # Fallback to BEGINNER if level not found
        level_sentences = sentence_bank.get("BEGINNER", [])
    
    # Analyze user weaknesses
    weaknesses = await analyze_user_weaknesses(user_id)
    weak_phonemes = weaknesses["weak_phonemes"]
    
    if not weak_phonemes:
        # No weakness data, return random sentences
        selected = random.sample(level_sentences, min(count, len(level_sentences)))
        return [
            {
                **sent,
                "relevance_score": 0.0,
                "match_type": "random"
            }
            for sent in selected
        ]
    
    # Score all sentences
    scored_sentences = []
    for sent in level_sentences:
        score = score_sentence_for_user(sent, weak_phonemes)
        scored_sentences.append({
            **sent,
            "relevance_score": score
        })
    
    # Sort by score (highest first)
    scored_sentences.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # Select mix: 70% targeted (high score) + 30% general (lower score/random)
    targeted_count = int(count * 0.7)  # 3-4 sentences
    general_count = count - targeted_count  # 1-2 sentences
    
    # Get targeted sentences (highest scores)
    targeted = scored_sentences[:targeted_count]
    for sent in targeted:
        sent["match_type"] = "targeted"
    
    # Get general sentences (from middle/lower scores for variety)
    remaining = scored_sentences[targeted_count:]
    if remaining:
        general = random.sample(remaining, min(general_count, len(remaining)))
    else:
        general = []
    
    for sent in general:
        sent["match_type"] = "general"
    
    # Combine
    selected = targeted + general
    
    # Shuffle to mix targeted and general (so targeted aren't always first)
    random.shuffle(selected)
    
    return selected


def format_sentence_for_response(sentence: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Format a sentence for API response."""
    return {
        "id": f"prac_{hash(sentence['text']) % 1000000}",
        "order": index + 1,
        "text": sentence["text"],
        "level": sentence["level"],
        "phonemes": sentence["phonemes"],
        "phoneme_counts": sentence["phoneme_counts"],
        "unique_phonemes": sentence["unique_phonemes"],
        "total_phonemes": sentence["total_phonemes"],
        "relevance_score": round(sentence.get("relevance_score", 0.0), 2),
        "match_type": sentence.get("match_type", "random"),
        "source": sentence.get("source", ""),
    }
