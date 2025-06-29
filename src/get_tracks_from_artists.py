import requests
import json
from dotenv import load_dotenv
import os

bearer_token = "BQAW71Zoicyjbnh9sa7XoJQXJon_RsN0arTtDslZwTp92ExpMqOjQIUzko3mQQ-IP8s_ioaAYnOBYeBXfo3JyBTumPAdK39QjJNzdzjWQftmFbq7KkeC5TG8hJO61pfBPZetOiQD6Mk"
# Trocar para o seu token atualizado

headers = {
    'Authorization': f'Bearer {bearer_token}',
    'Content-Type': 'application/json'
}

search_url = 'https://api.spotify.com/v1/search'

artist = 'Matheus e Kauan'  # nome do artista 
params = {'q': artist, 'type': 'artist', 'limit': 1}
resp = requests.get(search_url, params=params, headers=headers)
artist = resp.json()['artists']['items'][0]

artist_data = {
    'id': artist['id'],
    'name': artist['name'],
    'genres': artist['genres'],
    'followers': artist['followers']['total'],
    'popularity': artist['popularity']
}

# Buscar álbuns
albums_url = f'https://api.spotify.com/v1/artists/{artist_data["id"]}/albums'
albums = []
params = {'limit': 50, 'include_groups': 'album,single'}
next_url = albums_url

cont = 0

while next_url: # Loop para buscar todas as páginas de álbuns
    resp = requests.get(next_url, params=params, headers=headers)
    data = resp.json()
    """ with open(f'albums_page_{cont}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4) """
    cont += 1
    for album in data['items']:
        album_data = {
            'id': album['id'],
            'name': album['name'],
            'release_date': album['release_date'],
            'total_tracks': album['total_tracks'],
            'album_type': album['album_type'],
            'images': album['images'],
            'tracks': []
        }
        
        # Buscar faixas do álbum
        tracks_url = f'https://api.spotify.com/v1/albums/{album["id"]}/tracks'
        track_resp = requests.get(tracks_url, headers=headers)
        track_data = track_resp.json()
        print(track_data)
        
        for track in track_data['items']:
            track_info = {
                'name': track['name'],
                'duration_ms': track['duration_ms'],
            }
            album_data['tracks'].append(track_info)
        
        albums.append(album_data)
    
    next_url = data.get('next')

final_data = {
    'artist': artist_data,
    'albums': albums
}

with open(f'{artist_data["name"].replace(" ", "_").lower()}_data.json',
           'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=4)

print(f"JSON salvo como '{artist_data['name'].replace(' ', '_').lower()}_data.json'")