import base64
from functools import cached_property
from io import BytesIO

import cv2
import Levenshtein
import numpy as np
import requests
from PIL import Image as PILImage
from PIL.Image import Image
from PyQt6.QtCore import QSettings

GAME_DATA_URL = "https://raw.githubusercontent.com/kel-z/HSR-Data/v4/output/min/game_data_with_icons.json"
SRO_MAPPINGS_URL = (
    "https://raw.githubusercontent.com/kel-z/HSR-Data/v4/output/min/sro_key_map.json"
)

RELIC_MAIN_STATS = {
    "SPD",
    "HP",
    "ATK",
    "DEF",
    "Break Effect",
    "Effect Hit Rate",
    "Energy Regeneration Rate",
    "Outgoing Healing Boost",
    "Physical DMG Boost",
    "Fire DMG Boost",
    "Ice DMG Boost",
    "Wind DMG Boost",
    "Lightning DMG Boost",
    "Quantum DMG Boost",
    "Imaginary DMG Boost",
    "CRIT Rate",
    "CRIT DMG",
}

RELIC_SUB_STATS = {
    "SPD",
    "ATK",
    "DEF",
    "HP",
    "Effect Hit Rate",
    "Effect RES",
    "CRIT Rate",
    "CRIT DMG",
    "Break Effect",
}

PATHS = {
    "The Hunt",
    "Erudition",
    "Harmony",
    "Preservation",
    "Destruction",
    "Nihility",
    "Abundance",
}


