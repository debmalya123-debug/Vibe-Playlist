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
