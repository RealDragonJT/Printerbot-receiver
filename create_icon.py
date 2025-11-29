"""
Generate icon files for PrintsAlot Receiver.
Run this once to create the app icon.
"""
from PIL import Image, ImageDraw
import os

def create_printer_icon(size=256):
    """Create a printer icon."""
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Scale factor
    s = size / 64
    
    # Colors
    body_color = '#4CAF50'  # Green
    paper_color = '#FFFFFF'
    shadow_color = '#388E3C'
    
    # Main body (with shadow)
    draw.rounded_rectangle(
        [int(10*s), int(22*s), int(54*s), int(48*s)], 
        radius=int(4*s), 
        fill=shadow_color
    )
    draw.rounded_rectangle(
        [int(8*s), int(20*s), int(52*s), int(46*s)], 
        radius=int(4*s), 
        fill=body_color
    )
    
    # Paper input tray (top)
    draw.rectangle(
        [int(16*s), int(8*s), int(48*s), int(22*s)], 
        fill=paper_color
    )
    
    # Paper output (bottom) 
    draw.rectangle(
        [int(14*s), int(44*s), int(50*s), int(58*s)], 
        fill=paper_color
    )
    
    # Paper lines
    draw.line(
        [int(18*s), int(48*s), int(46*s), int(48*s)], 
        fill='#CCCCCC', 
        width=max(1, int(s))
    )
    draw.line(
        [int(18*s), int(52*s), int(42*s), int(52*s)], 
        fill='#CCCCCC', 
        width=max(1, int(s))
    )
    
    # Indicator light
    draw.ellipse(
        [int(42*s), int(26*s), int(48*s), int(32*s)], 
        fill='#81C784'
    )
    
    return image


def main():
    # Create assets directory if needed
    os.makedirs('assets', exist_ok=True)
    
    # Create icon at various sizes for ICO file
    sizes = [16, 32, 48, 64, 128, 256]
    images = [create_printer_icon(size) for size in sizes]
    
    # Save as ICO (Windows icon format)
    ico_path = 'assets/icon.ico'
    images[0].save(
        ico_path, 
        format='ICO', 
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"Created: {ico_path}")
    
    # Also save as PNG for other uses
    png_path = 'assets/icon.png'
    images[-1].save(png_path, format='PNG')
    print(f"Created: {png_path}")
    
    print("\nIcon files created successfully!")


if __name__ == "__main__":
    main()

