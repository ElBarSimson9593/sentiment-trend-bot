from app.sentiment import analyze_text


def test_positive_text():
    score, label = analyze_text("Absolutely love this service, amazing experience!")
    assert label == "positive"
    assert score > 0


def test_negative_text():
    score, label = analyze_text("Terrible experience, complete scam and waste of money")
    assert label == "negative"
    assert score < 0


def test_neutral_text():
    score, label = analyze_text("The package arrived on Tuesday")
    assert label == "neutral"


def test_spanish_positive_hint():
    score, label = analyze_text("Muy buena atención, muy profesionales.")
    assert label == "positive"
    assert score > 0


def test_spanish_negative_hint():
    score, label = analyze_text("Pésima atención, estafa total.")
    assert label == "negative"
    assert score < 0
