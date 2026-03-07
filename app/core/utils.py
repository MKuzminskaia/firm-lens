import streamlit as st
import pandas as pd
GARBAGE_WORDS = ['llc', 'ltd', 'inc', 'corp']

# clean garbage words wrom list GARBAGE_WORDS
#--------------------------------------------------------------------------------------------------------------------------------------------------------
def clean_str(dirty_str: str) -> str:
    for garbage_word in GARBAGE_WORDS:
        dirty_str = dirty_str.replace(garbage_word, "")
    dirty_str = dirty_str.strip().capitalize()
    return dirty_str

# convert dict to str
#--------------------------------------------------------------------------------------------------------------------------------------------------------
def rules_to_str(rules: dict[str, int]) -> str:
    return "\n".join(f"{k}:{v}" for k,v in rules.items())


# analyses rules for scoring
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


@st.cache_data
def convert_df_to_csv(df : pd.DataFrame) -> bytes :
    return df.to_csv(index = False, sep = ';').encode('utf-8')
