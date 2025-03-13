import cv2
import numpy as np
import os

# Load the image
image = cv2.imread("/home/jarred/Downloads/round-yellow-emoticon-set-isolated-beige-background/v767-wan-07.jpg")

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply thresholding to separate emojis from the background
_, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

# Find contours (each emoji should be a separate contour)
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Create an output folder
output_folder = "/home/jarred/Downloads/"
os.makedirs(output_folder, exist_ok=True)

# Loop through contours and save each emoji
for i, contour in enumerate(contours):
    x, y, w, h = cv2.boundingRect(contour)
    emoji = image[y:y+h, x:x+w]  # Crop emoji from original image
    cv2.imwrite(f"{output_folder}/emoji_{i}.png", emoji)  # Save as PNG

print(f"Extracted {len(contours)} emojis and saved them in {output_folder}/")