class GameData:
    """GameData class for storing and accessing game data"""

    sro_mappings = None

    def __init__(self) -> None:
        try:
            response = requests.get(GAME_DATA_URL)
            data = response.json()
        except requests.exceptions.RequestException:
            raise Exception("Failed to fetch game data from " + GAME_DATA_URL)

        self.settings = QSettings("kel-z", "HSR-Scanner")

        self.version = data["version"]
        self.RELIC_META_DATA = data["relics"]
        self.LIGHT_CONE_META_DATA = data["light_cones"]
        self.CHARACTER_META_DATA = data["characters"]
        self.EQUIPPED_ICONS = {}

        # where i + 1 is the rarity
        self.COLOURS = np.array(
            [
                [94, 97, 111],  # gray
                [74, 100, 121],  # green
                [61, 90, 145],  # blue
                [101, 92, 142],  # purple
                [158, 109, 95],  # gold
            ]
        )

        for key in data["mini_icons"]:
            base64_string = data["mini_icons"][key]
            decoded_image = base64.b64decode(base64_string)
            img = PILImage.open(BytesIO(decoded_image))
            img = np.array(img)
            img = cv2.GaussianBlur(img, (5, 5), 0)
            self.EQUIPPED_ICONS[key] = img

    def get_sro_mappings(self) -> dict:
        """Get SRO mappings

        :return: The SRO mappings
        """
        if self.sro_mappings is None:
            try:
                response = requests.get(SRO_MAPPINGS_URL)
                self.sro_mappings = response.json()
            except requests.exceptions.RequestException:
                raise Exception("Failed to fetch SRO mappings from " + SRO_MAPPINGS_URL)

        return self.sro_mappings

    def get_relic_meta_data(self, name: str) -> dict:
        """Get relic meta data from name

        :param name: The name of the relic
        :return: The relic meta data
        """
        return self.RELIC_META_DATA[name]

    def get_light_cone_meta_data(self, name: str) -> dict:
        """Get light cone meta data from name

        :param name: The name of the light cone
        :return: The light cone meta data
        """
        return self.LIGHT_CONE_META_DATA[name]

    def get_character_meta_data(self, name: str) -> dict:
        """Get character meta data from name

        :param name: The name of the character
        :return: The character meta data
        """
        return self.CHARACTER_META_DATA[name]

    def get_equipped_character(self, equipped_avatar_img: Image) -> str:
        """Get equipped character from equipped avatar image

        Side effect: Sets the is_stelle QSetting

        :param equipped_avatar_img: The equipped avatar image
        :return: The character name
        """
        equipped_avatar_img = np.array(equipped_avatar_img)
        equipped_avatar_img = cv2.resize(equipped_avatar_img, (100, 100))

        # Circle mask
        mask = np.zeros(equipped_avatar_img.shape[:2], dtype="uint8")
        (h, w) = equipped_avatar_img.shape[:2]
        cv2.circle(mask, (int(w / 2), int(h / 2)), 50, 255, -1)
        equipped_avatar_img = cv2.bitwise_and(
            equipped_avatar_img, equipped_avatar_img, mask=mask
        )

        max_conf = 0
        character = ""

        # Get character with highest confidence
        for c in self._get_character_keys:
            # Construct key
            key = "".join(filter(lambda char: char.isalnum() or char == "#", c))

            # Get confidence
            conf = cv2.matchTemplate(
                equipped_avatar_img,
                self.EQUIPPED_ICONS[key],
                cv2.TM_CCOEFF_NORMED,
            ).max()
            if conf > max_conf:
                max_conf = conf
                character = c

        if character.startswith("Trailblazer"):
            self.settings.setValue("is_stelle", character.split("#")[1] == "F")
        return character.split("#")[0]

    def get_closest_relic_name(self, name: str) -> str:
        """Get closest relic name from name

        :param name: The name of the relic
        :return: The closest relic name
        """
        return self._get_closest_match(name, self.RELIC_META_DATA)

    def get_closest_light_cone_name(self, name: str) -> str:
        """Get closest light cone name from name

        :param name: The name of the light cone
        :return: The closest light cone name
        """
        return self._get_closest_match(name, self.LIGHT_CONE_META_DATA)

    def get_closest_relic_sub_stat(self, name: str) -> str:
        """Get closest relic sub stat from name

        :param name: The name of the relic sub stat
        :return: The closest relic sub stat
        """
        return self._get_closest_match(name, RELIC_SUB_STATS)

    def get_closest_relic_main_stat(self, name: str) -> str:
        """Get closest relic main stat from name

        :param name: The name of the relic main stat
        :return: The closest relic main stat
        """
        return self._get_closest_match(name, RELIC_MAIN_STATS)

    def get_closest_character_name(self, name: str) -> str:
        """Get closest character name from name

        :param name: The name of the character
        :return: The closest character name
        """
        return self._get_closest_match(name, self._get_character_keys_no_march_path)

    def get_closest_path_name(self, name: str) -> str:
        """Get closest path name from name

        :param name: The name of the path
        :return: The closest path name
        """
        return self._get_closest_match(name, PATHS)

    def get_closest_rarity(self, pixel: list) -> int:
        """Get closest rarity from pixel

        :param pixel: The pixel to get the rarity from
        :return: The closest rarity
        """
        distances = np.linalg.norm(self.COLOURS - pixel, axis=1)

        return int(np.argmin(distances)) + 1

    def _get_closest_match(
        self, name: str, targets: set[str] | dict[str, dict] | list[str]
    ) -> tuple[str, int]:
        """Get closest match from name

        :param name: The name to get the closest match from
        :param targets: The targets to compare against
        :return: The closest match
        """
        name = name.strip()

        if not name:
            return name, 100

        if name in targets:
            return name, 0

        min_dist = 100
        min_name = ""
        for t in targets:
            to_compare = t
            if "#" in t:
                to_compare = t.split("#")[1]
            dist = Levenshtein.distance(name, to_compare, weights=(1, 1, 2))
            if dist < min_dist:
                min_dist = dist
                min_name = t

        return min_name, min_dist

    @cached_property
    def _get_character_keys(self) -> list:
        """Get character keys

        :return: The character keys
        """
        character_keys = list(self.CHARACTER_META_DATA.keys())
        for path in PATHS:
            path = path.split(" ")[-1]
            if f"Trailblazer{path}" in character_keys:
                character_keys.remove(f"Trailblazer{path}")
                character_keys.append(f"Trailblazer{path}#M")
                character_keys.append(f"Trailblazer{path}#F")

        return character_keys

    @cached_property
    def _get_character_keys_no_march_path(self) -> list:
        """Get character keys without March 7th paths

        (ugly hack for new March 7th path [why hoyoverse...])

        :return: The character keys without March 7th paths
        """
        character_keys = list(self.CHARACTER_META_DATA.keys())
        for path in PATHS:
            path = path.split(" ")[-1]
            if f"March 7th{path}" in character_keys:
                character_keys.remove(f"March 7th{path}")
        character_keys.append("March 7th")

        return character_keys
