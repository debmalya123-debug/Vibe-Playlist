from flask import Flask, render_template, request, jsonify
from vibe_engine import get_vibe_playlist, refine_playlist
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    model_type = request.form.get('model_type', 'gemini')
    language = request.form.get('language', 'any')
    result = get_vibe_playlist(image_file, model_type, language)
    
    if 'error' in result:
        return jsonify(result), 500
        
    return jsonify(result)

@app.route('/refine', methods=['POST'])
def refine():
    data = request.json
    current_mood = data.get('mood')
    modifier = data.get('modifier')
    
    if not current_mood or not modifier:
        return jsonify({'error': 'Missing mood or modifier'}), 400
        
    result = refine_playlist(current_mood, modifier)
    
    if 'error' in result:
        return jsonify(result), 500
        
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
