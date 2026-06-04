def score_text_risk(features):
    weights = {
        "suspicious_url_count": 22,
        "url_count": 6,
        "phone_count": 5,
        "money_mention_count": 14,
        "exclamation_count": 2,
        "uppercase_word_count": 1,
    }

    score = 8
    reasons = []

    for key, weight in weights.items():
        contribution = min(features.get(key, 0) * weight, 28)
        score += contribution

    if features["urgency_terms"]:
        score += min(len(features["urgency_terms"]) * 9, 24)
        reasons.append("Uses urgency or pressure language.")

    if features["money_terms"]:
        score += min(len(features["money_terms"]) * 8, 24)
        reasons.append("Mentions payment, money, reward, salary, or banking terms.")

    if features["trust_terms"]:
        score += min(len(features["trust_terms"]) * 5, 15)
        reasons.append("Uses trust-building language commonly found in scams.")

    if features["suspicious_url_count"]:
        reasons.append("Contains one or more suspicious-looking URLs.")
    elif features["url_count"]:
        reasons.append("Contains links that should be verified before clicking.")

    if features["phone_count"]:
        reasons.append("Includes phone numbers, which are common in social-engineering messages.")

    if features["money_mention_count"]:
        reasons.append("Contains explicit money amounts or payment references.")

    if features["word_count"] < 8 and (features["url_count"] or features["phone_count"]):
        score += 10
        reasons.append("Very short message with contact/link payload.")

    score = max(0, min(round(score), 100))

    if score >= 75:
        level = "High"
    elif score >= 45:
        level = "Medium"
    else:
        level = "Low"

    if not reasons:
        reasons.append("No strong scam indicators found in the text, but verification is still recommended.")

    return {
        "risk_score": score,
        "risk_level": level,
        "model_name": "TruthShield heuristic baseline v1",
        "top_reasons": reasons[:6],
    }

