from pathlib import Path
from time_profiler.chatbot.nlp_processor import NLPProcessor


def test_parse_time_allocation():
    config_path = Path(__file__).resolve().parents[1] / "config" / "dcri_config.json.example"
    nlp = NLPProcessor(config_path)
    text = "I spent 50% meetings, 30% research, 20% administration"
    result = nlp.parse_time_allocation(text)
    assert result["Meeting"] == 50
    assert result["Research"] == 30
    assert result["Administration"] == 20
