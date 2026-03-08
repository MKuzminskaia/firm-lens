import streamlit as st
import pandas as pd
import os
import json as js

GARBAGE_WORDS = ['llc', 'ltd', 'inc', 'corp']

RULES_FILE = "scoring_rules.json"

POS_RULES = {
    "medical": 30,
    "health": 25,
    "clinic": 20,
    "ai": 10,
    "internet": 10,
}


NEG_RULES = {
    "gambling": -100,
    "adult": -100,
}

# clean garbage words wrom list GARBAGE_WORDS
#--------------------------------------------------------------------------------------------------------------------------------------------------------
def clean_str(dirty_str: str) -> str:
    for garbage_word in GARBAGE_WORDS:
        dirty_str = dirty_str.replace(garbage_word, "")
    dirty_str = dirty_str.strip().capitalize()
    return dirty_str


@st.cache_data
def convert_df_to_csv(df : pd.DataFrame) -> bytes :
    return df.to_csv(index = False, sep = ';').encode('utf-8')


# lading file with information about scoring rules
#--------------------------------------------------------------------------------------------------------------------------------------------------------

def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE,"r") as f:
            return js.load(f)
    return {"pos": [{"Keyword": k, "Points": p} for k,p, in POS_RULES.items()],
            "neg": [{"Keyword": k, "Points": p} for k,p, in NEG_RULES.items()]}


# saving file with information about scoring rules 
#--------------------------------------------------------------------------------------------------------------------------------------------------------
def save_rules(pos, neg):
    with open(RULES_FILE, "w") as f:
        js.dump({"pos" : pos, "neg" : neg}, f)
    st.success("Rules saved successfully!")    