import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def fetch_event_data(org_name, website):
    """Scrape event details from a given organization's website."""
    try:
        response = requests.get(website, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        events = []
        
        for event in soup.find_all(class_=re.compile("event|listing|schedule", re.IGNORECASE)):
            event_name = event.find('h2') or event.find('h3')
            date_text = event.find(string=re.compile(r'\b(March|April|May)\b', re.IGNORECASE))
            time_text = event.find(string=re.compile(r'\d{1,2}:\d{2}\s?(AM|PM)', re.IGNORECASE))
            category_text = event.find(string=re.compile(r'(theater|museum|book reading|tour|panel discussion|festival)', re.IGNORECASE))
            
            if event_name and date_text and category_text:
                start_date, end_date = extract_dates(date_text)
                event_time = time_text.strip() if time_text else "TBD"
                
                if start_date and (datetime(2025, 3, 1) <= start_date <= datetime(2025, 5, 31)):
                    events.append({
                        "Event Name": event_name.get_text(strip=True),
                        "Start Date": start_date.strftime('%Y-%m-%d'),
                        "End Date": end_date.strftime('%Y-%m-%d') if end_date else "",
                        "Time": event_time,
                        "Venue/Organization": org_name,
                        "Website": website
                    })
        return events
    except Exception as e:
        st.error(f"Error scraping {website}: {e}")
        return []

def extract_dates(text):
    """Extract start and end dates from text."""
    date_pattern = re.findall(r'\b(March|April|May)\s\d{1,2}\b', text, re.IGNORECASE)
    if date_pattern:
        dates = [datetime.strptime(d, '%B %d') for d in date_pattern]
        return dates[0], dates[1] if len(dates) > 1 else None
    return None, None

st.title("NYC Event Scraper")

uploaded_file1 = st.file_uploader("Upload 'Spreadsheet of Things to Do - Spring 2023.csv'", type=['csv'])
uploaded_file2 = st.file_uploader("Upload 'Cape CI Ideas + Dump Doc 2024.csv'", type=['csv'])

if uploaded_file1 and uploaded_file2:
    orgs_df1 = pd.read_csv(uploaded_file1)
    orgs_df2 = pd.read_csv(uploaded_file2)
    
    # Debugging: Display file contents
    st.write("### First Few Rows of Uploaded Files")
    st.write("#### Spreadsheet of Things to Do - Spring 2023")
    st.write(orgs_df1.head())
    
    st.write("#### Cape CI Ideas + Dump Doc 2024")
    st.write(orgs_df2.head())
    
    st.write("### Categories Found in Files")
    st.write(orgs_df1.columns)
    st.write(orgs_df2.columns)
    
    merged_orgs = pd.concat([orgs_df1, orgs_df2], ignore_index=True)
    relevant_categories = ["Theater", "Museums", "Book Readings", "Tours", "Panel Discussions", "Seasonal Outdoor Festivals"]
    merged_orgs['Flag for Review'] = merged_orgs['Category'].apply(lambda x: 'Yes' if x == "Misc" else 'No')
    merged_orgs = merged_orgs[merged_orgs['Category'].isin(relevant_categories + ["Misc"])]
    
    # Debugging: Test Google search URLs
    test_orgs = ["The Metropolitan Museum of Art", "Brooklyn Academy of Music"]
    for org in test_orgs:
        website = f"https://www.google.com/search?q={org.replace(' ', '+')}+official+website"
        st.write(f"🔍 Searching for: {org}")
        st.write(f"🌐 Google Search URL: {website}")
    
    output_data = []
    
    for _, row in merged_orgs.iterrows():
        org_name = row['Organization']
        if isinstance(org_name, str):
            website = f"https://www.google.com/search?q={org.replace(' ', '+')}+official+website"
            event_data = fetch_event_data(org_name, website)
            for event in event_data:
                event['Flag for Review'] = row['Flag for Review']
            output_data.extend(event_data)
    
    output_df = pd.DataFrame(output_data)
    
    if not output_df.empty:
        st.write("### Scraped Events")
        st.dataframe(output_df)
        csv = output_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Events CSV", data=csv, file_name="NYC_Events_Spring_2025.csv", mime='text/csv')
    else:
        st.warning("No events found. Try another file.")
