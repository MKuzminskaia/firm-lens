import streamlit as st
import pandas as pd

st.title("0.2 Layer")
st.header("Hello Streamlit + downloading CSV")

uploaded_file = st.file_uploader("Upload data", type="csv")

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


def score(text: str): #-> int:
    total_score = 0
    
    for word, pts in POS_RULES.items():
        if word in text.lower():
            total_score += pts

    for word, pts in NEG_RULES.items():
        if word in text.lower():
            total_score += pts

    return total_score

if uploaded_file is not None:
    st.success("File uploaded")
    df = pd.read_csv(uploaded_file)

    table_columns = df.columns.to_list()
    st.write("Table size is ", df.shape)
    
    st.dataframe(df.head(10))

    table_columns_name = st.selectbox(
        "Select column name of table: ",
        table_columns,
    )
    
    out = df.copy()
    out['score_column'] = out[table_columns_name].astype(str).apply(score)

    out = out.sort_values(by='score_column', ascending=False).reset_index(drop=True)

    st.dataframe(out.head(10))

    csv = out.to_csv(index = False).encode("utf-8")

    st.download_button(
        label = "Download CSV",
        data = csv,
        file_name = "data.csv",
    )

else: 
    st.info("No file yet")


