import pytest
import requests

from unittest.mock import patch
from core.services import ScorerService, WikidataService
from core.models import Company

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


#----------------------------------------------------------------------------------------------------------------------------------
# Tests for the search_companies method in WikidataService

def test_search_empty_company_name():
    #ARRANGE: Preparing data for the test
    wikiService = WikidataService()

    #ACT & ASSERT: Calling the method we want to test and Checking if the results are expected  
    with pytest.raises (ValueError, match="Company Name is empty"):
       results = wikiService.search_companies("", "", "")  # Testing with an empty string should raise an exception


#ARRANGE: Preparing data for the test
@pytest.mark.parametrize("company_name, website, country, result_exists", [
    ("Google", "https://about.google/", "United States", True),
    ("Google", "https://about.google/", "", True),
    ("Google", "", "", True),
    ("123456", "fgvhbj", "cfgvhbjn", False)
])
def test_search_companies (company_name, website, country, result_exists):
    # ARRANGE: Preparing data for the test
    wikiService = WikidataService()

    # ACT: Calling the method we want to test
    
    results = wikiService.search_companies(company_name, website, country)  # Testing with valid inputs should return results
    
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

def test_search_companies_network_timeout():
    # ARRANGE: Preparing data for the test
    wikiService = WikidataService()

    # Mock the requests.get method to simulate a network timeout and 
    # Mock the st.error method to prevent actual error messages from being displayed during testing
    with patch('core.services.requests.get') as mock_get, \
        patch('core.services.st.error') as mock_st_error: 
        mock_get.side_effect = requests.exceptions.Timeout("Wikidata API server timeout")

        # ACT: Calling the method we want to test 
        results = wikiService.search_companies("TimeoutCompany", "", "")

        # ASSERT: checking results        
        # result of function should be an empty list when a timeout occurs
        assert results == [], f"Expected an empty list when a timeout occurs, but got {results}"    
        #st.error should have been called to log the error message once
        mock_st_error.assert_called_once()
        mock_st_error.assert_called_with("Search failed: Wikidata API server timeout")


def test_rank_candidates():
    #ARRANGE: prepare data for test
    wikiService = WikidataService()
    boost_keywords = ["technology", "internet", "ai"]
    penalty_keywords = ["gambling", "adult", "general"]

    TestCompanys = [
                    Company( company_id="Q9531", company_name="Google", description="Google is a multinational technology company specializing in internet-related services and products."),
                    Company( company_id="Q9532", company_name="Google", description="Google is an AI research and deployment company dedicated to ensuring that artificial general intelligence benefits all of humanity."),
                    Company( company_id="Q9533", company_name="Google", description="")
                ]
    
        
    #ACT: call _rank_candidates for testimg
    result = wikiService._rank_candidates(TestCompanys, boost_keywords, penalty_keywords)
    
    #ASSERT: check if the results are as expected 
    assert isinstance(result, list), "Expected result to be a list"
    assert len(result) == 2, "Expected exactly two companies in the result"

    assert result[0].company_id == "Q9531", f"Expected company_id 'Q9531' to be ranked highest, but got '{result[0].company_id}'"
    assert result[1].company_id == "Q9533", f"Expected company_id 'Q9533', but got '{result[1].company_id}'"
    
