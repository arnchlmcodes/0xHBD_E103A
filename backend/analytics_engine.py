import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel

# Configuration
DATA_DIR = Path("user_data")
HISTORY_FILE = DATA_DIR / "quiz_history.json"

class QuizResult(BaseModel):
    topic: str
    score: int
    total_questions: int
    date: str  # ISO format
    weak_subtopics: List[str] = []

def _load_history() -> List[Dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def _save_history(history: List[Dict]):
    DATA_DIR.mkdir(exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

def save_quiz_result(result: QuizResult):
    """Save a new quiz result to history"""
    history = _load_history()
    # Add simple ID
    record = result.dict()
    record['id'] = len(history) + 1
    history.append(record)
    _save_history(history)
    return record

def get_analytics_dash_data():
    """
    Process history to return:
    1. Spiderweb data (Topic v/s Average Score %)
    2. Recent Activity
    3. Weakest Topics
    """
    history = _load_history()
    if not history:
        return {
            "spider_data": [],
            "recent_activity": [],
            "weakest_topics": []
        }

    # 1. Calculate Topic Scores
    topic_stats = {}
    for entry in history:
        t = entry['topic']
        score = entry['score']
        total = entry['total_questions']
        percentage = (score / total) * 100 if total > 0 else 0
        
        if t not in topic_stats:
            topic_stats[t] = {'sum_pct': 0, 'count': 0}
        
        topic_stats[t]['sum_pct'] += percentage
        topic_stats[t]['count'] += 1

    spider_data = []
    weakest_list = []
    
    for topic, stats in topic_stats.items():
        avg_score = round(stats['sum_pct'] / stats['count'], 1)
        spider_data.append({
            "subject": topic,
            "A": avg_score,
            "fullMark": 100
        })
        
        if avg_score < 70:  # Threshold for "Weak"
            weakest_list.append({"topic": topic, "score": avg_score})

    # Sort weakest
    weakest_list.sort(key=lambda x: x['score'])

    return {
        "spider_data": spider_data,
        "recent_activity": history[-5:], # Last 5
        "weakest_topics": weakest_list
    }

def get_recommendations(weak_topics: List[str], qa_system=None):
    """
    Use RAG/Vector DB to find related concepts for weak topics.
    """
    recommendations = []
    
    # If no QA system provided, just return generic advice
    if not qa_system:
        # Fallback if system not initialized
        for t in weak_topics:
            recommendations.append({
                "topic": t,
                "suggestion": f"Review chapter on {t}",
                "type": "General"
            })
        return recommendations

    for topic_name in weak_topics:
        # Search vector DB for 'prerequisites' or 'summary' of this topic
        # to find related concepts.
        try:
            # We ask the system for "Key concepts in [Topic]"
            query = f"Key concepts and prerequisites for {topic_name}"
            results = qa_system.ask(query, n_results=2)
            
            # Extract distinct chapter names from sources
            related_chapters = set()
            if results.get('sources'):
                for src in results['sources']:
                     # Assuming source metadata has 'chapter' or 'topic'
                     # 'topic' in chunks is usually specific section header
                     related_chapters.add(src.get('topic', 'Unknown Chapter'))
            
            rec_text = f"Focus on: {', '.join(list(related_chapters)[:3])}"
            
            recommendations.append({
                "topic": topic_name,
                "suggestion": rec_text,
                "sources": results.get('sources', [])[:2] # Return top 2 source chunks
            })
            
        except Exception as e:
            print(f"Error getting recs for {topic_name}: {e}")
            recommendations.append({
                "topic": topic_name,
                "suggestion": "Review core concepts.",
                "sources": []
            })
            
    return recommendations
