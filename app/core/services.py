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
        
        search_url = "https://www.wikidata.org/w/api.php"
        search_params = {
            "action": "wbsearchentities",
            "language": "en",
            "format": "json",
            "search": company_name,
            "type": "item",
            "limit": 50
        }

        try:
            search_res = requests.get(search_url, 
                                      params=search_params, 
                                      headers=self.headers,
                                      timeout=10)
            
            if search_res.status_code != 200:
                st.error(f"Wikidata Search API error: {search_res.status_code}")
                return []

            search_data = search_res.json()
            
            search_results = search_data.get('search', [])

            
            if not search_results:
                return []  #return null if found nothing 
        
            ids = [item['id'] for item in search_results]
            id_list = " ".join([f"wd:{i}" for i in ids])
            
            query = f"""
                    SELECT DISTINCT ?item ?itemLabel ?website ?countryLabel ?industryLabel WHERE {{
                        VALUES ?item {{ {id_list} }}
                        ?item wdt:P31/wdt:P279* wd:Q4830453 . """
            
            if website.strip() and website.strip() != 'https://':
                st.write(website)
                query += f"?item wdt:P856 <{website}> . "
                query += f"BIND(<{website}> AS ?website) "  
            else:
                query += "OPTIONAL { ?item wdt:P856 ?website . } "
            query += f"""OPTIONAL {{ ?item wdt:P17 ?country. ?country rdfs:label ?countryLabel. FILTER(LANG(?countryLabel) = "en") }}
                        OPTIONAL {{ ?item wdt:P452 ?industry. ?industry rdfs:label ?industryLabel. FILTER(LANG(?industryLabel) = "en") }}
                        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
                    }}
                    """
                
            response = requests.get(self.url, params = {'query' : query, 'format': 'json'}, headers = self.headers, timeout=20)
            data = response.json()
            results = data.get('results', {}).get('bindings', [])


            companies_dict: dict[str, Company] = {}

            for res in results:
                c_id = res.get('item', {}).get('value', "N/A")
                ind_label = res.get('industryLabel', {}).get('value', "N/A")

                if c_id not in companies_dict:
                    companies_dict[c_id] = Company(
                        company_id=c_id,
                        company_name=res.get('itemLabel', {}).get('value', "N/A"),
                        website=res.get('website', {}).get('value', "N/A"),
                        country=res.get('countryLabel', {}).get('value', "N/A"),
                        industry=[ind_label] if ind_label != "N/A" else []
                    )
                else:
                    if ind_label != "N/A" and ind_label not in companies_dict[c_id].industry:
                        companies_dict[c_id].industry.append(ind_label)

            return list(companies_dict.values())

        except Exception as e:
            # st.error(f"Search failed: {e}")
            return []


    # returns the enriched list of one company by id 
    #--------------------------------------------------------------------------------------------------------------------------------------------------------
    def enrich_company(self, company_id :str, website: str, country: str) -> Company:  #-> dict [str, str]:  #-> Company:
        company_id = company_id.strip()

        result_company : dict [str, Company] = {}

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
            query += f"""?item wdt:P31/wdt:P279* wd:Q4830453 .
                    OPTIONAL {{ ?item wdt:P856 ?website. }}
                    OPTIONAL {{ ?item wdt:P17 ?country. ?country rdfs:label ?countryLabel. FILTER(LANG(?countryLabel) = "en") }}
                    OPTIONAL {{ ?item wdt:P452 ?industry. ?industry rdfs:label ?industryLabel. FILTER(LANG(?industryLabel) = "en") }}
                    SERVICE wikibase:label {{bd:serviceParam wikibase:language "en". }}
                    }}
                    """

            try:
                
                response = requests.get(self.url, params = {'query' : query, 'format': 'json'}, headers = self.headers, timeout=10)
                data = response.json()
                results = data.get('results', {}).get('bindings', [])
                
                if not results:
                    return Company(company_id = '',company_name= '', country='', industry='', reasons='', score='', website='' )
                else:
                    one_company_result : Company = Company(
                        company_id = results[0].get('item', {}).get('value', "N/A"),
                        company_name = results[0].get('itemLabel', {}).get('value', "N/A"),
                        website = results[0].get('website', {}).get('value', "N/A"),
                        country = results[0].get('countryLabel', {}).get('value', "N/A")
                    )
                    
                    for res in results:
                        #if res.get('industryLabel', {}) != "N/A" and res.get('industryLabel', {}) in one_company_result.industry: 
                        #    one_company_result.industry.append(res.get('industryLabel', {}).get('value', "N/A"))
                        ind_label = res.get('industryLabel', {}).get('value', "N/A")    
                        if ind_label != "N/A" and ind_label not in one_company_result.industry:
                            one_company_result.industry.append(ind_label)


                    if one_company_result.company_id not in result_company:
                        result_company[one_company_result.company_id] = one_company_result
                    return result_company[one_company_result.company_id]
            except Exception as e:
                st.error(f"Error enriching {company_id}: {e}") 
        return Company(company_id = '',company_name= '', country='', industry='', reasons='', score='', website='' )
    

class ScorerService:
    # total score and reasons for dict (one row of table)
    #--------------------------------------------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def calculate_score(text: str, pos_rules: list[dict], neg_rules: list[dict]) -> tuple[int, str]:
        total_score = 0
        reasons = []
        text_lower = text.lower()

        for pos in pos_rules:
            if pos['Keyword'] in text_lower:
                total_score += pos['Points']
                reasons.append(f"+{pos['Keyword']}:{pos['Points']}")
        
        for neg in neg_rules:
            if neg['Keyword'] in text_lower:
                total_score += neg['Points']
                reasons.append(f"+{neg['Keyword']}:{neg['Points']}")
                
        return total_score, "; ".join(reasons)