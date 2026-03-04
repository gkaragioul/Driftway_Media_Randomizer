#!/usr/bin/env python3
"""
Generate icon for PriveRandomizer app
"""

from PIL import Image, ImageDraw
import os

def create_icon():
    """Create a professional icon for PriveRandomizer"""
    
    # Create a 256x256 image with dark blue background
    size = 256
    img = Image.new('RGBA', (size, size), (20, 30, 70, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient-like background (concentric circles for depth)
    for i in range(size // 2, 0, -20):
        color = (20 + i // 4, 30 + i // 5, 70 + i // 3, 255)
        draw.ellipse([size//2 - i, size//2 - i, size//2 + i, size//2 + i], outline=color, width=2)
    
    # Draw play button (triangle) - primary focus
    play_button_points = [
        (80, 70),    # left point
        (80, 186),   # bottom left
        (180, 128),  # right point (center)
    ]
    draw.polygon(play_button_points, fill=(100, 200, 255, 255), outline=(200, 230, 255, 255))
    
    # Draw shuffle lines (two curved lines representing randomization)
    # Left shuffle line
    draw.line([(30, 50), (60, 50)], fill=(150, 220, 100, 255), width=4)
    draw.line([(40, 35), (70, 65)], fill=(150, 220, 100, 255), width=4)
    
    # Right shuffle lines
    draw.line([(196, 200), (226, 200)], fill=(150, 220, 100, 255), width=4)
    draw.line([(186, 215), (216, 185)], fill=(150, 220, 100, 255), width=4)
    
    # Draw a film strip border (represents media)
    # Top strip
    draw.rectangle([(20, 210), (236, 240)], fill=(255, 200, 0, 200), outline=(255, 150, 0, 255), width=2)
    
    # Add small squares in the film strip
    for i in range(3):
        x = 40 + i * 60
        draw.rectangle([(x, 215), (x + 30, 235)], outline=(255, 150, 0, 255), width=1)
    
    # Save as ICO in multiple sizes
    icon_path = os.path.dirname(__file__)
    
    # Save as 256x256 PNG first (for PyInstaller)
    img.save(os.path.join(icon_path, 'icon.png'))
    
    # Create ICO file with multiple resolutions
    icon_sizes = [16, 32, 64, 128, 256]
    icon_images = []
    
    for icon_size in icon_sizes:
        icon_img = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        icon_images.append(icon_img)
    
    # Save as ICO
    icon_images[0].save(
        os.path.join(icon_path, 'icon.ico'),
        format='ICO',
        sizes=[(s, s) for s in icon_sizes]
    )
    
    print("✓ Icon created: icon.png")
    print("✓ Icon created: icon.ico")
    print(f"  Location: {icon_path}")

if __name__ == '__main__':
    create_icon()
