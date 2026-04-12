import pytest
from core.utils import clean_str 

# ARRANGE: table of dirty strings and their expected cleaned versions
@pytest.mark.parametrize("dirty_str, expected_cleaned_str", [
    (" Google LLC                  ", "Google"), 
    (" Apple Inc", "Apple"), 
    ("   Microsoft Corporation   ", "Microsoft"), 
    ("Amazon.com, Inc.   ", "Amazon.com"), 
    ("Facebook, Inc.   ", "Facebook"), 
    ("   limited OpenAI Ltd.   ", "Openai"), 
    ("   alphabet Inc.   ", "Alphabet"), 
    ("   tesla, Inc.   ", "Tesla"), 
    ("microsoft corp   ", "Microsoft"), 
    (" My company GmbH   ", "My")
])
def test_clean_str(dirty_str, expected_cleaned_str):
    
    # ACT
    cleaned_str = clean_str(dirty_str)

    # ASSERT

    assert cleaned_str == expected_cleaned_str, f"Expected '{expected_cleaned_str}' but got '{cleaned_str}' for input '{dirty_str}'"