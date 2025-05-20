import streamlit as st
import pandas as pd
import difflib
import tldextract
import seaborn as sns
from serpapi import GoogleSearch
import matplotlib.pyplot as plt
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="SERP Similarity Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Page title and description
st.title("Compare Keyword SERP Similarity in Bulk")
st.markdown("""
This tool allows you to compare the similarity between search engine results pages (SERPs) for different keywords.
It helps identify keyword cannibalization issues and improve your SEO strategy.
""")

# Function to call SERP API
def serp(api_key, query, location="United States", num_results="9"):
    params = {
        "q": query,
        "location": location,
        "hl": "en",
        "gl": "us",
        "google_domain": "google.com",
        "device": "desktop",
        "num": num_results,
        "api_key": api_key
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    return results

# Function to extract domains from SERP
def get_serp_comp(results):
    serp_comp = []
    try:
        for x in results["organic_results"]:
            ext = tldextract.extract(x["link"])
            domain = ext.domain + '.' + ext.suffix
            serp_comp.append(domain)
    except KeyError:
        st.error(f"Error extracting organic results. Check the API response.")
        return []
    return serp_comp

# Function to calculate SERP difference percentages
def get_keyword_serp_diffs(serp_comp):
    diffs = []
    keyword_diffs = []
    
    for x in serp_comp:
        diffs = []
        for y in serp_comp:
            if x != y:
                sm = difflib.SequenceMatcher(None, x, y)
                diffs.append(sm.ratio())
        try:    
            keyword_diffs.append(round(sum(diffs)/len(diffs), 2))
        except:
            keyword_diffs.append(1)
    
    keyword_diffs = [int(x*100) for x in keyword_diffs]
    
    return keyword_diffs

# Sidebar for API key input
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter your SerpAPI Key", type="password")
    st.markdown("""
    Don't have an API key? [Sign up for SerpAPI](https://serpapi.com/)
    """)
    
    # Location input
    location = st.text_input("Location", "United States")
    
    # Number of results
    num_results = st.select_slider("Number of results", options=["5", "9", "10", "20", "30", "50", "100"], value="9")
    
    # URL comparison type
    comp_type = st.radio(
        "Comparison Type",
        ["Domain only", "Full URL"],
        help="Domain only compares website domains. Full URL compares complete URLs for more granular analysis."
    )
    
    st.markdown("---")
    st.markdown("Created based on [ImportSEM tutorial](https://importsem.com/compare-keyword-serp-similarity-in-bulk-with-python/)")

# Main content area
col1, col2 = st.columns([3, 2])

with col1:
    # Keywords input
    st.subheader("Enter Keywords")
    keywords_input = st.text_area(
        "Enter keywords (one per line)",
        height=200,
        placeholder="International Business Machines Corporation\nIBM\nbig blue\nInternational Business Machines\nWatson"
    )
    
    keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
    
    # Process button
    process_button = st.button("Analyze SERP Similarity", disabled=(not api_key or not keywords))

# Display area
with col2:
    st.subheader("Recommendations")
    st.markdown("""
    - Compare topically similar keywords for best results
    - Limit to 20 or fewer keywords for meaningful analysis
    - Higher similarity percentage means the SERPs are more similar
    - Low similarity may indicate the keywords target different intents
    """)

# Process data when button is clicked
if process_button:
    with st.spinner('Analyzing keyword SERPs...'):
        try:
            serp_comp_list = []
            progress_bar = st.progress(0)
            
            # Process each keyword
            for i, keyword in enumerate(keywords):
                st.text(f"Processing: {keyword}")
                
                # Call SerpAPI
                results = serp(api_key, keyword, location, num_results)
                
                # Extract domains or URLs
                if comp_type == "Domain only":
                    serp_comp = get_serp_comp(results)
                else:
                    # Full URL comparison
                    serp_comp = []
                    try:
                        for x in results["organic_results"]:
                            serp_comp.append(x["link"])
                    except KeyError:
                        st.error(f"Error extracting organic results for '{keyword}'. Check the API response.")
                        continue
                
                serp_comp_list.append(serp_comp)
                progress_bar.progress((i + 1) / len(keywords))
            
            # Calculate similarity percentages
            serp_comp_keyword = get_keyword_serp_diffs(serp_comp_list)
            
            # Create dataframe
            df = pd.DataFrame({
                'Keyword': keywords,
                'Keyword SERP Similarity (%)': serp_comp_keyword
            })
            
            # Display results
            st.subheader("Results")
            
            # Color mapping with seaborn
            cm = sns.light_palette("green", as_cmap=True)
            
            # Display styled dataframe
            st.dataframe(
                df.style.background_gradient(
                    cmap=cm, 
                    subset=['Keyword SERP Similarity (%)']
                )
            )
            
            # Create a visualization
            fig, ax = plt.subplots(figsize=(10, len(keywords)/2 + 2))
            
            # Sort by similarity
            df_sorted = df.sort_values(by='Keyword SERP Similarity (%)', ascending=True)
            
            # Create horizontal bar chart
            bars = ax.barh(
                df_sorted['Keyword'], 
                df_sorted['Keyword SERP Similarity (%)'],
                color=plt.cm.Greens(np.linspace(0.3, 0.8, len(keywords)))
            )
            
            ax.set_xlabel('Similarity (%)')
            ax.set_title('Keyword SERP Similarity')
            
            # Add value labels
            for bar in bars:
                width = bar.get_width()
                ax.text(
                    width + 1, 
                    bar.get_y() + bar.get_height()/2, 
                    f'{width}%', 
                    ha='left', 
                    va='center'
                )
            
            st.pyplot(fig)
            
            # Allow download as CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download results as CSV",
                data=csv,
                file_name="serp_similarity_results.csv",
                mime="text/csv",
            )
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
