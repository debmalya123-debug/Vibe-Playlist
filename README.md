# 🎵 VibePlaylist

**Transform images into mood-matched playlists**

VibePlaylist is an AI-powered web application that analyzes the emotional essence of your images and generates perfectly curated Spotify playlists to match the vibe. Upload a photo, and let AI discover the soundtrack to your moment.

![VibePlaylist](https://img.shields.io/badge/AI-Powered-blueviolet) ![Flask](https://img.shields.io/badge/Flask-2.0+-green) ![Gemini](https://img.shields.io/badge/Gemini-2.5-orange)

---

## ✨ Features

### 🎨 **Image-to-Mood Analysis**

- Upload any image and receive instant mood interpretation
- Advanced AI vision analysis using Google's Gemini 2.5 Flash
- Extracts dominant color palette from your image
- Real-time background adaptation to match image colors

### 🎵 **Dual AI Recommendation Engines**

- **Gemini 2.5**: Direct AI curation based on mood and context
- **Custom AI**: ReccoBeats-powered algorithmic recommendations
- Switch between engines with a single click
- Smart fallback system ensures you always get results

### 🎭 **Mood Particle Animation**

- Dynamic particle system that responds to your playlist's vibe
- 60fps canvas-based animations
- Color-matched particles using extracted palette
- Creates an immersive, living atmosphere

### 🎛️ **Vibe Tuner**

- Real-time playlist refinement
- Adjust mood with preset modifiers: More Energy, Chill Out, Darker, Happier
- Instant playlist regeneration without re-uploading

### 🎧 **Spotify Integration**

- Embedded Spotify players for instant preview
- Direct links to Spotify for each track
- Album art and artist information
- No OAuth required for playback

### 📷 **Mobile Camera Support** ⭐ NEW

- Capture images directly from your mobile device camera
- Seamless switching between front and back cameras
- Live camera preview before capture
- **Note**: Requires HTTPS on mobile - see [Mobile Camera Setup Guide](MOBILE_CAMERA_SETUP.md)

### 🌊 **Premium UI/UX**

- "Liquid Glass" aesthetic with animated mesh gradients
- Glassmorphism effects with depth and blur
- Micro-interactions and smooth animations
- Fully responsive design (mobile/tablet/desktop)
- Gradient text effects and custom scrollbars

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Spotify Developer Account
- Google Gemini API Key

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/vibe-playlist.git
   cd vibe-playlist
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the root directory:

   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   ```

   **Get your API keys:**

   - **Gemini API**: [Google AI Studio](https://makersuite.google.com/app/apikey)
   - **Spotify API**: [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

5. **Run the application**

   ```bash
   python app.py
   ```

6. **Open your browser**
   ```
   http://localhost:5000
   ```

---

## 🛠️ Technology Stack

### Backend

- **Flask** - Web framework
- **Google Gemini 2.5 Flash** - Image analysis and mood detection
- **Spotipy** - Spotify API wrapper
- **Pillow (PIL)** - Image processing and color extraction
- **Requests** - ReccoBeats API integration

### Frontend

- **Vanilla JavaScript** - Dynamic UI interactions
- **Canvas API** - Mood particle animations
- **Tailwind CSS** - Utility-first styling
- **Custom CSS** - Glassmorphism and animations

### APIs

- **Google Gemini API** - AI vision and text generation
- **Spotify Web API** - Music metadata and search
- **ReccoBeats API** - Algorithmic music recommendations

---

## 📁 Project Structure

```
vibe-playlist/
├── app.py                  # Flask application & routes
├── vibe_engine.py          # Core logic: mood analysis, recommendations, color extraction
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── static/
│   └── css/
│       └── style.css       # Premium UI styling
├── templates/
│   └── index.html          # Main application interface
└── README.md              # You are here!
```

---

## 🎨 How It Works

1. **Upload Image** → User uploads any image (photo, artwork, screenshot)

2. **AI Analysis** → Gemini analyzes the image and identifies:

   - Emotional mood (e.g., "Energetic and uplifting")
   - Music genres (e.g., "Pop, Dance, Electronic")
   - Seed song for recommendations
   - Curated song list (Gemini mode)

3. **Color Extraction** → PIL extracts 6 dominant colors from the image

4. **Playlist Generation**:

   - **Gemini Mode**: Uses AI's curated song list
   - **Custom AI Mode**: Uses seed song → ReccoBeats API → Spotify track details

5. **Visual Transformation**:

   - Background blobs adopt extracted colors
   - Particle system activates with color-matched animations
   - UI displays mood, genres, and tracks

6. **Playback** → Spotify embeds allow instant preview

---

## 🎯 API Usage

### Gemini API

```python
model = genai.GenerativeModel('gemini-2.5-flash-lite')
response = model.generate_content([prompt, image])
```

### Spotify API

```python
results = sp.search(q=query, type='track', limit=1)
track_details = sp.tracks([track_id])
```

### ReccoBeats API

```python
url = f"https://api.reccobeats.com/v1/track/recommendation?seeds={spotify_id}&size=10"
response = requests.get(url)
```

---

## 🎨 Color Palette Extraction

VibePlaylist uses PIL's quantization algorithm to extract dominant colors:

```python
def extract_color_palette(image_file, num_colors=6):
    img = Image.open(image_file).resize((150, 150))
    img_quantized = img.quantize(colors=num_colors, method=2)
    palette = img_quantized.getpalette()
    # Extract RGB → Convert to hex → Filter by brightness
    return colors
```

**Applied to:**

- Background gradient blobs
- Particle animation system
- Creates cohesive visual experience

---

## 🎛️ Features Breakdown

### Vibe Tuner Modifiers

- **More Energy** → Increases tempo and intensity
- **Chill Out** → Mellower, relaxed tracks
- **Darker** → Moodier, deeper vibes
- **Happier** → Uplifting, positive tracks

### Recommendation Engines

| Engine     | Method                       | Best For                                    |
| ---------- | ---------------------------- | ------------------------------------------- |
| Gemini 2.5 | AI curation based on context | Semantic mood matching, thematic playlists  |
| Custom AI  | ReccoBeats algorithmic       | Discovery, similar tracks, musical patterns |

---

## 🚀 Future Enhancements

- [ ] Playlist history and favorites
- [ ] Share playlists via link
- [ ] Export to Spotify (OAuth)
- [ ] Multi-image mood blending
- [ ] Voice input mood description
- [ ] Weekly mood reports
- [ ] User accounts and saved preferences

---

## 📧 Contact

**Debmalya Paul**

- Email: debmalya0603@gmaiil.com

---

## 🌟 Show Your Support

If you found this project interesting, please give it a ⭐️!

---

<div align="center">
  <sub>Made with ❤️ by Debmalya Paul</sub>
</div>
