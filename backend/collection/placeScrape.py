import googlemaps
import pandas as pd
import os
import json
import requests
from pprint import pprint

def load_api_keys(file_path='api_keys.json'):
    """
    Load API keys from a JSON file.
    """
    with open(file_path, 'r') as file:
        keys = json.load(file)
    return keys

def initialize_google_maps_client(api_key):
    """
    Initialize the Google Maps client.
    """
    return googlemaps.Client(key=api_key)

def get_nearby_restaurants_google(gm_client, location, radius=1000):
    """
    Fetch nearby restaurants using the Google Maps API.
    """
    nearby_places = gm_client.places_nearby(location=location, radius=radius, type='restaurant')
    df = pd.DataFrame([{
        'Name': place['name'].strip().lower(),
        'Google Business ID': place.get('place_id'),
        'Google Address': place.get('vicinity'),
        'Google Rating': place.get('rating'),
        'Google Total Ratings': place.get('user_ratings_total'),
        'Google Price': place.get('price_level'),
        # Add Photos column with an empty list as default
        'Photos': []
    } for place in nearby_places['results']])

    # Populate the Photos column with the list of photo references for each place
    for index, row in df.iterrows():
        place_id = row['Google Business ID']
        place_details = gm_client.place(place_id=place_id)
        photos = place_details.get('result', {}).get('photos', [])
        # Add list of photo references to the 'Photos' column
        df.at[index, 'Photos'] = [photo['photo_reference'] for photo in photos]

    return df


def get_nearby_restaurants_yelp(api_key, location, radius=1000):
    """
    Fetch nearby restaurants using the Yelp Fusion API.
    """
    # Yelp API endpoint for business search
    url = "https://api.yelp.com/v3/businesses/search"

    # Convert radius from meters to miles for Yelp API (as Yelp uses miles for distance)

    # Split the location into latitude and longitude
    lat, lon = location.split(',')

    # Set parameters for the Yelp API request
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    params = {
        'term': 'restaurant',
        'latitude': lat,
        'longitude': lon,
        'radius': radius,  # Convert back to meters for Yelp's radius parameter
        'limit': 20  # Yelp API allows up to 50 results per request
    }

    # Make a request to the Yelp API
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error: Unable to fetch data from Yelp API. Status Code: {response.status_code}")
        return pd.DataFrame()  # Return an empty DataFrame if there's an error

    data = response.json()

    # Create DataFrame from Yelp API response
    df = pd.DataFrame([{
        'Name': business['name'],
        'Yelp Business ID': business.get('id'),
        'Yelp Address': ', '.join(business['location'].get('display_address', [])),
        'Yelp Rating': business.get('rating'),
        'Yelp Total Ratings': business.get('review_count'),
        'Yelp Price': business.get('price', None),  # Price may not be available for all businesses
        'Yelp Cuisine': business.get('categories')
    } for business in data.get('businesses', [])])
    
    return df



def download_photos_from_dataframe(gm_client, df):
    """
    Download and save photos for each restaurant from the DataFrame.
    """
    for index, row in df.iterrows():
        place_name = row['Name']
        photo_references = row['Photos']  # Get the list of photo references from the DataFrame

        # Replace any illegal characters in folder names
        folder_name = ''.join(char for char in place_name if char.isalnum() or char in (' ', '_')).strip()

        # Create a directory named after the restaurant
        os.makedirs(f'photos/{folder_name}', exist_ok=True)

        for i, ref in enumerate(photo_references):
            # Retrieve the photo using the Google Maps client
            response = gm_client.places_photo(photo_reference=ref, max_width=1000)
            
            # Construct the file name with the source
            file_name = f"photos/{folder_name}/{folder_name}_Google_photo_{i+1}.jpg"
            
            # Save the photo to disk
            with open(file_name, 'wb') as file:
                for chunk in response:
                    file.write(chunk)

            print(f"Saved photo {file_name}")

def get_yelp_food_and_drink_insights(api_key, business_id):
    """
    Fetch food and drink insights from Yelp using the Business ID.
    """
    url = f"https://api.yelp.com/v3/businesses/{business_id}/insights/food_and_drinks"

    headers = {
        'Authorization': f'Bearer {api_key}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Unable to fetch data from Yelp for Business ID {business_id}. Status Code: {response.status_code}")
        return None

def fetch_and_print_yelp_insights(api_key, df):
    """
    Fetch Yelp food and drink insights for each business in the DataFrame and print them.
    """
    for index, row in df.iterrows():
        yelp_business_id = row.get('Yelp Business ID')  # Ensure the column name matches
        print(yelp_business_id)
        # Fetch Yelp insights
        if yelp_business_id:
            insights = get_yelp_food_and_drink_insights(api_key, yelp_business_id)

            # Print insights if available
            if insights:
                print(f"Food and Drink Insights for {row['Name']} (Yelp Business ID: {yelp_business_id}):")
                print(json.dumps(insights, indent=4))  # Pretty-print the JSON data
            else:
                print(f"No insights available for {row['Name']}.")

def main():
    pd.set_option('display.max_columns', None)   # Show all columns
    pd.set_option('display.expand_frame_repr', False)  # Prevent line wrapping for wide DataFrames
    pd.set_option('display.max_colwidth', None)  # Show full column content
    # Load API keys from JSON file
    keys = load_api_keys('api_keys.json')
    
    # Initialize Google Maps client
    gm_client = initialize_google_maps_client(keys['google_maps_api_key'])
    
    # Define location
    location = '29.9511,-90.0715'
    
    # Fetch nearby restaurants from Google
    google_df = get_nearby_restaurants_google(gm_client, location)
    google_df['Name'] = google_df['Name'].str.strip().str.lower() 
    print("Google Places API Data:")
    print(google_df.head())
    
    # Fetch nearby restaurants from Yelp
    yelp_df = get_nearby_restaurants_yelp(keys['yelp_api_key'], location)
    yelp_df['Name'] = yelp_df['Name'].str.strip().str.lower() 
    print("\nYelp Fusion API Data:")
    print(yelp_df.head())
   
    merged_df = pd.merge(google_df, yelp_df, on='Name', how='outer', indicator=True)

    # Remove rows with matching names
    non_matching_df = merged_df[merged_df['_merge'] != 'both']

    # Drop the indicator column
    non_matching_df.drop(columns=['_merge'], inplace=True)
    
    print(non_matching_df.head())
    # Download photos from Google Places
    #download_photos_from_dataframe(gm_client, google_df)
    fetch_and_print_yelp_insights(keys['yelp_api_key'], non_matching_df)


if __name__ == "__main__":
    main()
