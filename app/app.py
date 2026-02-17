import streamlit as st
import pandas as pd

st.title("0.3 Layer")
st.header("Hello")

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


if "pos_rules" not in st.session_state: 
    st.session_state["pos_rules"] = POS_RULES.copy()

if "neg_rules" not in st.session_state:
    st.session_state["neg_rules"] = NEG_RULES.copy()

def rules_to_str(rules: dict[str, int]) -> str:
    return "\n".join(f"{k}:{v}" for k,v in rules.items())

def score(text: str):
    total_score = 0
    reasons = []

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

    return total_score, "; ".join(reasons)


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


if uploaded_file is not None:
    st.success("File uploaded")
    df = pd.read_csv(uploaded_file)

    table_columns = df.columns.to_list()

    table_columns_name = st.multiselect(
        "Select column name of table: ",
        table_columns,
    )

    out = df.copy()
        
    if not table_columns_name:
        st.write("Choose at least one column name for further work")
    else:    
        out[['score_column', 'reason_column']] = out[table_columns_name].fillna("").astype(str).agg(" ".join , axis=1).apply(score).apply(pd.Series)
        loc_pos = (out['score_column'] > 0).sum()
        loc_neg = (out['score_column'] < 0).sum()
        loc_nul = (out['score_column'] == 0).sum()

        st.write("Statistics:")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.write("Positive count")
            st.write(str(loc_pos))    
        with m2: 
            st.write("Negative count")
            st.write(str(loc_neg))
        with m3:
            st.write("Zero count")
            st.write(str(loc_nul))
  
    if 'score_column' in out.columns: 
        out = out.sort_values(by='score_column', ascending=False).reset_index(drop=True)

    col1, col2 = st.columns(2)

    with col1:
        st.header('Before:')
        st.dataframe(df.head(10))
    with col2: 
        st.header('After')
        st.dataframe(out.head(10))
    csv = out.to_csv(index = False, sep=';').encode("utf-8")

    st.download_button(
        label = "Download CSV",
        data = csv,
        file_name = "data.csv",
    )

else: 
    st.info("No file yet")


