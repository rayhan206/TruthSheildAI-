import json
import re


def retrieve_context(root, text, features, limit=3):
    kb_path = root / "knowledge_base" / "scam_patterns.json"
    patterns = json.loads(kb_path.read_text(encoding="utf-8"))

    query_terms = set(_tokens(text))
    query_terms.update(features.get("urgency_terms", []))
    query_terms.update(features.get("money_terms", []))
    query_terms.update(features.get("trust_terms", []))

    scored = []
    for item in patterns:
        item_terms = set(_tokens(" ".join([
            item["title"],
            item["description"],
            " ".join(item["signals"]),
        ])))
        overlap = len(query_terms.intersection(item_terms))
        if features.get("url_count") and "link" in item_terms:
            overlap += 2
        if features.get("money_mention_count") and "payment" in item_terms:
            overlap += 2
        scored.append((overlap, item))

    scored.sort(key=lambda row: row[0], reverse=True)
    return [
        {
            "title": item["title"],
            "description": item["description"],
            "signals": item["signals"],
            "recommended_action": item["recommended_action"],
            "match_score": score,
        }
        for score, item in scored[:limit]
        if score > 0
    ] or [
        {
            "title": "General verification",
            "description": "When evidence is limited, verify through official channels before clicking links, paying money, or sharing personal data.",
            "signals": ["Unknown sender", "Unverified request", "External links or attachments"],
            "recommended_action": "Contact the organization through its official website or known phone number.",
            "match_score": 0,
        }
    ]


def _tokens(value):
    return re.findall(r"[a-zA-Z]{3,}", value.lower())

