import re
from urllib.parse import urlparse


URGENCY_TERMS = {
    "urgent", "immediately", "limited", "deadline", "final", "warning",
    "verify now", "act now", "today only", "expire", "blocked", "suspended"
}

MONEY_TERMS = {
    "payment", "pay", "fee", "deposit", "crypto", "bitcoin", "upi",
    "bank", "salary", "prize", "lottery", "refund", "investment",
    "registration fee", "processing fee"
}

TRUST_TERMS = {
    "official", "government", "verified", "guaranteed", "no interview",
    "selected", "congratulations", "confidential", "do not share"
}

SUSPICIOUS_TLDS = {".zip", ".mov", ".top", ".xyz", ".click", ".work", ".support"}


def extract_text_features(text):
    normalized = " ".join(text.lower().split())
    urls = re.findall(r"https?://[^\s)>\]]+|www\.[^\s)>\]]+", normalized)
    phones = re.findall(r"(?:\+?\d[\s-]?){8,}", normalized)
    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", normalized)
    money_mentions = re.findall(r"(?:rs\.?|inr|\$|₹)\s?\d+|\d+\s?(?:rs|inr|rupees|dollars)", normalized)
    exclamations = text.count("!")
    uppercase_words = re.findall(r"\b[A-Z]{3,}\b", text)

    matched_urgency = sorted(term for term in URGENCY_TERMS if term in normalized)
    matched_money = sorted(term for term in MONEY_TERMS if term in normalized)
    matched_trust = sorted(term for term in TRUST_TERMS if term in normalized)
    suspicious_urls = [url for url in urls if _is_suspicious_url(url)]

    word_count = len(re.findall(r"\w+", text))
    avg_word_length = (
        sum(len(word) for word in re.findall(r"\w+", text)) / max(word_count, 1)
    )

    return {
        "word_count": word_count,
        "url_count": len(urls),
        "urls": urls,
        "suspicious_url_count": len(suspicious_urls),
        "suspicious_urls": suspicious_urls,
        "phone_count": len(phones),
        "email_count": len(emails),
        "money_mention_count": len(money_mentions),
        "money_mentions": money_mentions,
        "exclamation_count": exclamations,
        "uppercase_word_count": len(uppercase_words),
        "avg_word_length": round(avg_word_length, 2),
        "urgency_terms": matched_urgency,
        "money_terms": matched_money,
        "trust_terms": matched_trust,
    }


def _is_suspicious_url(url):
    if url.startswith("www."):
        url = "https://" + url
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if any(host.endswith(tld) for tld in SUSPICIOUS_TLDS):
        return True
    if "@" in url or host.count("-") >= 2 or len(host.split(".")[0]) > 25:
        return True
    if any(token in host + path for token in ["login", "verify", "bonus", "claim", "free"]):
        return True
    return False

