from core.services import ScorerService

def test_calculate_score_mixed_rules():
    # ARRANGE: Preparing data for the test
    text = "We are an AI clinic focused on health, but we do not support gambling."
    
    pos_rules = [
        {"Keyword": "health", "Points": 25},
        {"Keyword": "clinic", "Points": 20},
        {"Keyword": "ai", "Points": 10}
    ]
    
    neg_rules = [
        {"Keyword": "gambling", "Points": -100}
    ]

    # ACT: Calling the method we want to test
    score, reasons = ScorerService.calculate_score(text, pos_rules, neg_rules)

    # ASSERT: Checking if the results are as expected
    # 25 + 20 + 10 - 100 = -45
    assert score == -45
    
    # We expect exactly 4 rules to have been triggered (3 positive and 1 negative)
    assert len(reasons.split("; ")) == 4
    
    # Check that the specific reason with the correct score is in the report
    assert "+health:25" in reasons