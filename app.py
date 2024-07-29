import os
from typing import Tuple
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from _testing_image_overlay import create_standardized_overlay_image,get_comments_info,copy_and_rotate
import pandas as pd
import numpy as np

def scan_and_write_excel(directory: str, excel_path: str) -> None:
    """
    Scans a directory for JPG images and writes the paths to an Excel file
    along with empty columns for additional data.
    """
    # Create a new Excel workbook and select the active worksheet
    wb = Workbook()
    ws = wb.active
    
    # Set the column titles
    columns = ['image_path', 'glocation', 'component', 'defect_line1', 'defect_line2', 'idd','rotation']
    ws.append(columns)
    
    # Scan the directory for JPG files and write the paths to the Excel
    for file in os.listdir(directory):
        if file.lower().endswith('.jpg'):
            ws.append([os.path.join(directory, file)])
    
    # Save the Excel workbook
    wb.save(excel_path)

def process_images_from_excel(excel_path: str,output_folder:str) -> None:
    """
    Reads the Excel file and processes each image using the provided details.
    """
    # Load the Excel file
    df = pd.read_excel(excel_path)

    for index, row in df.iterrows():
        image_path = row['image_path']
        # Assuming get_comments_info is defined elsewhere and available
        cord1, cord2, date_month_year, hour_min_second, angle = get_comments_info(image_path)
        
        # Call the function with the data from the Excel and the extracted information
        create_standardized_overlay_image(image_path,
                                          cord1=cord1,
                                          cord2=cord2,
                                          date_month_year=date_month_year,
                                          hour_min_second=hour_min_second,
                                          angle=angle,
                                          glocation=row['glocation'],
                                          component=row['component'],
                                          defect_line1=row['defect_line1'],
                                          defect_line2=row['defect_line2'],
                                          idd=row['idd'],
                                          output_folder = output_folder)



def process_images_from_excel_with_rotation(excel_path: str,output_folder:str) -> None:
    """
    Reads the Excel file and processes each image using the provided details.
    """
    # Load the Excel file
    df = pd.read_excel(excel_path)

    for index, row in df.iterrows():
        image_path = row['image_path']
        # Assuming get_comments_info is defined elsewhere and available
        if row['rotation'] != 0:
            image_path = copy_and_rotate(image_path,row['rotation'])
            print('path' ,image_path)
            try:
                cord1, cord2, date_month_year, hour_min_second, angle = get_comments_info(image_path)
            except:
                cord1, cord2, date_month_year, hour_min_second, angle = 32.25315, 115.76708, '2024:06:12', '2024:06:12', -75

        # Call the function with the data from the Excel and the extracted information
        create_standardized_overlay_image(image_path,
                                          cord1=cord1,
                                          cord2=cord2,
                                          date_month_year=date_month_year,
                                          hour_min_second=hour_min_second,
                                          angle=angle,
                                          glocation=row['glocation'],
                                          component=row['component'],
                                          defect_line1=row['defect_line1'],
                                          defect_line2=row['defect_line2'],
                                          idd=row['idd'],
                                          output_folder = output_folder)

# Example usage
if __name__ == '__main__':
    directory = r"test" 
    excel_path = r"data\defects.xlsx"
    scan_and_write_excel(directory, excel_path)
    process_images_from_excel_with_rotation(excel_path,output_folder=r"results")
