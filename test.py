# import requests

# with open("data/user_profile_image/981644603008634920.png", "rb") as file:
#     url = "http://localhost:8080/upload_avatar_decoration_image/"
#     headers = {"api-key": "D832djD10W=QE_3f#fc10934vcFVbnED2$581X)449+1"}
#     files = {"file": file}
#     params = {"user_id": 981644603008634920}

#     r = requests.post(url, headers=headers, params=params, files=files)
#     requests.post
#     print(r.status_code, r.json())


import easyocr
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from pathlib import Path

reader = easyocr.Reader(['en'], gpu=False, recognizer='Transformer', detector='DB')

def gettext_from_image(region_cords, image):
    cropped = image.crop(region_cords)
    cropped = cropped.convert('L')
    cropped = cropped.filter(ImageFilter.MedianFilter()) 
    cropped = cropped.resize((cropped.width*2, cropped.height*2)) 
    cropped_np = np.array(cropped)
    result = reader.readtext(cropped_np, detail=0) 
    return ' '.join(result)

name_region = (50, 60, 230, 105)
series_region = (50, 310, 230, 360)

offset = 279

def get_info_from_card(image_path):
    for i in range(3):
        image = Image.open(image_path).convert("L")
        image_name_region = (name_region[0] + i*offset, name_region[1], name_region[2] + i*offset, name_region[3])
        image_series_region = (series_region[0] + i*offset, series_region[1], series_region[2] + i*offset, series_region[3])
        name_text = gettext_from_image(image_name_region, image)
        series_text = gettext_from_image(image_series_region, image)
        print(name_text, "|", series_text)


for image in Path("C:/Users/Mix/Downloads/karuta-test").glob("*.png"):
    get_info_from_card(image)

