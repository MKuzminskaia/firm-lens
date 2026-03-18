import streamlit as st
import pandas as pd
import sys
import os
import io
import json as js

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config

# clean garbage words wrom list GARBAGE_WORDS
#--------------------------------------------------------------------------------------------------------------------------------------------------------
def clean_str(dirty_str: str) -> str:
    for garbage_word in config.GARBAGE_WORDS:
        dirty_str = dirty_str.replace(garbage_word, "")
    dirty_str = dirty_str.strip().capitalize()
    return dirty_str


@st.cache_data
def convert_df_to_csv(df : pd.DataFrame) -> bytes :
    return df.to_csv(index = False, sep = ';').encode('utf-8')


# lading file with information about scoring rules
#--------------------------------------------------------------------------------------------------------------------------------------------------------

def load_rules():
    if os.path.exists(config.RULES_FILE_PATH):
        with open(config.RULES_FILE_PATH,"r", encoding='utf-8') as f:
            return js.load(f)
    return {"pos": [{"Keyword": k, "Points": p} for k,p, in config.POS_RULES.items()],
            "neg": [{"Keyword": k, "Points": p} for k,p, in config.NEG_RULES.items()]}


# saving file with information about scoring rules 
#--------------------------------------------------------------------------------------------------------------------------------------------------------
def save_rules(pos, neg):
    # Extract the path to the folder itself (cut off rules.json)
    directory = os.path.dirname(config.RULES_FILE_PATH)
    
    # Create the folder if it doesn't exist.
    os.makedirs(directory, exist_ok=True)
    
    with open(config.RULES_FILE_PATH, "w", encoding="utf-8") as f:
        js.dump({"pos" : pos, "neg" : neg}, f, ensure_ascii=False, indent=4)
        
    st.success("Rules saved successfully!") 

# convert dataframe object to Excel file format 
#--------------------------------------------------------------------------------------------------------------------------------------------------------
def convert_df_to_excel(df):
    output = io.BytesIO()
    # use xlsxwriter like a driver
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Firm-Lens Report')
        
        workbook  = writer.book
        worksheet = writer.sheets['Firm-Lens Report']

        # Formats
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        green_fmt  = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        red_fmt    = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        url_fmt    = workbook.add_format({'font_color': 'blue', 'underline': 1})

        # 1. Styling the headings
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)

        # 2. Conditional formatting for Score
        score_col_idx = df.columns.get_loc("score") 
        worksheet.conditional_format(1, score_col_idx, len(df), score_col_idx, {
            'type': 'cell', 'criteria': '>=', 'value': 10, 'format': green_fmt
        })
        worksheet.conditional_format(1, score_col_idx, len(df), score_col_idx, {
            'type': 'cell', 'criteria': '<', 'value': 0, 'format': red_fmt
        })

        # 3. Make links clickable (if the column is called 'website')
        if 'website' in df.columns:
            web_col_idx = df.columns.get_loc("website")
            for row_num in range(len(df)):
                url = df.iloc[row_num, web_col_idx]
                if url and url != 'N/A' and str(url).startswith('http'):
                    worksheet.write_url(row_num + 1, web_col_idx, url, url_fmt, string=url)

        # 4. Auto-fit width (approximate)
        for i, col in enumerate(df.columns):
            worksheet.set_column(i, i, 20)

        worksheet.freeze_panes(1, 0)

    return output.getvalue()