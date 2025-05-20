# SERP Similarity Analyzer

A Streamlit application to compare keyword SERP similarity in bulk. This tool helps SEOs identify keyword cannibalization issues and analyze how similar Google considers different keywords to be based on their search results.

This application is based on the Python script described in the [ImportSEM blog post](https://importsem.com/compare-keyword-serp-similarity-in-bulk-with-python/).

## Features

- Compare multiple keywords' SERPs and calculate their similarity percentages
- Choose between domain-only or full URL comparison for different granularity levels
- Visualize the results with color-coded tables and bar charts
- Download results as CSV
- Configure location and number of results to analyze

## Requirements

- Python 3.7+
- SerpAPI API key (get one at [serpapi.com](https://serpapi.com/))

## Installation

1. Clone this repository or download the code
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit application:

```bash
streamlit run app.py
```

2. Enter your SerpAPI key in the sidebar
3. Input keywords (one per line) in the text area
4. Configure additional settings in the sidebar if needed
5. Click "Analyze SERP Similarity" to run the analysis

## How It Works

The application:
1. Queries the Google Search API for each keyword
2. Extracts domains or full URLs from the search results
3. Uses Python's difflib to calculate the similarity between each pair of keyword SERPs
4. Computes an average similarity percentage for each keyword
5. Displays the results in a clear, visual format

## Interpreting Results

- Higher percentages indicate more similar SERPs
- Keywords with very similar SERPs (80%+) may be cannibalizing each other
- Keywords with low similarity likely target different search intents
- Try to group your content strategy around keywords with similar SERP profiles

## Notes

- The free tier of SerpAPI has request limitations, so be mindful of how many keywords you analyze at once
- For best results, compare topically similar keywords (20 or fewer)
