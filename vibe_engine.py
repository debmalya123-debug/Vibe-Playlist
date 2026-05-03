import os
import json
from google import genai
from google.genai import types
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from PIL import Image
import requests

# Load environment variables
load_dotenv(override=True)

# Configure APIs
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=120000)
)

# Spotify API has been bypassed due to developer API restrictions
sp = None

def get_vibe_playlist(image_file, model_type='gemini', language='any'):
    """
    Analyzes the image using Gemini and fetches a matching playlist.
    model_type: 'gemini' or 'custom_ai' (ReccoBeats)
    language: Language preference for songs (e.g., 'any', 'english', 'hindi', 'korean', 'japanese', 'spanish')
    """
    try:
        # 1. Analyze Image with Gemini
        img = Image.open(image_file)
        
        # Convert to RGB if needed to avoid transparency issues
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Resize image to reduce API payload size and processing time
        img.thumbnail((1024, 1024))
        
        # Map language to natural language
        language_map = {
            'any': 'Any',
            'english': 'English',
            'hindi': 'Hindi',
            'korean': 'Korean',
            'japanese': 'Japanese',
            'spanish': 'Spanish'
        }
        
        language_name = language_map.get(language.lower(), 'Any')
        
        # Create different prompts based on language selection
        if language_name == 'Any':
            prompt = """
        Analyze this image and determine its mood. 
        
        Task 1: Curate a playlist of 10 songs that perfectly match this mood (Title - Artist).
        Task 2: Identify ONE perfect "seed song" (Title - Artist) for a recommendation engine.
        
        Return a JSON object with the following keys:
        - mood_description: a short sentence describing the mood.
        - genres: a list of 3 music genres that match the mood.
        - songs: a list of objects, each with 'title' and 'artist' keys (The curated playlist).
        - seed_song: an object with 'title' and 'artist' keys (The seed song).
        
        Return ONLY the JSON string, no markdown formatting.
        """
        else:
            prompt = f"""
        Analyze this image and determine its mood. 
        
        Task 1: Curate a playlist of 10 songs IN {language_name.upper()} ONLY that perfectly match this mood (Title - Artist).
        Task 2: Identify ONE perfect "seed song" (Title - Artist) IN {language_name.upper()} for a recommendation engine.
        
        IMPORTANT: All songs MUST be in {language_name} language. Do not include songs in other languages.
        
        Return a JSON object with the following keys:
        - mood_description: a short sentence describing the mood.
        - genres: a list of 3 music genres that match the mood.
        - songs: a list of objects, each with 'title' and 'artist' keys (The curated playlist in {language_name}).
        - seed_song: an object with 'title' and 'artist' keys (The seed song in {language_name}).
        
        Return ONLY the JSON string, no markdown formatting.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img]
        )
        text_response = response.text.strip()
        
        # Clean up potential markdown code blocks
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        vibe_data = json.loads(text_response)
        
        # Due to Spotify API restrictions, we directly format the Gemini output
        # to render as a list instead of querying Spotify.
        tracks = [{'name': song.get('title'), 'artist': song.get('artist')} for song in vibe_data.get('songs', [])]

        # Extract color palette from image
        colors = extract_color_palette(image_file)
        
        return {
            'mood': vibe_data.get('mood_description'),
            'genres': vibe_data.get('genres'),
            'tracks': tracks,
            'colors': colors
        }

    except Exception as e:
        print(f"Error in vibe_engine: {e}")
        return {'error': str(e)}

def refine_playlist(current_mood, modifier):
    """
    Refines the playlist based on a modifier using ReccoBeats (via a new seed).
    """
    try:
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
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        text_response = response.text.strip()
        
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        vibe_data = json.loads(text_response)
        
        # Due to Spotify API restrictions, directly format the Gemini backup songs
        tracks = [{'name': song.get('title'), 'artist': song.get('artist')} for song in vibe_data.get('backup_songs', [])]
            
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

def extract_color_palette(image_file, num_colors=6):
    """
    Extract dominant colors from an image.
    Returns a list of hex color codes.
    """
    try:
        # Reset file pointer if needed
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        
        img = Image.open(image_file)
        
        # Resize for faster processing
        img = img.resize((150, 150))
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Quantize to reduce colors
        img_quantized = img.quantize(colors=num_colors, method=2)
        
        # Get palette and convert to RGB
        palette = img_quantized.getpalette()
        
        # Extract colors
        colors = []
        for i in range(num_colors):
            r = palette[i * 3]
            g = palette[i * 3 + 1]
            b = palette[i * 3 + 2]
            
            # Convert to hex
            hex_color = f'#{r:02x}{g:02x}{b:02x}'
            
            # Calculate brightness to filter out very dark/light colors
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            
            # Only include colors with reasonable brightness (not too dark or too light)
            if 30 < brightness < 225:
                colors.append({
                    'hex': hex_color,
                    'rgb': {'r': r, 'g': g, 'b': b}
                })
        
        # Ensure we have at least some colors
        if len(colors) < 3:
            # Fallback colors if extraction fails
            colors = [
                {'hex': '#667eea', 'rgb': {'r': 102, 'g': 126, 'b': 234}},
                {'hex': '#764ba2', 'rgb': {'r': 118, 'g': 75, 'b': 162}},
                {'hex': '#f093fb', 'rgb': {'r': 240, 'g': 147, 'b': 251}}
            ]
        
        return colors[:6]  # Return max 6 colors
        
    except Exception as e:
        print(f"Error extracting colors: {e}")
        # Return default gradient colors
        return [
            {'hex': '#667eea', 'rgb': {'r': 102, 'g': 126, 'b': 234}},
            {'hex': '#764ba2', 'rgb': {'r': 118, 'g': 75, 'b': 162}},
            {'hex': '#f093fb', 'rgb': {'r': 240, 'g': 147, 'b': 251}}
        ]
