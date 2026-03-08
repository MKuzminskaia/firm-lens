import requests 
from .models import Company
from  core.utils import clean_str
import streamlit as st

class WikidataService:
    def __init__(self):
        self.url = "https://query.wikidata.org/sparql"
        self.headers = {
            'User-Agent': 'FirmLensBot/1.0 (blackmarka@gmail.com)', 
            'Accept': 'application/sparql-results+json'
        }

    # returns a short list of companies that match the parameters 
    #--------------------------------------------------------------------------------------------------------------------------------------------------------
    #@st.cache_data
    def search_companies(self, company_name :str, website: str, country: str) -> list[Company]: 
        company_name = company_name.strip()
        company_name = clean_str(company_name.lower())
        result_info : dict [str, Company] = {}

        if not company_name:
            raise ValueError("Company Name is empty")
        else: 
            query = f"""SELECT DISTINCT ?item ?itemLabel ?website ?countryLabel ?industryLabel WHERE {{
                    ?item rdfs:label "{company_name}"@en ."""
            if website:
                query += f"""?item wdt:P856 "<{website}>" ."""    
            if country:
                query += f"""?item wdt:P17 "{country}"@en ."""    
            query += f"""?item wdt:P31 wd:Q4830453 .
                    OPTIONAL {{ ?item wdt:P856 ?website. }}
                    OPTIONAL {{ ?item wdt:P17 ?country. ?country rdfs:label ?countryLabel. FILTER(LANG(?countryLabel) = "en") }}
                    OPTIONAL {{ ?item wdt:P452 ?industry. ?industry rdfs:label ?industryLabel. FILTER(LANG(?industryLabel) = "en") }}
                    SERVICE wikibase:label {{bd:serviceParam wikibase:language "en". }}
                    }}
                    """
            url = "https://query.wikidata.org/sparql"
            headers = {'User-Agent': 'FirmLensBot/1.0 (blackmarka@gmail.com)', 'Accept': 'application/sparql-results+json'}

            try:
                response = requests.get(url, params = {'query' : query, 'format': 'json'}, headers = headers, timeout=10)
                data = response.json()
                results = data.get('results', {}).get('bindings', [])


                for res in results:
                    one_company_result : Company = Company(
                        company_id = res.get('item', {}).get('value', "N/A"),
                        company_name = res.get('itemLabel', {}).get('value', "N/A"),
                        website = res.get('website', {}).get('value', "N/A"),
                        country = res.get('countryLabel', {}).get('value', "N/A"),
                        industry = [res.get('industryLabel', {}).get('value', "N/A")]
                    )
                    
                    if one_company_result.company_id not in result_info:
                        result_info[one_company_result.company_id] = one_company_result
                    else:
                        if one_company_result.industry[0] != "N/A" and one_company_result.industry[0] not in result_info[one_company_result.company_id].industry:
                            result_info[one_company_result.company_id].industry.append(one_company_result.industry[0])
            except Exception as e:
                #st.error(f"Error enriching {company_name}: {e}") 
                pass
        return list(result_info.values())


    # returns the enriched list of one company by id 
    #--------------------------------------------------------------------------------------------------------------------------------------------------------
    def enrich_company(self, company_id :str, website: str, country: str) -> Company:  #-> dict [str, str]:  #-> Company:
        company_id = company_id.strip()

        result_company : Company

        default_result = {
            'company_id' : company_id,
            'company_name' : country,
            'website' : website,
            'country' : 'N/A',
            'industry' : 'N/A'
        }

        if not company_id or company_id == 'N/A':
            raise ValueError("Company Name is empty")
        else: 
            company_id = company_id.split('/')[-1]
            query = f"""SELECT DISTINCT ?item ?itemLabel ?website ?countryLabel ?industryLabel WHERE {{
                    BIND(wd:{company_id} AS ?item) ."""
            if website:
                query += f"""?item wdt:P856 "<{website}>" ."""    
            if country:
                query += f"""?item wdt:P17 "{country}"@en ."""    
            query += f"""?item wdt:P31 wd:Q4830453 .
                    OPTIONAL {{ ?item wdt:P856 ?website. }}
                    OPTIONAL {{ ?item wdt:P17 ?country. ?country rdfs:label ?countryLabel. FILTER(LANG(?countryLabel) = "en") }}
                    OPTIONAL {{ ?item wdt:P452 ?industry. ?industry rdfs:label ?industryLabel. FILTER(LANG(?industryLabel) = "en") }}
                    SERVICE wikibase:label {{bd:serviceParam wikibase:language "en". }}
                    }}
                    """
            url = "https://query.wikidata.org/sparql"
            headers = {'User-Agent': 'FirmLensBot/1.0 (blackmarka@gmail.com)', 'Accept': 'application/sparql-results+json'}

            try:
                response = requests.get(url, params = {'query' : query, 'format': 'json'}, headers = headers, timeout=10)
                data = response.json()
                enriched_result = data.get('results', {}).get('bindings', [])

                if enriched_result:
                    res = enriched_result[0]
                    result_company = Company(
                        company_id = res.get('item', {}).get('value', "N/A"),
                        company_name = res.get('itemLabel', {}).get('value', "N/A"),
                        website = res.get('website', {}).get('value', "N/A"),
                        country = res.get('countryLabel', {}).get('value', "N/A"),
                        industry = res.get('industryLabel', {}).get('value', "N/A")
                    )
                    
                    return result_company
            except Exception as e:
                pass
                #st.error(f"Error enriching {company_name}: {e}") 
        result_company = Company(
                company_id = 'N/A',
                company_name = 'N/A',
                website = 'N/A',
                country = 'N/A',
                industry = 'N/A'
            )
        return result_company
    

class ScorerService:
    # total score and reasons for dict (one row of table)
    #--------------------------------------------------------------------------------------------------------------------------------------------------------
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