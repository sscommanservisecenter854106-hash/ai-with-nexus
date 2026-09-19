import os
import re
import math
import json
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any, Tuple
from config import UPLOAD_DIR, DATA_DIR

INDEX_FILE = DATA_DIR / "rag_index.json"

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
    "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's",
    "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs",
    "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
}

def tokenize(text: str) -> List[str]:
    # Lowercase and extract alphanumeric words filtered by stop words
    words = re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    return filtered if filtered else words


class DocumentRAG:
    def __init__(self, index_path: Path = INDEX_FILE):
        self.index_path = index_path
        self.documents: List[Dict[str, Any]] = [] # [{id, source, text, tokens, doc_len}]
        self.df: Counter = Counter() # Document frequencies of terms
        self.total_docs: int = 0
        self.avg_doc_len: float = 0.0
        self.load_index()

    def load_index(self):
        if self.index_path.exists():
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                    self._rebuild_stats()
            except Exception:
                self.documents = []
                self._rebuild_stats()

    def save_index(self):
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump({"documents": self.documents}, f, indent=2)

    def _rebuild_stats(self):
        self.total_docs = len(self.documents)
        self.df = Counter()
        total_len = 0
        for doc in self.documents:
            tokens = set(doc.get("tokens", []))
            for t in tokens:
                self.df[t] += 1
            total_len += doc.get("doc_len", 0)
        self.avg_doc_len = (total_len / self.total_docs) if self.total_docs > 0 else 0.0

    def add_document(self, filename: str, content: str, chunk_size: int = 400, overlap: int = 50) -> int:
        words = content.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            chunks.append(chunk_text)
            if i + chunk_size >= len(words):
                break
            i += (chunk_size - overlap)

        added_count = 0
        for idx, chunk in enumerate(chunks):
            tokens = tokenize(chunk)
            doc_entry = {
                "id": f"{filename}_{idx}",
                "source": filename,
                "text": chunk,
                "tokens": tokens,
                "doc_len": len(tokens)
            }
            self.documents.append(doc_entry)
            added_count += 1

        self._rebuild_stats()
        self.save_index()
        return added_count

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.documents or not query.strip():
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # BM25 Scoring parameters
        k1 = 1.5
        b = 0.75
        scores: List[Tuple[float, Dict[str, Any]]] = []

        for doc in self.documents:
            score = 0.0
            doc_tokens = doc["tokens"]
            doc_len = doc["doc_len"]
            doc_term_freq = Counter(doc_tokens)

            for q_term in query_tokens:
                if q_term in doc_term_freq:
                    tf = doc_term_freq[q_term]
                    df_val = self.df.get(q_term, 1)
                    # IDF formula
                    idf = math.log(1 + (self.total_docs - df_val + 0.5) / (df_val + 0.5))
                    # Term frequency saturation
                    num = tf * (k1 + 1)
                    denom = tf + k1 * (1 - b + b * (doc_len / (self.avg_doc_len or 1)))
                    score += idf * (num / denom)

            if score > 0.1:
                scores.append((score, doc))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, doc in scores[:top_k]:
            results.append({
                "score": round(score, 3),
                "source": doc["source"],
                "text": doc["text"]
            })
        return results

    def list_sources(self) -> List[Dict[str, Any]]:
        sources: Dict[str, int] = {}
        for doc in self.documents:
            src = doc["source"]
            sources[src] = sources.get(src, 0) + 1
        return [{"filename": k, "chunks": v} for k, v in sources.items()]

    def clear(self):
        self.documents = []
        self._rebuild_stats()
        self.save_index()
