import streamlit as st

import pandas as pd

import json as js

import requests

import time



st.title("0.5 Layer")

st.header("Firm-Lens")



#uploaded_file = st.file_uploader("Upload data", type="csv")



POS_RULES = {

    "medical": 30,

    "health": 25,

    "clinic": 20,

    "ai": 10,

    "software": 10,

}



NEG_RULES = {

    "gambling": -100,

    "adult": -100,

}



ENRICH = {

    "enriched_description": "...",

    "enriched_website": "...",

    "enriched_country": "...",

    "enriched_industry": "...",

    "enrich_status": "not_found",  # "hit" | "not_found" | "error",

    "enrich_source": "wikidata"

}





TABLE_COLUMS = ['company_name', 'domain', 'website', 'description', 'industry', 'country']



TABLE_EMPTY = {

    'company_name' : ['empty'],

    'domain' : ['empty'],

    'website' : ['empty'],

    'description' : ['empty'],

    'industry' : ['empty'],

    'country' : ['empty']

}



MAIN_COLUMN = 'company_name'



GARBAGE_WORDS = ['llc', 'ltd', 'inc', 'corp']



SEARCH_INFO = {

    'company_name' : ['empty'],  

    'website' : ['empty'],  

    'country' : ['empty']

}



COMPANY_LIST_FOR_ENRICHING = {

        'company_name' : ['empty'],

        'company_id': ['empty'],

       # 'domain' : ['empty'],

        'website' : ['empty'],

       # 'description' : ['empty'],

        'country' : ['empty'],

        'industry' : ['empty'],

        'score_column' : ['empty'],

        'reason_column': ['empty']

}



if "pos_rules" not in st.session_state:

    st.session_state["pos_rules"] = POS_RULES.copy()

if "neg_rules" not in st.session_state:

    st.session_state["neg_rules"] = NEG_RULES.copy()

if "enrich" not in st.session_state:

    st.session_state["enrich"] = ENRICH.copy()

# information entered into input fields

if "search_info" not in st.session_state:

    st.session_state["search_info"] = SEARCH_INFO.copy()

# list of searching companies by name and another parameters    

if "founded_list_of_companies" not in st.session_state:

    st.session_state['founded_list_of_companies'] = ['']

# one selected current firm  

if "selected_company_for_enriching" not in st.session_state:

    st.session_state['selected_company_for_enriching'] = ''

# Finaly list of companies    

if "company_list_for_enriching" not in st.session_state:

    st.session_state['company_list_for_enriching'] = COMPANY_LIST_FOR_ENRICHING.copy()





#--------------------------------------------------------------------------------------------------------------------------------------------------------

def clean_str(dirty_str: str) -> str:

    for garbage_word in GARBAGE_WORDS:

        dirty_str = dirty_str.replace(garbage_word, "")

    dirty_str = dirty_str.strip()

    dirty_str = dirty_str[0].upper() + dirty_str[1:len(dirty_str)]

    return dirty_str





# returns a short list of companies that match the parameters

#--------------------------------------------------------------------------------------------------------------------------------------------------------

def search_company(company_name :str, website: str, country: str): # -> dict{str, []}:

    company_name = company_name.strip()

    company_name = clean_str(company_name.lower())

    result_info = []



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



            if results:

                for res in results:

                    one_company_result = {

                        'company_id' : res.get('item', {}).get('value', "N/A"),

                        'company_name' : res.get('itemLabel', {}).get('value', "N/A"),

                        'website' : res.get('website', {}).get('value', "N/A"),

                        'country' : res.get('countryLabel', {}).get('value', "N/A"),

                        'industry' : res.get('industryLabel', {}).get('value', "N/A")

                    }

                    result_info.append(one_company_result)

        except Exception as e:

            st.error(f"Error enriching {company_name}: {e}")



    return result_info



# returns the enriched list of one company by id

#--------------------------------------------------------------------------------------------------------------------------------------------------------

