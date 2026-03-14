from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class SearchMode (Enum):
    INDIVIDUAL = 1
    BY_FILE = 2
    NOT_DEFINED = 3

@dataclass
class Company:
    company_id : str
    company_name : str
    website : str = 'N/A'
    country : str = 'N/A'
    industry : list[str] = field(default_factory=list)
    score : int = 0
    reasons : str = ""
    description : str = ""

    # returns dictionary of fields for Pandas
    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        if isinstance(d.get('industry'), list):
            d['industry'] = ", ".join(d['industry'])
        return d
    
@dataclass
class ScoringRule:
    word: str
    points: int