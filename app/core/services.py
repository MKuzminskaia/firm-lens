import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config

import requests 
from .models import Company
from  core.utils import clean_str
import streamlit as st


class WikidataService:
    def __init__(self):
        self.url = config.WIKIDATA_SPARQL_URL 
        self.headers = {
            'User-Agent': config.USER_AGENT, 
            'Accept': config.ACCEPT
        }

    # returns a short list of companies that match the parameters 
    #--------------------------------------------------------------------------------------------------------------------------------------------------------
    def search_companies(_self, company_name :str, website: str = '', country: str = '') -> list[Company]: 
        company_name = company_name.strip()
        company_name = clean_str(company_name.lower())
        result_info : dict [str, Company] = {}

        if website.strip() == 'https://':
            website = ''

        if not company_name:
            raise ValueError("Company Name is empty")
        
        search_url = config.WIKIDATA_API_URL
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
                                      headers=_self.headers,
                                      timeout=config.API_TIMEOUT)
            
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
                    SELECT DISTINCT ?item ?itemDescription ?itemLabel ?website ?countryLabel ?industryLabel WHERE {{
                        VALUES ?item {{ {id_list} }}
                        ?item wdt:P31/wdt:P279* wd:Q4830453 . 
                        OPTIONAL {{ ?item wdt:P856 ?website . }} 
                        OPTIONAL {{ ?item wdt:P17 ?country. 
                                    ?country rdfs:label ?countryLabel. 
                                    FILTER(LANG(?countryLabel) = "en") }}
                        OPTIONAL {{ ?item wdt:P452 ?industry. 
                                    ?industry rdfs:label ?industryLabel. 
                                    FILTER(LANG(?industryLabel) = "en") }}
                        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
                    }}"""
                
            response = requests.get(_self.url, params = {'query' : query, 'format': 'json'}, headers = _self.headers, timeout=config.API_TIMEOUT)
            data = response.json()
            results = data.get('results', {}).get('bindings', [])

            companies_dict: dict[str, Company] = {}

            for res in results:
                
                c_id = res.get('item', {}).get('value', "N/A")
                
                ind_label = res.get('industryLabel', {}).get('value', "N/A")


                comp = Company(
                            company_id=c_id,
                            company_name=res.get('itemLabel', {}).get('value', "N/A"),
                            website=res.get('website', {}).get('value', "N/A"),
                            country=res.get('countryLabel', {}).get('value', "N/A"),
                            industry=[ind_label] if ind_label != "N/A" else [],
                            description=res.get('itemDescription', {}).get('value', 'N/A')
                        )
                
                if (not website or comp.website == website) and (not country or comp.country == country):
                    if c_id not in companies_dict:
                        companies_dict[c_id] = comp
                    else:
                        if ind_label != "N/A" and ind_label not in companies_dict[c_id].industry:
                            companies_dict[c_id].industry.append(ind_label)

            ranked_candidates = []
            
            for item in list(companies_dict.values()):
                description = item.description.lower()
                
                # basic "weight" of item instead of description
                weight = 0

                for word in config.BOOST_KEYWORDS:
                    if word in description:
                        weight +=10

                for word in config.PENALTY_KEYWORDS:
                    if word in description:
                        weight -=20

                ranked_candidates.append({
                    'id' : item.company_id,
                    'weight' : weight,
                    'company' : item
                    }
                )

            ranked_candidates.sort(key=lambda x: x["weight"], reverse=True)
            # if weight < 0 , dont add to result list
            result = []
            for item in ranked_candidates:
                if item['weight'] >= 0:
                    result.append(item['company'])
                
            return result 

        except Exception as e:
            st.error(f"Search failed: {e}")
            return []


    # returns the enriched list of one company by id 
    #--------------------------------------------------------------------------------------------------------------------------------------------------------
    def enrich_company(_self, company_id :str, website: str, country: str) -> Company: 
        company_id = company_id.strip()

        result_company : dict [str, Company] = {}
        if not company_id or company_id == 'N/A':
            raise ValueError("Company Name is empty")
        else: 
            company_id = company_id.split('/')[-1]
            query = f"""SELECT DISTINCT ?item ?itemDescription ?itemLabel ?website ?countryLabel ?industryLabel WHERE {{
                    BIND(wd:{company_id} AS ?item) .
                    ?item wdt:P31/wdt:P279* wd:Q4830453 .
                    OPTIONAL {{ ?item wdt:P856 ?website. }}
                    OPTIONAL {{ ?item wdt:P17 ?country. 
                                ?country rdfs:label ?countryLabel. 
                                FILTER(LANG(?countryLabel) = "en") }}
                    OPTIONAL {{ ?item wdt:P452 ?industry. 
                                ?industry rdfs:label ?industryLabel. 
                                FILTER(LANG(?industryLabel) = "en") }}
                    SERVICE wikibase:label {{bd:serviceParam wikibase:language "en". }}
                    }}"""

            try:
                
                response = requests.get(_self.url, params = {'query' : query, 'format': 'json'}, headers = _self.headers, timeout=config.API_TIMEOUT)
                data = response.json()
                results = data.get('results', {}).get('bindings', [])
                if not results:
                    return Company(company_id = '',company_name= '', country='', industry='', reasons='', score='', website='' )
                else:
                    one_company_result : Company = Company(
                        company_id = results[0].get('item', {}).get('value', "N/A"),
                        company_name = results[0].get('itemLabel', {}).get('value', "N/A"),
                        website = results[0].get('website', {}).get('value', "N/A"),
                        country = results[0].get('countryLabel', {}).get('value', "N/A"),
                        description= results[0].get('itemDescription', {}).get('value', "N/A")
                    )
                    
                    if (not website or one_company_result.website == website) and (not country or one_company_result.country):
                        for res in results:
                            ind_label = res.get('industryLabel', {}).get('value', "N/A")    
                            if ind_label != "N/A" and ind_label not in one_company_result.industry:
                                one_company_result.industry.append(ind_label)


                    if one_company_result.company_id not in result_company:
                        result_company[one_company_result.company_id] = one_company_result
                    return result_company[one_company_result.company_id]
            except Exception as e:
                st.error(f"Error enriching {company_id}: {e}") 
        return Company(company_id = '',company_name= '', country='', industry='', reasons='', score='', website='' )
    

    #
    #--------------------------------------------------------------------------------------------------------------------------------------------------------
    def process_raw_company(self, name: str, website: str = "", country: str = "") -> Company:
        # searching companies by name
        candidates = self.search_companies(name, website, country)
        
        if not candidates:
            return Company(company_id='Not Found', company_name=name, score=-1, reasons='No match found')

        # select the best candidate 
        # (first candidate for test version)
        best_candidate_id = candidates[0].company_id 
        
        # Enrich candidate with full data
        enriched_data = self.enrich_company(best_candidate_id, website, country)
        
        return enriched_data
    

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
    
