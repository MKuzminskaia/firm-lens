import pytest

from core.services import ScorerService, WikidataService

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


def test_search_empty_company_name():
    #ARRANGE: Preparing data for the test
    WikiService = WikidataService()

    #ACT & ASSERT: Calling the method we want to test and Checking if the results are expected  
    with pytest.raises (ValueError, match="Company Name is empty"):
       results = WikiService.search_companies("", "", "")  # Testing with an empty string should raise an exception



#ARRANGE: Preparing data for the test
@pytest.mark.parametrize("company_name, website, country, result_exists", [
    ("Google", "https://about.google/", "United States", True),
    ("Google", "https://about.google/", "", True),
    ("Google", "", "", True),
    ("123456", "fgvhbj", "cfgvhbjn", False)
])
def test_search_companies (company_name, website, country, result_exists):
    # ARRANGE: Preparing data for the test
    WikiService = WikidataService()

    # ACT: Calling the method we want to test
    
    results = WikiService.search_companies(company_name, website, country)  # Testing with valid inputs should return results
    
    # ASSERT: Checking if the results are as expected

    assert isinstance(results, list), "Expected results to be a list"

    if result_exists:
        assert len(results) > 0, "Expected at least one result for a valid company name"
        assert results[0].company_name is not None, "Expected 'company_name' field in the results"
        assert results[0].website is not None, "Expected 'website' field in the results" 
        assert results[0].country is not None, "Expected 'country' field in the results"
        assert results[0].industry is not None, "Expected 'industry' field in the results"
        assert results[0].description is not None, "Expected 'description' field in the results"
    else:
        assert len(results) == 0, "Expected no results for invalid company name"

    