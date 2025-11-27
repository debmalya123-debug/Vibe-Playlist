import os
import json
import google.generativeai as genai
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# Configure APIs
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
))

def get_vibe_playlist(image_file):
    """
    Analyzes the image using Gemini and fetches a matching playlist from Spotify.
    """
    try:
        # 1. Analyze Image with Gemini
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        img = Image.open(image_file)
        
        prompt = """
        Analyze this image and determine its mood. 
        Then, curate a playlist of 10 songs that perfectly match this mood.
        
        Return a JSON object with the following keys:
        - mood_description: a short sentence describing the mood.
        - genres: a list of 3 music genres that match the mood.
        - songs: a list of objects, each with 'title' and 'artist' keys.
        
        Return ONLY the JSON string, no markdown formatting.
        """
        
        response = model.generate_content([prompt, img])
        return _process_gemini_response(response.text)

    except Exception as e:
        print(f"Error in vibe_engine: {e}")
        return {'error': str(e)}

def refine_playlist(current_mood, modifier):
    """
    Refines the playlist based on a modifier (e.g., 'More Energetic').
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        prompt = f"""
        The current mood is: "{current_mood}".
        The user wants to make it: "{modifier}".
        
        Curate a NEW playlist of 10 songs that matches the modified mood.
        
        Return a JSON object with the following keys:
        - mood_description: a short sentence describing the new mood.
        - genres: a list of 3 music genres that match the new mood.
        - songs: a list of objects, each with 'title' and 'artist' keys.
        
        Return ONLY the JSON string, no markdown formatting.
        """
        
        response = model.generate_content(prompt)
        return _process_gemini_response(response.text)
        
    except Exception as e:
        print(f"Error in refine_playlist: {e}")
        return {'error': str(e)}

def _process_gemini_response(text_response):
    try:
        text_response = text_response.strip()
        # Clean up potential markdown code blocks
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        vibe_data = json.loads(text_response)
        
        # Query Spotify Search for each song
        tracks = []
        for song in vibe_data.get('songs', []):
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
            
        return {
            'mood': vibe_data.get('mood_description'),
            'genres': vibe_data.get('genres'),
            'tracks': tracks
        }
    except Exception as e:
        print(f"Error processing Gemini response: {e}")
        return {'error': str(e)}

    except Exception as e:
        print(f"Error in vibe_engine: {e}")
        return {'error': str(e)}