def enrich(company_id :str, website: str, country: str) -> dict [str, str]:

    company_id = company_id.strip()

    default_result = {

        'company_id': company_id,

        'company_name': "N/A",

        'website': "N/A",

        'country': "N/A",

        'industry': "N/A"

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

                return {

                    'company_id' : res.get('item', {}).get('value', "N/A"),

                    'company_name' : res.get('itemLabel', {}).get('value', "N/A"),

                    'website' : res.get('website', {}).get('value', "N/A"),

                    'country' : res.get('countryLabel', {}).get('value', "N/A"),

                    'industry' : res.get('industryLabel', {}).get('value', "N/A")

                }



        except Exception as e:

            st.error(f"Error enriching {company_name}: {e}")

    return default_result



#--------------------------------------------------------------------------------------------------------------------------------------------------------

def rules_to_str(rules: dict[str, int]) -> str:

    return "\n".join(f"{k}:{v}" for k,v in rules.items())



#--------------------------------------------------------------------------------------------------------------------------------------------------------

def score(text: str) -> dict [str, str]:

    total_score = 0

    reasons = []

    if not text:

        raise ValueError("Column with this name is empty")

    else:

        pos_rules :dict [str, int] = st.session_state["pos_rules"]

        neg_rules :dict [str, int] = st.session_state["neg_rules"]

       

        for word, pts in pos_rules.items():

            if word in text.lower():

                total_score += pts

                reasons.append(f"+{pts}:{word}")



        for word, pts in neg_rules.items():

            if word in text.lower():

                total_score += pts

                reasons.append(f"{pts}:{word}")



    return str(total_score), "; ".join(reasons)



#--------------------------------------------------------------------------------------------------------------------------------------------------------

def rules_parser(rule :str) -> dict[str, int]:

    result :dict[str, int] = {}



    for line in rule.splitlines():

        line = line.strip()



        if not line:

            continue

        if ":" not in line:

            continue



        key, value = line.split(':',1)



        key = key.strip().lower()



        if not key:

            continue



        value = value.strip()



        try:

            result[key] = int(value)

        except ValueError:

            continue



    return result



with st.sidebar:

    txt_pos = st.text_area(

        "Write positive rules:",

        rules_to_str(st.session_state["pos_rules"]),

        height="content"

    )

    txt_neg = st.text_area(

        "Write negative rules:",

        rules_to_str(st.session_state["neg_rules"]),

        height="content"

    )

    apply = st.button(

        label="Apply"

    )



    if apply:

        st.session_state["pos_rules"] = rules_parser(txt_pos)

        st.session_state["neg_rules"] = rules_parser(txt_neg)





#if uploaded_file is not None:

    #st.success("File uploaded")

    #df = pd.read_csv(uploaded_file)



    #table_columns = df.columns.to_list()







company_name = clean_str(st.text_input("Company name: ", "Google inc"))

website = st.text_input("website: ", "https://")

country = st.text_input("Country: ")



search_info = {

    'company_name' : [company_name],  

    'Website' : [website],  

    'country' : [country]

}



results_df = pd.DataFrame(search_info)



if st.button("Submit"):

    #table_result = search_info



    try:

        rare_data = search_company(search_info['company_name'][0], '', '')

        results_df = pd.DataFrame(rare_data)

        st.session_state['founded_list_of_companies'] = rare_data

        #out[["company","site","country"]] = out['company_name'].fillna("").astype(str).apply(lambda x: search_company(x, "", "")).apply(pd.Series)    

        #out[["enriched_description","enriched_website","enriched_country","enriched_industry","enrich_status","enrich_source"]] = out['company_name'].fillna("").astype(str).apply(lambda x: enrich(x, "", "")).apply(pd.Series)

    except Exception as e:

        st.write(e)





table_columns = COMPANY_LIST_FOR_ENRICHING.keys()

table_columns_name = st.multiselect(

    "Select column name of table for enriching: ",

    table_columns,

)





#company_name = st.selectbox(

#    "Select company name column: ",

#    table_columns,

#    index=0

#)

   

if not table_columns_name:

    st.error("Choose at least one column name for further work")

#    st.write("Choose at least one column name for further work")

#else:    

#    out[['score_column', 'reason_column']] = out[table_columns_name].fillna("").astype(str).agg(" ".join , axis=1).apply(score).apply(pd.Series)

#    

#    enrich_cols = list(st.session_state['enrich'].keys())

#    

#

#    loc_pos = (out['score_column'] > 0).sum()

#    loc_neg = (out['score_column'] < 0).sum()

#    loc_nul = (out['score_column'] == 0).sum()

#

#    st.write("Statistics:")

#    m1, m2, m3 = st.columns(3)

#    with m1:

#        st.write("Positive count")

#        st.write(str(loc_pos))    

#    with m2:

#        st.write("Negative count")

#        st.write(str(loc_neg))

#    with m3:

#        st.write("Zero count")

#        st.write(str(loc_nul))



#if 'score_column' in out.columns:

#    out = out.sort_values(by='score_column', ascending=False).reset_index(drop=True)



#col1, col2 = st.columns(2)



#with col1:

#    st.header('Before:')

    #st.dataframe(df.head(10))

#with col2:

#    st.header('After')



selected_rows = []

choosen_row = {}



if 'founded_list_of_companies' in st.session_state:

    df = pd.DataFrame(st.session_state['founded_list_of_companies'])

    s = st.dataframe(df,

             selection_mode="single-row",

             on_select="rerun",

             column_config = {'company_id' : None}

             )

   

    selected_rows = s['selection']['rows']

    if selected_rows:

        first_index = selected_rows[0]

        choosen_row = df.iloc[first_index]

        st.session_state['selected_company_for_enriching'] = choosen_row

        st.write(choosen_row)

        st.success(f"You choose:{choosen_row}, {choosen_row['company_name']}")



if selected_rows and table_columns_name:

    try:

        company_id = st.session_state['selected_company_for_enriching']['company_id']



        with st.spinner("Searching data in Wikidata..."):
            enriched_data = enrich(company_id, '', '')

        current_table = {}
        current_table = st.session_state['company_list_for_enriching']
        current_table['company_id'].append(enriched_data['company_id'])
        current_table['company_name'].append(enriched_data['company_name'])
        current_table['website'].append(enriched_data['website'])
        current_table['country'].append(enriched_data['country'])
        current_table['industry'].append(enriched_data['industry'])

        current_table['score_column'].append('N/A')
        current_table['reason_column'].append('N/A')

        
        if (current_table['company_id'][0] == 'empty'):
            for key in current_table:
                current_table[key].pop(0)

        final_df = pd.DataFrame(current_table)
        final_df[['score_column', 'reason_column']] = final_df[table_columns_name].fillna("").astype(str).agg(" ".join , axis=1).apply(score).apply(pd.Series)

        st.session_state['company_list_for_enriching'] = current_table

        if enriched_data:     
            #final_df = pd.DataFrame([enriched_data])
            #final_df = pd.DataFrame(current_table)
            
            #'enrich_status': ['empty']
            #'enrich_source': ['empty']


            st.subheader("Result of deep analysis:")
            st.table(final_df) 
            
            # count scoring
            text_to_score = f"{enriched_data['company_name']} {enriched_data['industry']} {enriched_data['country']}"
            total_score, reason = score(text_to_score)
            
            st.metric("The company's final score", f"{total_score} pts")
            st.caption(f"Justification: {reason}")

        #df = pd.DataFrame(st.session_state['founded_list_of_companies'])
        #s = st.dataframe(df, 
        #        selection_mode="single-row", 
        #        on_select="rerun", 
        #        column_config = {'company_id' : None}
        #)
            

    except Exception as e:
        st.write(e)


#csv = out.to_csv(index = False, sep=';').encode("utf-8")

#st.download_button(
#    label = "Download CSV",
#    data = csv,
#    file_name = "data.csv",
#)

#else: 
#    st.info("No file yet")


