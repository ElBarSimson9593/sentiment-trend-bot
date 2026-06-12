from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


_NEGATIVE_HINTS = ("estafa", "pésima", "pesima", "horrible", "nunca más", "nunca mas", "fraude")
_POSITIVE_HINTS = ("excelente", "recomendable", "profesionales", "amable", "rápido", "rapido")


def analyze_text(text: str) -> tuple[float, str]:
    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]
    lower = text.lower()

    if any(hint in lower for hint in _NEGATIVE_HINTS):
        compound = min(compound, -0.45)
    elif any(hint in lower for hint in _POSITIVE_HINTS):
        compound = max(compound, 0.45)

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return compound, label
