

import os
import math

from typing import Tuple
from PIL import Image, ImageDraw, ImageFont

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import pandas as pd
from PIL import Image, ExifTags
import piexif

import piexif

# %% Functions
def calculate_initial_compass_bearing(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Calculate the change in coordinates
    dlon = lon2 - lon1

    # Calculate the bearing
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    bearing = math.atan2(x, y)

    bearing = math.degrees(bearing)
    bearing = (bearing + 180) % 360 - 180

    return 129#int(bearing)


def save_image_with_metadata(image_path, metadata):
    # Open the image
    img = Image.open(image_path)

    # Load the existing EXIF data
    exif_dict = piexif.load(img.info.get('exif', b''))

    # Assign GPS information (make sure to follow EXIF format for GPS data)
    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: metadata['GPSLatitudeRef'],
        piexif.GPSIFD.GPSLatitude: metadata['GPSLatitude'],
        piexif.GPSIFD.GPSLongitudeRef: metadata['GPSLongitudeRef'],
        piexif.GPSIFD.GPSLongitude: metadata['GPSLongitude']
    }

    exif_dict['GPS'] = gps_ifd

    # Convert the updated EXIF data back to bytes
    exif_bytes = piexif.dump(exif_dict)

    # Save the image with the updated EXIF data
    img.save(image_path, "jpeg", exif=exif_bytes)
    img.close()


def get_decimal_from_dms(dms):

    degrees = dms[0] 
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0
    return round(degrees+minutes+seconds,5)

def get_comments_info(image_path:str) -> Tuple:
    with Image.open(image_path) as img:
        info = img._getexif()
        if 34853 not in info:
            return {}
        
        data_dict = info[34853]
        cord1 = get_decimal_from_dms(data_dict[2])
        cord2 = get_decimal_from_dms(data_dict[4])
        date_month_year = info[36867].split(' ')[0]
        hour_min_second = info[36867].split(' ')[0]
        angle = calculate_initial_compass_bearing(
                lat1=cord1, lon1=cord2, lat2=0.0, lon2=0.0
            )


        return cord1,cord2,date_month_year,hour_min_second,angle

def create_standardized_overlay_image(image_path: str, cord1: str, cord2: str, date_month_year: str, hour_min_second: str, angle: float, glocation: str, component: str, defect_line1: str, defect_line2: str,idd:int,output_folder:str) -> str:
    ''' creates the overlay and add text'''
    with Image.open(image_path) as img:
        base_width, base_height = img.size
    
    text_size = int(base_height * 0.027)
    
    box_height = base_height // 8
    
    overlay_image = Image.new('RGBA', (base_width, base_height), (255, 255, 255, 0))
    
    draw = ImageDraw.Draw(overlay_image, 'RGBA')
    
    transparency = 128
    
    font = ImageFont.FreeTypeFont(r"C:\Windows\Fonts\CONSOLA.ttf", size=text_size)

    def draw_boxes_with_text(y_position, text_lines):
        num_boxes = len(text_lines)
        box_width = base_width // num_boxes
        for i, lines in enumerate(text_lines):
            x_position = i * box_width
            box = (x_position, y_position, x_position + box_width, y_position + box_height)
            draw.rectangle(box, fill=(0, 0, 0, transparency))
            
            for j, line in enumerate(lines):
                text_bbox = draw.textbbox((0, 0), line, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = x_position + (box_width - text_width) // 2
                if j ==1:
                    text_y = y_position + 20+ (box_height - text_height * len(lines)) // 2 + (text_height * j)
                else:
                    text_y = y_position + (box_height - text_height * len(lines)) // 2 + (text_height * j)
                draw.text((text_x, text_y), line, fill="white", font=font)
                
    top_boxes_text = [
        ['DIRECTION', f"{angle} deg (T)"],
        [f"{cord1}°S", f"{cord2}°E"],
        ["ACCURACY", "DATUM WGS84"]
    ]
    
    bottom_boxes_text = [
        [glocation, component],
        [defect_line1, defect_line2],
        [date_month_year, f"{hour_min_second}+10:00"]
    ]
    
    draw_boxes_with_text(0, top_boxes_text)  # Top boxes
    draw_boxes_with_text(base_height - box_height, bottom_boxes_text)  # Bottom boxes
    
    with Image.open(image_path) as base_img:
        combined_image = Image.alpha_composite(base_img.convert('RGBA'), overlay_image)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    combined_image_path = f'{glocation}_{component}_{defect_line1}_{defect_line2}_{idd}.png'
    combined_image.save(f"{output_folder}/{combined_image_path}")
    
    return combined_image_path


def copy_and_rotate(image_path: str, rotation_angle: int):
    # Open the image
    image = Image.open(image_path)

    # Check if the image has EXIF data
    exif_data = None
    if "exif" in image.info:
        exif_data = image.info['exif']

    # Rotate the image
    rotated_image = image.rotate(rotation_angle, expand=True)

    # Create a new filename for the rotated image
    new_filename = f"{image_path.rsplit('.', 1)[0]}_rotated.{image_path.rsplit('.', 1)[-1]}"

    # Save the rotated image with the original EXIF data (if present)
    rotated_image.save(new_filename, "JPEG", exif=exif_data)

    # Close the image files
    image.close()
    rotated_image.close()

    return new_filename


# %% engine

if __name__ =='__main__':
    image_path = 'images\GOPR0200.JPG'
    output_folder = 'images\filled'
    cord1,cord2,date_month_year,hour_min_second,angle = get_comments_info(image_path)
    create_standardized_overlay_image(image_path,
                                    cord1=cord1,
                                    cord2=cord2, 
                                    date_month_year=date_month_year,
                                    hour_min_second=hour_min_second,
                                    angle=angle,
                                    glocation='Microcell Building',
                                    component = 'Monorail 5024',
                                    defect_line1='Corrosion and ',
                                    defect_line2= 'dmg in PC',
                                    idd = 3,
                                    output_folder=output_folder)




    