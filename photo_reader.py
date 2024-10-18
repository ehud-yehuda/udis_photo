import os
from datetime import date, datetime
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scope for Google Photos API
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
file_path: str = 'cred/secrets_fake.json'

def authenticate_user():
    """Authenticate the user and return credentials."""
    flow = InstalledAppFlow.from_client_secrets_file(file_path, SCOPES)
    credentials = flow.run_local_server(port=0, access_type='offline', prompt='consent')
    return credentials

def authenticate():
    """Authenticate the user and return credentials."""
    creds = None
    # Load credentials from token.json if it exists
    flow = InstalledAppFlow.from_client_secrets_file(
        file_path, SCOPES
    )
    creds = flow.run_local_server(
        port=0, access_type='offline', prompt='consent'
    )
    # if os.path.exists(file_path):
    #     creds = Credentials.from_authorized_user_file(file_path, SCOPES)
        # with io.open(file_path, "r", encoding="utf-8") as json_file:
        #     data = json.load(json_file)
        #     creds = Credentials.from_authorized_user_info(data["installed"], scopes=SCOPES)

    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


def fetch_photos_by_date(service, start_date, end_date):
    """Fetch photos between the start and end dates from Google Photos."""
    filters = {
        'dateFilter': {
            'ranges': [{
                'startDate': {'year': start_date.year, 'month': start_date.month, 'day': start_date.day},
                'endDate': {'year': end_date.year, 'month': end_date.month, 'day': end_date.day},
            }]
        }
    }

    response = service.mediaItems().search(body={'filters': filters}).execute()
    photos = response.get('mediaItems', [])

    # Continue fetching more pages if they exist
    while 'nextPageToken' in response:
        next_page_token = response['nextPageToken']
        response = service.mediaItems().search(body={'filters': filters, 'pageToken': next_page_token}).execute()
        photos.extend(response.get('mediaItems', []))

    return photos


def fetch_photos(creds):
    """Fetch photos from Google Photos."""
    headers = {'Authorization': f'Bearer {creds.token}'}
    url = 'https://photoslibrary.googleapis.com/v1/mediaItems'
    photos = []

    while url and len(photos) < 10:
        response = requests.get(url, headers=headers)
        data = response.json()

        if 'mediaItems' in data:
            photos.extend(data['mediaItems'])

        # Get the next page token
        url = data.get('nextPageToken')
        if url:
            url = f'https://photoslibrary.googleapis.com/v1/mediaItems?pageToken={url}'

    return photos


def __save_photos_by_date(photos):
    """Organize and save photos by date."""
    for photo in photos:
        creation_time = photo['mediaMetadata']['creationTime']
        date_str = creation_time.split('T')[0]  # Get date part
        date_dir = os.path.join('photos', date_str)

        # Create the directory if it doesn't exist
        os.makedirs(date_dir, exist_ok=True)

        # Download the photo
        photo_url = photo['baseUrl'] + '=d'  # Adding '=d' for full resolution
        photo_name = os.path.join(date_dir, f"{photo['id']}.jpg")

        # Save the photo
        with requests.get(photo_url) as r:
            with open(photo_name, 'wb') as f:
                f.write(r.content)


def download_photo(photo_url, save_dir, file_name):
    """Download photo from the given URL and save it to the specified directory."""
    response = requests.get(photo_url)
    if response.status_code == 200:
        with open(os.path.join(save_dir, file_name), 'wb') as f:
            f.write(response.content)

def save_photos_by_date(photos, base_dir):
    """Save photos into directories based on their creation date."""
    for photo in photos:
        creation_date = photo['mediaMetadata']['creationTime']
        date_obj = datetime.strptime(creation_date, '%Y-%m-%dT%H:%M:%S.%fZ')
        date_dir = os.path.join(base_dir, date_obj.strftime('%Y-%m-%d'))

        if not os.path.exists(date_dir):
            os.makedirs(date_dir)

        file_name = photo['filename']
        download_photo(photo['baseUrl'] + '=d', date_dir, file_name)

def main():
    creds = authenticate()
    service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

    # Define the date range to fetch photos
    start_date = datetime(year=2023, month=9, day=1)
    end_date = datetime(year=2024, month=10, day=15)

    # Fetch photos from Google Photos based on the date range
    photos = fetch_photos_by_date(service, start_date, end_date)
    # photos = fetch_photos(creds)

    # Save photos to directories categorized by date
    save_photos_by_date(photos, 'DownloadedPhotos')


if __name__ == '__main__':
    main()