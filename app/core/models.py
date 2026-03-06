from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Company:
    company_id : str
    company_name : str
    website : str = 'N/A'
    country : str = 'N/A'
    industry : str = 'N/A'
    score : int = 0
    reasons : str = ""

    # returns dictionary of fields for Pandas
    def to_dict(self) -> dict:
        return self.__dict__
    
@dataclass
class ScoringRule:
    word: str
    points: int