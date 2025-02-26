import pandas as pd
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
        
        # Look for event listings (this will vary by website)
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
        print(f"Error scraping {website}: {e}")
        return []

def extract_dates(text):
    """Extract start and end dates from text."""
    date_pattern = re.findall(r'\b(March|April|May)\s\d{1,2}\b', text, re.IGNORECASE)
    if date_pattern:
        dates = [datetime.strptime(d, '%B %d') for d in date_pattern]
        return dates[0], dates[1] if len(dates) > 1 else None
    return None, None

def main():
    # Load organization lists (from uploaded CSV files)
    orgs_df1 = pd.read_csv('/mnt/data/Spreadsheet of Things to do - Spring 2023.csv')
    orgs_df2 = pd.read_csv('/mnt/data/Cape CI Ideas + Dump Doc 2024 - CI misc don\'t lose.csv')
    
    # Merge both lists and filter for relevant categories
    merged_orgs = pd.concat([orgs_df1, orgs_df2], ignore_index=True)
    relevant_categories = ["Theater", "Museums", "Book Readings", "Tours", "Panel Discussions", "Seasonal Outdoor Festivals"]
    merged_orgs['Flag for Review'] = merged_orgs['Category'].apply(lambda x: 'Yes' if x == "Misc" else 'No')
    merged_orgs = merged_orgs[merged_orgs['Category'].isin(relevant_categories + ["Misc"])]
    
    output_data = []
    
    for _, row in merged_orgs.iterrows():
        org_name = row['Organization']
        if isinstance(org_name, str):
            website = f"https://www.google.com/search?q={org_name.replace(' ', '+')}+official+website"
            event_data = fetch_event_data(org_name, website)
            for event in event_data:
                event['Flag for Review'] = row['Flag for Review']
            output_data.extend(event_data)
    
    # Save results to CSV
    output_df = pd.DataFrame(output_data)
    output_df.to_csv('/mnt/data/NYC_Events_Spring_2025.csv', index=False)
    
    print("Event scraping complete! File saved.")

if __name__ == "__main__":
    main()
