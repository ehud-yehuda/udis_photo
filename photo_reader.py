import os
import json
import datetime
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import io
import json

# Define the scope for Google Photos API
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']


def authenticate():
    """Authenticate the user and return credentials."""
    creds = None
    # Load credentials from token.json if it exists
    file_path: str = 'cred/secrets_fake.json'
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


def fetch_photos(creds):
    """Fetch photos from Google Photos."""
    headers = {'Authorization': f'Bearer {creds.token}'}
    url = 'https://photoslibrary.googleapis.com/v1/mediaItems'
    photos = []

    while url:
        response = requests.get(url, headers=headers)
        data = response.json()

        if 'mediaItems' in data:
            photos.extend(data['mediaItems'])

        # Get the next page token
        url = data.get('nextPageToken')
        if url:
            url = f'https://photoslibrary.googleapis.com/v1/mediaItems?pageToken={url}'

    return photos


def save_photos_by_date(photos):
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


def main():
    creds = authenticate()
    photos = fetch_photos(creds)
    save_photos_by_date(photos)
    print("Photos have been organized by date.")


if __name__ == '__main__':
    main()