import pytest


@pytest.fixture(autouse=True)
def no_classifier(monkeypatch):
    """Unit tests never download the classifier; tests that need it pass a fake scorer."""
    monkeypatch.setenv("MERLION_CLASSIFIER", "off")
