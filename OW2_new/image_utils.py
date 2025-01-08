import os

import cv2
import numpy as np


def split_image(image):
    """Split the image into two halves (top and bottom)"""
    height, width = image.shape
    top_half = image[:height // 2, :]
    bottom_half = image[height // 2:, :]
    return top_half, bottom_half

def crop_image(image):
    """Crop the image using template matching."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "search_stats.png")

    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(result)
    template_height, template_width = template.shape[:2]
    top_left = max_loc
    bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
    output_image = image[top_left[1]:bottom_right[1], top_left[0]:]
    output_image = output_image[:, :850]
    return output_image

def prepare_sub_images(image):
    """Split the image into 10 sub-images.

    :param image: The input image (grayscale or color) as a NumPy array.
    :return: A list of 10 sub-images.
    """
    # Split the image into top and bottom halves
    top, bottom = split_image(image)

    # Crop the halves if necessary
    top = crop_image(top)
    bottom = crop_image(bottom)

    # Further split the top and bottom halves into 5 sub-images each
    sub_images = []
    height_top = top.shape[0]
    height_bottom = bottom.shape[0]
    width = top.shape[1]

    for i in range(5):
        sub_image_top = top[i * height_top // 5:(i + 1) * height_top // 5, :width]
        sub_images.append(sub_image_top)

    for i in range(5):
        sub_image_bottom = bottom[i * height_bottom // 5:(i + 1) * height_bottom // 5, :width]
        sub_images.append(sub_image_bottom)

    return sub_images

def adjust_gamma(image, gamma=1.0):
    """Apply gamma correction to an image."""
    inv_gamma = 1.0 / gamma
    table = np.array([(i / 255.0) ** inv_gamma * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def process_image(image):
    """Process the image by adjusting gamma and modifying specific regions."""
    new_img = adjust_gamma(image.copy(), gamma=0.45)
    new_img[0:100, :] = image[0:100, :]
    new_img[0:100, :] = np.where(new_img[0:100, :] <= 100, 0, 255)
    new_img[100:, :][new_img[100:, :] <= 110] = 0
    crop_height, crop_width = image.shape[:2]
    if 925 <= crop_height and 405 <= crop_width:
        crop_img = image[190:925, 340:405]
        new_img[190:925, 340:405] = crop_img
    return new_img

def generate_sub_images(image_path):
    """Load an image from the given path and generate 10 sub-images.

    :param image_path: Path to the input image.
    :return: List of 10 sub-images as NumPy arrays.
    """
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Unable to load image at path: {image_path}")

    # Convert to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Process the image
    processed_image = process_image(gray_image)

    # Generate sub-images
    sub_images = prepare_sub_images(processed_image)
    return sub_images