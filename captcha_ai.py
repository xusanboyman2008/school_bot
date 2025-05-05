import cv2
import pytesseract
from PIL import Image
import numpy as np
import re

def preprocess_image(image_path='captcha_debug.png'):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    denoised = cv2.medianBlur(thresh, 3)
    return denoised

def extract_numbers_from_clean_image(image_path):
    processed = preprocess_image(image_path)

    # Save to temp file to read with PIL for pytesseract
    temp_path = "temp_clean.png"
    cv2.imwrite(temp_path, processed)

    text = pytesseract.image_to_string(Image.open(temp_path), config='--psm 7')  # PSM 7 = single line
    numbers = re.findall(r'\d+', text)
    return ''.join(numbers)  # Return as single string
