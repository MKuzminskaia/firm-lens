# Firm-Lens
**[Live Demo: Firm-Lens App](https://firm-lens.streamlit.app/)**

![Firm-Lens Interface](<docs/00 screen-1.PNG>)

![Excel file](<docs/04 screen-1.PNG>)

Firm-Lens is a Streamlit application built to automate company data enrichment and scoring. It takes a list of companies (or a single name), fetches structured data from the Wikidata API (industry, location, website), and calculates a relevance score based on custom keyword rules.

It was developed to speed up the process of qualifying leads and filtering out irrelevant companies from large datasets.

## What it does
* **Batch Processing:** Upload a CSV, select the column containing company names, and enrich the entire dataset at once.
* **Single Search:** Quick manual lookup for individual companies.
* **Rule-based Scoring:** Automatically assigns positive or negative points based on keywords found in the company's description and industry tags.
* **Export:** Download the processed data as a CSV or a conditionally formatted Excel report.

## Tech Stack
* Python 3.10+
* **UI:** Streamlit
* **Data manipulation:** Pandas
* **External APIs:** Wikidata SPARQL & REST API
* **Export:** xlsxwriter

## Running Locally

1. Clone the repository:
```bash
git clone [https://github.com/MKuzminskaia/firm-lens.git](https://github.com/MKuzminskaia/firm-lens.git)
cd firm-lens
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
streamlit run app.py
``` 

## Configuration
All core parameters, scoring weights, API settings, and keyword lists are centralized in config.py. To tweak the scoring engine or add new penalty keywords, update the dictionaries in the configuration file.