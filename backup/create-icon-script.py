#!/usr/bin/env python3
"""
Create an icon for the Break Reminder application
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Create a simple clock icon for the break reminder"""
    
    # Create a 256x256 image with transparent background
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw clock circle with gradient effect
    center = size // 2
    radius = size // 2 - 20
    
    # Outer circle (shadow)
    draw.ellipse(
        [center - radius - 5, center - radius - 5, 
         center + radius + 5, center + radius + 5],
        fill=(100, 100, 100, 100)
    )
    
    # Main clock circle with gradient colors
    draw.ellipse(
        [center - radius, center - radius, 
         center + radius, center + radius],
        fill=(70, 130, 180),  # Steel blue
        outline=(255, 255, 255),
        width=8
    )
    
    # Inner circle
    draw.ellipse(
        [center - radius + 15, center - radius + 15, 
         center + radius - 15, center + radius - 15],
        fill=(135, 206, 235),  # Sky blue
    )
    
    # Clock center dot
    dot_radius = 8
    draw.ellipse(
        [center - dot_radius, center - dot_radius,
         center + dot_radius, center + dot_radius],
        fill=(25, 25, 112)  # Midnight blue
    )
    
    # Clock hands
    # Hour hand (shorter, pointing to 10)
    hour_angle = -120  # degrees
    hour_length = radius * 0.5
    hour_end_x = center + hour_length * 0.866  # cos(30°)
    hour_end_y = center - hour_length * 0.5    # sin(30°)
    draw.line(
        [(center, center), (hour_end_x, hour_end_y)],
        fill=(25, 25, 112),
        width=10
    )
    
    # Minute hand (longer, pointing to 12)
    minute_length = radius * 0.7
    minute_end_x = center
    minute_end_y = center - minute_length
    draw.line(
        [(center, center), (minute_end_x, minute_end_y)],
        fill=(25, 25, 112),
        width=8
    )
    
    # Add hour markers
    for hour in range(12):
        angle = hour * 30 - 90  # 30 degrees per hour, -90 to start at top
        import math
        angle_rad = math.radians(angle)
        
        # Outer position
        outer_x = center + (radius - 25) * math.cos(angle_rad)
        outer_y = center + (radius - 25) * math.sin(angle_rad)
        
        # Inner position
        inner_x = center + (radius - 35) * math.cos(angle_rad)
        inner_y = center + (radius - 35) * math.sin(angle_rad)
        
        # Draw hour marker
        if hour % 3 == 0:  # Emphasize 12, 3, 6, 9
            draw.line(
                [(inner_x, inner_y), (outer_x, outer_y)],
                fill=(255, 255, 255),
                width=4
            )
        else:
            draw.ellipse(
                [outer_x - 3, outer_y - 3, outer_x + 3, outer_y + 3],
                fill=(255, 255, 255)
            )
    
    # Add a small coffee cup icon in corner to indicate break
    cup_x, cup_y = size - 60, size - 60
    # Cup body
    draw.rectangle([cup_x, cup_y, cup_x + 30, cup_y + 35], 
                   fill=(139, 69, 19))  # Brown
    # Cup handle
    draw.arc([cup_x + 25, cup_y + 10, cup_x + 40, cup_y + 25], 
             270, 90, fill=(139, 69, 19), width=3)
    # Steam lines
    for i in range(3):
        x = cup_x + 5 + i * 8
        draw.line([(x, cup_y - 5), (x + 2, cup_y - 15)], 
                  fill=(200, 200, 200), width=2)
    
    # Save as multiple sizes for the ICO file
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = []
    
    for size_tuple in sizes:
        resized = img.resize(size_tuple, Image.Resampling.LANCZOS)
        icons.append(resized)
    
    # Save as ICO file with multiple resolutions
    icons[0].save('break_reminder.ico', format='ICO', 
                  sizes=sizes, append_images=icons[1:])
    
    # Also save as PNG for other uses
    img.save('break_reminder.png', 'PNG')
    
    print("✅ Icon created successfully!")
    print("   - break_reminder.ico (multiple sizes)")
    print("   - break_reminder.png (256x256)")
    
    return 'break_reminder.ico'

if __name__ == "__main__":
    # Check if PIL/Pillow is installed
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Installing Pillow for icon creation...")
        import subprocess
        subprocess.check_call(["pip", "install", "Pillow"])
        from PIL import Image, ImageDraw
    
    icon_path = create_icon()
    print(f"\nYou can now use '{icon_path}' with Nuitka or PyInstaller!")