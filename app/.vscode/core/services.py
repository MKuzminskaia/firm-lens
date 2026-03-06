import requests 
from .models import Company

class WikidataService:
    def __init__(self):
        self.url = "https://query.wikidata.org/sparql"
        self.headers = {
            'User-Agent': 'FirmLensBot/1.0 (blackmarka@gmail.com)', 
            'Accept': 'application/sparql-results+json'
        }

    def search_companies(self, name: str) -> list[Company]:
        pass

    def enrich_company(self, company_id: str) -> Company:
        pass

class ScorerService:
    @staticmethod
    def calculate_score(text: str, pos_rules: dict, neg_rules: dict) -> tuple[int, str]:
        total_score = 0
        reasons = []
        text_lower = text.lower()
        
        for word, pts in pos_rules.items():
            if word in text_lower:
                total_score += pts
                reasons.append(f"+{pts}:{word}")
        
        for word, pts in neg_rules.items():
            if word in text_lower:
                total_score += pts
                reasons.append(f"{pts}:{word}")
                
        return total_score, "; ".join(reasons)