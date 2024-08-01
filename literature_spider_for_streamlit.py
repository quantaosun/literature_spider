import streamlit as st
import requests
from xml.etree import ElementTree
from datetime import datetime
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# Set page config with title and icon
st.set_page_config(page_title="Literature Spider", page_icon="🕷️")

# Apply custom CSS for background image and text colors
st.markdown(
    """
    <style>
    body {
        background-image: url('https://example.com/your-image.jpg');
        background-size: cover;
    }
    .stApp {
        background-color: rgba(0, 0, 0, 0.5);
        color: white;
    }
    .css-1d391kg, .css-2trqyj, .css-1avcm0n {
        color: #ffffff;
    }
    h1, h2, h3, h4 {
        color: #FF6347;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Set the app title and subtitle with new theme colors
st.markdown("<h1 style='text-align: center;'>Literature Spider</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Discover the latest research articles effortlessly</h3>", unsafe_allow_html=True)

# Input field for keywords
user_keywords = st.text_input('🔍 Enter search keywords')

# Input fields for date range
col1, col2 = st.columns(2)
with col1:
    start_year = st.number_input('📅 Start Year', min_value=1900, max_value=datetime.now().year, value=datetime.now().year-5)
with col2:
    end_year = st.number_input('📅 End Year', min_value=1900, max_value=datetime.now().year, value=datetime.now().year)

# Input field for the number of articles to retrieve
num_articles = st.slider('📑 Number of articles to retrieve', min_value=1, max_value=100, value=10)

# Function to truncate abstracts to 100 words
def truncate_abstract(abstract):
    if abstract is None:
        return "No abstract available"
    words = abstract.split()
    if len(words) > 100:
        return ' '.join(words[:100]) + '...'
    else:
        return abstract

# Search button
if st.button('Search'):
    if user_keywords:
        # Construct the query with the time frame
        query = f'{user_keywords} AND ("{start_year}/01/01"[PDAT] : "{end_year}/12/31"[PDAT])'
        response = requests.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi', params={
            'db': 'pubmed',
            'term': query,
            'retmode': 'xml',
            'retmax': num_articles
        })

        if response.status_code == 200:
            root = ElementTree.fromstring(response.content)
            id_list = [id_elem.text for id_elem in root.findall('.//Id')]

            # Check if any articles were found
            if not id_list:
                st.write("No articles found.")
            else:
                # Prepare a list to store article details
                articles = []

                for index, pmid in enumerate(id_list, start=1):
                    detail_response = requests.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi', params={
                        'db': 'pubmed',
                        'id': pmid,
                        'retmode': 'xml'
                    })

                    if detail_response.status_code == 200:
                        detail_root = ElementTree.fromstring(detail_response.content)
                        title = detail_root.findtext('.//Item[@Name="Title"]')
                        journal = detail_root.findtext('.//Item[@Name="Source"]')
                        pub_date = detail_root.findtext('.//Item[@Name="PubDate"]')
                        
                        # Fetch and parse the abstract with error handling
                        try:
                            abstract_response = requests.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi', params={
                                'db': 'pubmed',
                                'id': pmid,
                                'retmode': 'xml'
                            })
                            # Check if the response is valid XML
                            logging.info(f"Abstract response: {abstract_response.content[:500]}")  # Log the beginning of the response
                            abstract_root = ElementTree.fromstring(abstract_response.content)
                            abstract = abstract_root.findtext('.//AbstractText')
                            truncated_abstract = truncate_abstract(abstract)
                        except ElementTree.ParseError as e:
                            logging.error(f"Failed to parse abstract for PMID {pmid}: {e}")
                            truncated_abstract = 'Abstract unavailable due to parsing error.'
                        except Exception as e:
                            logging.error(f"Error fetching abstract for PMID {pmid}: {e}")
                            truncated_abstract = 'Abstract unavailable due to error.'

                        pubmed_link = f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'

                        articles.append({
                            'Index': index,
                            'Title': title,
                            'Journal': journal,
                            'Publication Date': pub_date,
                            'Abstract': truncated_abstract,
                            'URL': pubmed_link
                        })

                # Display the articles with entry numbers and truncated abstracts
                for article in articles:
                    st.markdown(f"<h4>{article['Index']}. {article['Title']}</h4>", unsafe_allow_html=True)
                    st.write(f"**Journal:** {article['Journal']}")
                    st.write(f"**Publication Date:** {article['Publication Date']}")
                    st.write(f"**Abstract:** {article['Abstract']}")
                    st.markdown(f"<a href='{article['URL']}' style='color: #FF6347;'>Read more on PubMed</a>", unsafe_allow_html=True)
                    st.write("---")

        else:
            st.error("Search failed. Please try again.")

