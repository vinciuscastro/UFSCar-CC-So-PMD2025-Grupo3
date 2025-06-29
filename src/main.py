import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os

load_dotenv()

client_id = os.getenv('Client_ID')
client_secret = os.getenv('Client_Secret')

def main():
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    artist_id = '0TnOYISbd1XYRBk9myaseg'  
    artist = sp.artist_albums(artist_id, album_type='album,single', limit=50)
    print(artist)

if __name__ == "__main__":
    main()
