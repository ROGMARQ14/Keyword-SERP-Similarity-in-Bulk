import streamlit as st
import pandas as pd
import difflib
import tldextract
import seaborn as sns
import requests
import json
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

# Function to call ValueSERP API
def serp(api_key, query, location="United States", num_results="9"):
    params = {
        "api_key": api_key,
        "q": query,
        "location": location,
        "hl": "en",
        "gl": "us",
        "google_domain": "google.com",
        "device": "desktop",
        "num": num_results,
        "output": "json",  # Ensure JSON output format
        "flatten_results": "true"  # Get flattened results structure
    }
    
    # Make the HTTP GET request to ValueSERP
    api_result = requests.get('https://api.valueserp.com/search', params)
    
    # Check if the request was successful
    if api_result.status_code == 200:
        try:
            return api_result.json()
        except Exception as e:
            st.error(f"Error parsing API response: {str(e)}")
            return {"error": "Failed to parse response"}
    else:
        st.error(f"API request failed with status code: {api_result.status_code}")
        try:
            error_json = api_result.json()
            return {"error": error_json.get("error", f"Status code: {api_result.status_code}")}
        except:
            return {"error": f"Status code: {api_result.status_code}"}

# Function to extract domains from SERP
def get_serp_comp(results):
    serp_comp = []
    
    try:
        # Add debug information
        if "error" in results:
            st.error(f"API Error: {results['error']}")
            return []
        
        # ValueSERP might use different key structures
        potential_keys = [
            "organic_results",  # Standard 
            "search_results",   # Alternative 
            "results",          # Alternative
            "organic"           # Alternative
        ]
        
        # Find the correct key for organic results
        organic_key = None
        for key in potential_keys:
            if key in results and isinstance(results[key], list):
                organic_key = key
                break
        
        # If no standard key is found, examine the response structure
        if organic_key is None:
            st.warning("Could not find organic results using standard keys")
            st.json(results)
            
            # Look for any list in the response that might contain URLs
            for key, value in results.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    if "link" in value[0] or "url" in value[0]:
                        organic_key = key
                        st.success(f"Found alternative key: {organic_key}")
                        break
            
            if organic_key is None:
                st.error("Could not find any suitable organic results in the response")
                return []
                
        # Extract domains
        for item in results[organic_key]:
            # Find the URL field (might be 'link' or 'url')
            url = None
            if "link" in item:
                url = item["link"]
            elif "url" in item:
                url = item["url"]
            elif "displayed_link" in item:
                url = item["displayed_link"]
                
            if url:
                ext = tldextract.extract(url)
                domain = ext.domain + '.' + ext.suffix
                serp_comp.append(domain)
            
    except Exception as e:
        st.error(f"Error processing results: {str(e)}")
        st.info("API Response preview:")
        # Show a portion of the response for debugging
        st.json({k: str(results[k])[:100] + "..." for k in list(results.keys())[:5]} if results and isinstance(results, dict) else {})
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
    api_key = st.text_input("Enter your ValueSERP Key", type="password")
    st.markdown("""
    Don't have an API key? [Sign up for ValueSERP](https://valueserp.com/)
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
    input_method = st.radio(
        "Input Method",
        ["Text Input", "File Upload"],
        horizontal=True
    )
    
    keywords = []
    
    if input_method == "Text Input":
        keywords_input = st.text_area(
            "Enter keywords (one per line)",
            height=200,
            placeholder="International Business Machines Corporation\nIBM\nbig blue\nInternational Business Machines\nWatson"
        )
        keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
    else:
        uploaded_file = st.file_uploader("Upload a CSV or TXT file with keywords", type=["csv", "txt"])
        if uploaded_file is not None:
            try:
                # Check file type
                if uploaded_file.name.endswith('.csv'):
                    # Try to read as CSV with different delimiters
                    try:
                        df = pd.read_csv(uploaded_file)
                        # Use first column as keywords
                        keywords = df.iloc[:, 0].dropna().tolist()
                    except:
                        # If comma delimiter fails, try tab
                        uploaded_file.seek(0)  # Reset file pointer
                        df = pd.read_csv(uploaded_file, sep='\t')
                        keywords = df.iloc[:, 0].dropna().tolist()
                else:
                    # Read as plain text file
                    keywords = [line.decode('utf-8').strip() for line in uploaded_file if line.decode('utf-8').strip()]
                
                st.success(f"Successfully loaded {len(keywords)} keywords")
                
                # Show preview
                if keywords:
                    st.write("Preview:")
                    st.write(keywords[:5] + (["..."] if len(keywords) > 5 else []))
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    # Process button
    process_button = st.button("Analyze SERP Similarity", disabled=(not api_key or not keywords))

# Display area
with col2:
    st.subheader("Recommendations")
    st.markdown("""
    - Compare topically similar keywords for best results
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
                
                # Call ValueSERP API
                results = serp(api_key, keyword, location, num_results)
                
                # Extract domains or URLs
                if comp_type == "Domain only":
                    serp_comp = get_serp_comp(results)
                else:
                    # Full URL comparison
                    serp_comp = []
                    try:
                        # ValueSERP might use different key structures
                        potential_keys = [
                            "organic_results",  # Standard 
                            "search_results",   # Alternative 
                            "results",          # Alternative
                            "organic"           # Alternative
                        ]
                        
                        # Find the correct key for organic results
                        organic_key = None
                        for key in potential_keys:
                            if key in results and isinstance(results[key], list):
                                organic_key = key
                                break
                        
                        # If no standard key is found, examine the response structure
                        if organic_key is None:
                            st.warning(f"Could not find organic results for '{keyword}' using standard keys")
                            
                            # Look for any list in the response that might contain URLs
                            for key, value in results.items():
                                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                    if "link" in value[0] or "url" in value[0]:
                                        organic_key = key
                                        st.success(f"Found alternative key: {organic_key}")
                                        break
                            
                            if organic_key is None:
                                st.error(f"Could not find any suitable organic results for '{keyword}'")
                                continue
                        
                        # Extract URLs
                        for item in results[organic_key]:
                            # Find the URL field (might be 'link' or 'url')
                            url = None
                            if "link" in item:
                                url = item["link"]
                            elif "url" in item:
                                url = item["url"]
                            elif "displayed_link" in item:
                                url = item["displayed_link"]
                                
                            if url:
                                serp_comp.append(url)
                    
                    except Exception as e:
                        st.error(f"Error processing results for '{keyword}': {str(e)}")
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
