import os
import json
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from PIL import Image
import requests

# Load environment variables
load_dotenv()

# Configure APIs
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
))

def get_vibe_playlist(image_file):
    """
    Analyzes the image using Gemini and fetches a matching playlist using ReccoBeats.
    """
    try:
        # 1. Analyze Image with Gemini to get Mood and Seed Track
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        img = Image.open(image_file)
        
        prompt = """
        Analyze this image and determine its mood. 
        Then, identify ONE perfect "seed song" (Title - Artist) that captures this vibe.
        Also provide a backup list of 10 songs in case the recommendation engine fails.
        
        Return a JSON object with the following keys:
        - mood_description: a short sentence describing the mood.
        - genres: a list of 3 music genres that match the mood.
        - seed_song: an object with 'title' and 'artist' keys.
        - backup_songs: a list of objects, each with 'title' and 'artist' keys.
        
        Return ONLY the JSON string, no markdown formatting.
        """
        
        response = model.generate_content([prompt, img])
        text_response = response.text.strip()
        
        # Clean up potential markdown code blocks
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        vibe_data = json.loads(text_response)
        
        # 2. Get Seed Track ID from Spotify
        seed_song = vibe_data.get('seed_song')
        seed_track_id = None
        
        if seed_song:
            query = f"track:{seed_song['title']} artist:{seed_song['artist']}"
            try:
                results = sp.search(q=query, type='track', limit=1)
                items = results['tracks']['items']
                if items:
                    seed_track_id = items[0]['id']
            except Exception as e:
                print(f"Error searching for seed song: {e}")

        # 3. Get Recommendations from ReccoBeats (or fallback)
        tracks = []
        if seed_track_id:
            tracks = _get_reccobeats_recommendations(seed_track_id)
            
        # Fallback to Gemini's backup list if ReccoBeats fails or no seed found
        if not tracks:
            print("Falling back to Gemini curation...")
            tracks = _fetch_spotify_details(vibe_data.get('backup_songs', []))

        return {
            'mood': vibe_data.get('mood_description'),
            'genres': vibe_data.get('genres'),
            'tracks': tracks
        }

    except Exception as e:
        print(f"Error in vibe_engine: {e}")
        return {'error': str(e)}

def refine_playlist(current_mood, modifier):
    """
    Refines the playlist based on a modifier using ReccoBeats (via a new seed).
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        prompt = f"""
        The current mood is: "{current_mood}".
        The user wants to make it: "{modifier}".
        
        Identify a NEW "seed song" (Title - Artist) that matches this modified mood.
        Also provide a backup list of 10 songs.
        
        Return a JSON object with the following keys:
        - mood_description: a short sentence describing the new mood.
        - genres: a list of 3 music genres that match the new mood.
        - seed_song: an object with 'title' and 'artist' keys.
        - backup_songs: a list of objects, each with 'title' and 'artist' keys.
        
        Return ONLY the JSON string, no markdown formatting.
        """
        
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        vibe_data = json.loads(text_response)
        
        # Get Seed Track ID
        seed_song = vibe_data.get('seed_song')
        seed_track_id = None
        
        if seed_song:
            query = f"track:{seed_song['title']} artist:{seed_song['artist']}"
            try:
                results = sp.search(q=query, type='track', limit=1)
                items = results['tracks']['items']
                if items:
                    seed_track_id = items[0]['id']
            except Exception as e:
                print(f"Error searching for seed song: {e}")
                
        # Get Recommendations
        tracks = []
        if seed_track_id:
            tracks = _get_reccobeats_recommendations(seed_track_id)
            
        if not tracks:
            tracks = _fetch_spotify_details(vibe_data.get('backup_songs', []))
            
        return {
            'mood': vibe_data.get('mood_description'),
            'genres': vibe_data.get('genres'),
            'tracks': tracks
        }
        
    except Exception as e:
        print(f"Error in refine_playlist: {e}")
        return {'error': str(e)}

def _get_reccobeats_recommendations(seed_track_id):
    """
    Fetches recommendations from ReccoBeats API.
    """
    try:
        url = f"https://api.reccobeats.com/v1/track/recommendation?seeds={seed_track_id}&size=10"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # ReccoBeats returns tracks in 'content' key
            # The 'id' in the response might be internal, so we extract Spotify ID from 'href'
            # href format: https://open.spotify.com/track/{spotify_id}
            spotify_ids = []
            for track in data.get('content', []):
                href = track.get('href', '')
                if 'open.spotify.com/track/' in href:
                    spotify_id = href.split('track/')[-1].split('?')[0]
                    spotify_ids.append(spotify_id)
            
            if spotify_ids:
                return _fetch_spotify_details_by_ids(spotify_ids)
                
        print(f"ReccoBeats API Error: {response.status_code} - {response.text}")
        return []
    except Exception as e:
        print(f"Error calling ReccoBeats: {e}")
        return []

def _fetch_spotify_details(songs_list):
    """
    Helper to search Spotify for a list of songs (Title/Artist).
    """
    tracks = []
    for song in songs_list:
        query = f"track:{song['title']} artist:{song['artist']}"
        try:
            results = sp.search(q=query, type='track', limit=1)
            items = results['tracks']['items']
            if items:
                track = items[0]
                tracks.append({
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    'spotify_url': track['external_urls']['spotify'],
                    'preview_url': track['preview_url'],
                    'id': track['id']
                })
        except Exception as e:
            print(f"Error searching for {song['title']}: {e}")
            continue
    return tracks

def _fetch_spotify_details_by_ids(track_ids):
    """
    Helper to fetch details for a list of Spotify Track IDs.
    """
    tracks = []
    # Spotify allows fetching up to 50 tracks at once
    try:
        results = sp.tracks(track_ids)
        for track in results['tracks']:
            if track:
                tracks.append({
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    'spotify_url': track['external_urls']['spotify'],
                    'preview_url': track['preview_url'],
                    'id': track['id']
                })
    except Exception as e:
        print(f"Error fetching track details: {e}")
    return tracks
