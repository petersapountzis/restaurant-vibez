import requests
import os

API_KEY = 'AIzaSyBizJyXQMvzUARwhBpm3wivJghcjyaAb3g'
location = '29.9511,-90.0715'  # Latitude and Longitude for New Orleans
radius = 50000
type_place = 'restaurant'
url_places = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={type_place}&key={API_KEY}'

if not os.path.exists('restaurant_photos'):
    os.makedirs('restaurant_photos')

def fetch_restaurant_details(url):
    response = requests.get(url)
    results = response.json().get('results')
    return results

def download_photo(photo_reference, folder_name, photo_id):
    photo_url = f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={API_KEY}'
    photo_response = requests.get(photo_url)
    photo_file_path = os.path.join(folder_name, f'{photo_id}.jpg')
    with open(photo_file_path, 'wb') as photo_file:
        photo_file.write(photo_response.content)
    return photo_file_path

def get_place_details(place_id):
    details_url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,photo&key={API_KEY}'
    response = requests.get(details_url)
    details = response.json().get('result', {})
    return details

restaurants = fetch_restaurant_details(url_places)

for restaurant in restaurants:
    name = restaurant.get('name')
    place_id = restaurant.get('place_id')
    print(f"Processing {name}...")
    restaurant_dir = os.path.join('restaurant_photos', name.replace('/', '_'))
    if not os.path.exists(restaurant_dir):
        os.makedirs(restaurant_dir)
    
    # Fetch place details for more photos
    details = get_place_details(place_id)
    photos = details.get('photos', [])
    print(f"Found {len(photos)} photos in details.")

    for index, photo in enumerate(photos):
        photo_reference = photo['photo_reference']
        photo_path = download_photo(photo_reference, restaurant_dir, f'detail_photo_{index+1}')
        print(f"Downloaded to {photo_path}")
