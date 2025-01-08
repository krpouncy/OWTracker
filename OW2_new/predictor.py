# The best OW2_new model created
import pickle
import re

import cv2
import joblib
import numpy as np
import pytesseract
from torch.ao.nn.quantized.functional import threshold

from models import PredictorInterface
from models.OW2_new.image_parser import ImageParser
from models.OW2_new.image_utils import generate_sub_images

from models.OW2_new.custom_transformers import *

import pandas as pd

# create global variable for custom image parser
classifier = ImageParser(model_path="models/OW2_new/latest_model.pth")

class UserPredictor(PredictorInterface):
    def __init__(self):
        self.loaded_pipeline = joblib.load('models/OW2_new/prediction_pipeline.pkl')

    def predict_probability(self, stats, game_details):
        time_in_minutes, team_composition = game_details

        # return nothing if the there are 5 or more players missing
        if not stats or len(stats) < 5 or time_in_minutes is None:
            print(len(stats), stats)
            return None

        if time_in_minutes < 1.0:
            time_in_minutes = 1

        # convert the stats into a dataframe with each row representing a playerID and a new column with SnapID = 0 for entire column
        df = pd.DataFrame(stats, columns=['K', 'A', 'D', 'Damage', 'H', 'MIT'])
        df["Time"] = time_in_minutes
        df["SnapID"] = 0
        df["PlayerID"] = np.arange(0, 10)

        print(df)

        winning_chances = self.loaded_pipeline.predict_proba(df)[0][1]
        threshold = 0.5
        sensitivity = 0.6925
        specificity = 0.6923

        lr_positive = sensitivity / (1 - specificity)
        lr_negative = (1 - sensitivity) / specificity

        odds_prior = winning_chances / (1 - min(winning_chances, 0.9999))
        if winning_chances > threshold:
            odds_posterior = odds_prior * lr_positive
        else:
            odds_posterior = odds_prior * lr_negative

        posterior_prob = odds_posterior / (1 + odds_posterior)

        return posterior_prob

    def get_stats_and_details(self, filename):
        """
        Extract the stats and details from the given image.
        :param filename: The filename of the image.
        :return: A tuple of stats and game details. None if the image could not be read or the dimensions are too small.
        """
        image = cv2.imread(filename)
        if image is None:
            print(f"Error reading image: {filename}")
            return None

        if image.shape[0] < 100 or image.shape[1] < 750:
            print(f"Image dimensions are too small: {image.shape}")
            return None

        header_image = image[:100, 120:750]
        custom_config = r'--oem 3 --psm 6'
        header_text = pytesseract.image_to_string(header_image, config=custom_config)
        details = [line.strip() for line in header_text.split('\n') if line.strip()]

        time_in_minutes = None
        for detail in details:
            if 'TIME:' in detail:
                time_str = detail.split('TIME:')[-1].strip()
                match = re.match(r"(?:(\d+):)?(\d+)(?:\.(\d+))?", time_str)
                if match:
                    minutes = int(match.group(1)) if match.group(1) else 0
                    seconds = int(match.group(2))
                    time_in_minutes = minutes + seconds / 60.0
                else:
                    try:
                        time_in_minutes = float(time_str)
                    except ValueError:
                        print(f"Could not parse time: {time_str}")
                        time_in_minutes = None
                break

        sub_images = generate_sub_images(filename)

        # crop and parse character images
        character_images = [si[:, :91] for si in sub_images]
        team_composition, _ = classifier.classify_images(character_images,
                                                         skip_enemy=True)  # TODO process images in batch

        # crop and parse stat images
        stat_images = [si[:, 91:] for si in sub_images]
        stats = classifier.extract_text_from_stats(stat_images)
        stats = convert_stats_to_int(stats)  # convert stats to integers

        return stats, (time_in_minutes, team_composition)

def calculate_team_statuses(stats):
    """Calculate the status of the tank, dps, and support roles based on the given stats.

    :param stats: A list of 5 lists (representing players on Team) with each containing 6 numeric values for K, A, D, Dmg, H, and MIT.
    :return: A tuple of strings representing the status of the tank, dps, and support roles.
    """

    # initialize the status of each role
    tank_status, dps_status, support_status = 'not enough data', 'not enough data', 'not enough data'

    # calculate the tank, dps, and support status
    tank_k, tank_mit = stats[0][0], stats[0][5]
    if tank_k != 0 and tank_mit != 0:
        tank_ratio = tank_k / (tank_k + tank_mit**0.5)
        if tank_ratio <= 0.05:
            tank_status = 'poor'
        elif 0.04 < tank_ratio < 0.08:
            tank_status = 'average'
        else:
            tank_status = 'good'

    dps_damage = stats[1][3] + stats[2][3]
    enemy_dps_damage = stats[6][3] + stats[7][3]
    if dps_damage != 0 and enemy_dps_damage != 0:
        if abs(dps_damage - enemy_dps_damage) < 274:
            dps_status = 'average'
        elif dps_damage - enemy_dps_damage >= 274:
            dps_status = 'good'
        else:
            dps_status = 'poor'

    damage = stats[3][3] + stats[4][3]
    healing = stats[3][4] + stats[4][4]
    if damage != 0 and healing != 0:
        if damage + healing > 0:
            damage_ratio = damage / (damage + healing)
        else:
            damage_ratio = 0.0

        print(f"Damage Ratio: {damage_ratio:.2f}. Feedback: ", end="")

        if damage_ratio < 0.14:
            print("SHOOT!")
            support_status = 'poor'
        elif 0.185 <= damage_ratio <= 0.32:
            print("You're doing good.")
            support_status = 'average'
        else:
            support_status = 'good'

    print("Custom Team Status:", (tank_status, dps_status, support_status))

    return tank_status, dps_status, support_status

def convert_stats_to_int(stats):
    for i in range(len(stats)):
        for j in range(len(stats[i])):
            if stats[i][j] == '':
                stats[i][j] = 0
            else:
                stats[i][j] = int(stats[i][j])

    return stats