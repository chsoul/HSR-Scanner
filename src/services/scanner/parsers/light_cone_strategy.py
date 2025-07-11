from config.const import EQUIPPED, EQUIPPED_AVATAR, EQUIPPED_AVATAR_OFFSET, LOCK
from models.const import (
    LC_ASCENSION,
    LC_FILTERS,
    LC_ID,
    LC_LEVEL,
    LC_LOCATION,
    LC_LOCK,
    LC_NAME,
    LC_LEVEL,
    LC_RARITY,
    LC_SUPERIMPOSITION,
    MIN_LEVEL,
    MIN_RARITY,
    SORT_LV,
    SORT_RARITY,
)
from type_defs.stats_dict import LightConeDict

from PIL.Image import Image
from pyautogui import locate

from config.light_cone_scan import LIGHT_CONE_NAV_DATA
from enums.increment_type import IncrementType
from enums.log_level import LogLevel
from services.scanner.parsers.parse_strategy import BaseParseStrategy
from utils.data import filter_images_from_dict
from utils.ocr import (
    image_to_string,
    preprocess_equipped_img,
    preprocess_lc_level_img,
    preprocess_superimposition_img,
)


class LightConeStrategy(BaseParseStrategy):
    """LightConeStrategy class for parsing light cone data from screenshots."""

    SCAN_TYPE = IncrementType.LIGHT_CONE_ADD
    NAV_DATA = LIGHT_CONE_NAV_DATA

    def get_optimal_sort_method(self, filters: dict) -> str:
        """Gets the optimal sort method based on the filters

        :param filters: The filters
        :return: The optimal sort method
        """
        if filters[LC_FILTERS][MIN_LEVEL] > 1:
            return SORT_LV
        else:
            return SORT_RARITY

    def check_filters(
        self, stats_dict: LightConeDict, filters: dict, uid: int
    ) -> tuple[dict, LightConeDict]:
        """Check if the stats dictionary passes the filters

        :param stats_dict: The stats dictionary
        :param filters: The filters
        :param uid: The UID of the light cone
        :raises ValueError: Thrown if the filter key does not have an int value
        :raises KeyError: Thrown if the filter key is not valid
        :return: The filter results and the stats dictionary
        """
        filters = filters[LC_FILTERS]

        filter_results = {}
        for key in filters:
            filter_type, filter_key = key.split("_")

            val = stats_dict[filter_key] if filter_key in stats_dict else None

            if not val or isinstance(val, Image):
                if key == MIN_RARITY:
                    # Trivial case
                    if filters[key] <= 3:
                        filter_results[key] = True
                        continue
                    stats_dict[LC_NAME] = self.extract_stats_data(
                        LC_NAME, stats_dict[LC_NAME]
                    )
                    lc_name = stats_dict[LC_NAME]
                    if not lc_name or not isinstance(lc_name, str):
                        self._log(
                            f'Light Cone UID {uid}: Failed to parse name. Setting to "Void".',
                            LogLevel.ERROR,
                        )
                        stats_dict[LC_NAME] = "Void"
                        filter_results[key] = True
                        continue
                    stats_dict[LC_NAME], _ = (
                        self._game_data.get_closest_light_cone_name(lc_name)
                    )
                    val = self._game_data.get_light_cone_meta_data(lc_name)[LC_RARITY]
                    stats_dict[LC_RARITY] = val
                elif key == MIN_LEVEL:
                    # Trivial case
                    if filters[key] <= 1:
                        filter_results[key] = True
                        continue
                    stats_dict[LC_LEVEL] = self.extract_stats_data(
                        LC_LEVEL, stats_dict[LC_LEVEL]
                    )
                    if not stats_dict[LC_LEVEL]:
                        self._log(
                            f"Light Cone UID {uid}: Failed to parse level. Setting to 1.",
                            LogLevel.ERROR,
                        )
                        stats_dict[LC_LEVEL] = "1/20"
                        filter_results[key] = True
                        continue
                    val = int(stats_dict[LC_LEVEL].split("/")[0])  # type: ignore

            if not isinstance(val, int):
                raise ValueError(f'Filter key "{key}" does not have an int value.')

            if filter_type == "min":
                filter_results[key] = val >= filters[key]
            elif filter_type == "max":
                filter_results[key] = val <= filters[key]
            else:
                raise KeyError(f'"{key}" is not a valid filter.')

        return (filter_results, stats_dict)

    def extract_stats_data(self, key: str, data: str | Image) -> str | Image:
        """Extracts the stats data from the image

        :param key: The key
        :param data: The data
        :return: The extracted data, or the image if the key is not recognized
        """
        if not isinstance(data, Image):
            return data

        if key == LC_NAME:
            name, _ = self._game_data.get_closest_light_cone_name(
                image_to_string(
                    data,
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZ 'abcedfghijklmnopqrstuvwxyz-",
                    6,
                )
            )
            return name
        elif key == LC_LEVEL:
            return image_to_string(
                data, "0123456789S/", 7, True, preprocess_lc_level_img
            ).replace("S", "5")
        elif key == LC_SUPERIMPOSITION:
            return image_to_string(
                data, "12345S", 10, True, preprocess_superimposition_img
            ).replace("S", "5")
        elif key == EQUIPPED:
            return image_to_string(data, "Equipped", 7, True, preprocess_equipped_img)
        else:
            return data

    def parse(self, stats_dict: dict, uid: int) -> dict:
        """Parses the stats dictionary

        :param stats_dict: The stats dictionary
        :param uid: The UID of the light cone
        :return: The parsed stats dictionary
        """
        if self._interrupt_event.is_set():
            return {}

        try:
            for key in stats_dict:
                stats_dict[key] = self.extract_stats_data(key, stats_dict[key])

            (
                self._log(
                    f"Light Cone UID {uid}: Raw data: {filter_images_from_dict(stats_dict)}",
                    LogLevel.DEBUG,
                )
                if self._debug
                else None
            )

            name = stats_dict[LC_NAME]
            level = stats_dict[LC_LEVEL]
            superimposition = stats_dict[LC_SUPERIMPOSITION]
            lock = stats_dict[LOCK]
            equipped_text = stats_dict[EQUIPPED]

            if not name:
                self._log(
                    f'Light Cone UID {uid}: Failed to parse name. Setting to "Void".',
                    LogLevel.ERROR,
                )
                name = "Void"

            lc_id = str(self._game_data.get_light_cone_meta_data(name)[LC_ID])

            # Parse level, ascension, superimposition
            try:
                level, max_level = level.split("/")
                level = int(level)
                max_level = int(max_level)
            except ValueError:
                self._log(
                    f"Light Cone UID {uid}: Failed to parse level. Setting to 1.",
                    LogLevel.ERROR,
                )
                level = 1
                max_level = 20

            ascension = (max(max_level, 20) - 20) // 10

            try:
                superimposition = int(superimposition)
            except ValueError:
                self._log(
                    f"Light Cone UID {uid}: Failed to parse superimposition. Setting to 1.",
                    LogLevel.ERROR,
                )
                superimposition = 1

            min_dim = min(lock.size)
            try:
                locked = self._lock_icon.resize((min_dim, min_dim))

                # Check if locked by image matching
                lock = locate(locked, lock, confidence=0.1) is not None
            except Exception:  # https://github.com/kel-z/HSR-Scanner/issues/41
                self._log(
                    f"Light Cone UID {uid}: Failed to parse lock. Setting to False.",
                    LogLevel.ERROR,
                )
                lock = False

            location = ""
            outfit_id = None
            if equipped_text == "Equipped":
                equipped_avatar = stats_dict[EQUIPPED_AVATAR]
                location, outfit_id = self._game_data.get_equipped_character(
                    equipped_avatar
                )
            elif (
                equipped_text == "Equippe"
            ):  # https://github.com/kel-z/HSR-Scanner/issues/88
                equipped_avatar = stats_dict[EQUIPPED_AVATAR_OFFSET]
                location, outfit_id = self._game_data.get_equipped_character(
                    equipped_avatar
                )

            if outfit_id:
                self._log(
                    f"Light Cone UID {uid}: Equipped character is {location} with outfit ID {outfit_id}.",
                    LogLevel.DEBUG,
                )

            result = {
                LC_ID: lc_id,
                LC_NAME: name,
                LC_LEVEL: int(level),
                LC_ASCENSION: int(ascension),
                LC_SUPERIMPOSITION: int(superimposition),
                LC_LOCATION: location,
                LC_LOCK: lock,
                "_uid": f"light_cone_{uid}",
            }

            self._update_signal.emit(IncrementType.LIGHT_CONE_SUCCESS.value)

            return result
        except Exception as e:
            self._log(
                f"Failed to parse light cone {uid}. stats_dict={stats_dict}, exception={e}",
                LogLevel.ERROR,
            )
            return {}

    def _log(self, msg: str, level: LogLevel = LogLevel.INFO) -> None:
        """Logs a message

        :param msg: The message to log
        :param level: The log level
        """
        if self._debug or level in [LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR]:
            self._log_signal.emit((msg, level))
