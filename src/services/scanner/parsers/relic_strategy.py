import numpy as np
from PIL import Image as PILImage
from PIL.Image import Image
from pyautogui import locate

from config.const import EQUIPPED, EQUIPPED_AVATAR, EQUIPPED_AVATAR_OFFSET, LOCK
from config.relic_scan import RELIC_NAV_DATA
from enums.increment_type import IncrementType
from enums.log_level import LogLevel
from models.const import (
    FILTER_MAX,
    FILTER_MIN,
    RELIC_DISCARD,
    RELIC_LEVEL,
    RELIC_LOCATION,
    RELIC_MAINSTAT,
    RELIC_NAME,
    RELIC_RARITY,
    MIN_LEVEL,
    MIN_RARITY,
    RELIC_FILTERS,
    RELIC_SET,
    RELIC_SET_ID,
    RELIC_SLOT,
    RELIC_SUBSTAT_NAME,
    RELIC_SUBSTAT_VALUE,
    RELIC_SUBSTAT_VALUES,
    RELIC_SUBSTATS,
    RELIC_SUBSTAT_NAMES,
    SORT_LV,
    SORT_RARITY,
)
from models.substat_vals import SUBSTAT_ROLL_VALS
from services.scanner.parsers.parse_strategy import BaseParseStrategy
from type_defs.stats_dict import RelicDict
from utils.data import filter_images_from_dict, resource_path
from utils.ocr import (
    image_to_string,
    preprocess_equipped_img,
    preprocess_main_stat_img,
    preprocess_sub_stat_img,
)


class RelicStrategy(BaseParseStrategy):
    """RelicStrategy class for parsing relic data from screenshots."""

    SCAN_TYPE = IncrementType.RELIC_ADD
    NAV_DATA = RELIC_NAV_DATA

    def __init__(self, *args, **kwargs) -> None:
        """Constructor"""
        super().__init__(*args, **kwargs)
        self._discard_icon = PILImage.open(resource_path("assets/images/discard.png"))

    def get_optimal_sort_method(self, filters: dict) -> str:
        """Gets the optimal sort method based on the filters

        :param filters: The filters
        :return: The optimal sort method
        """
        if filters[RELIC_FILTERS][MIN_LEVEL] > 0:
            return SORT_LV
        else:
            return SORT_RARITY

    def check_filters(
        self, stats_dict: RelicDict, filters: dict, uid: int
    ) -> tuple[dict, RelicDict]:
        """Checks if the relic passes the filters

        :param stats_dict: The stats dict
        :param filters: The filters
        :param uid: The relic UID
        :raises ValueError: Thrown if the filter key does not have an int value
        :return: A tuple of the filter results and the stats dict
        """
        filters = filters[RELIC_FILTERS]

        filter_results = {}
        for key in filters:
            filter_type, filter_key = key.split("_")

            val = stats_dict[filter_key] if filter_key in stats_dict else None

            if not val or isinstance(val, Image):
                if key == MIN_RARITY:
                    # Trivial case
                    if filters[key] <= 2:
                        filter_results[key] = True
                        continue
                    val = stats_dict[RELIC_RARITY] = self.extract_stats_data(  # type: ignore
                        filter_key, stats_dict[RELIC_RARITY]
                    )
                elif key == MIN_LEVEL:
                    # Trivial case
                    if filters[key] <= 0:
                        filter_results[key] = True
                        continue
                    level = self.extract_stats_data(
                        RELIC_LEVEL, stats_dict[RELIC_LEVEL]
                    )
                    if not level or isinstance(level, Image):
                        self._log(
                            f"Relic UID {uid}: Failed to parse level. Setting to 0.",
                            LogLevel.ERROR,
                        )
                        stats_dict[RELIC_LEVEL] = 0
                        filter_results[key] = True
                        continue
                    val = stats_dict[RELIC_LEVEL] = int(level)

            if not isinstance(val, int):
                raise ValueError(f"Filter key {key} does not have an int value.")

            if filter_type == FILTER_MIN:
                filter_results[key] = val >= filters[key]
            elif filter_type == FILTER_MAX:
                filter_results[key] = val <= filters[key]

        return (filter_results, stats_dict)

    def extract_stats_data(
        self, key: str, data: str | int | Image
    ) -> str | int | Image:
        """Extracts the stats data from the image

        :param key: The key
        :param data: The data
        :return: The extracted data, or the image if the key is not relevant
        """
        if not isinstance(data, Image):
            return data

        if key == RELIC_NAME:
            return image_to_string(
                data, "ABCDEFGHIJKLMNOPQRSTUVWXYZ 'abcedfghijklmnopqrstuvwxyz-", 6
            )
        elif key == RELIC_LEVEL:
            return image_to_string(data, "0123456789S", 7, True).replace("S", "5")
        elif key == RELIC_MAINSTAT:
            return image_to_string(
                data,
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcedfghijklmnopqrstuvwxyz",
                7,
                True,
                preprocess_main_stat_img,
            )
        elif key == EQUIPPED:
            return image_to_string(data, "Equiped", 7, True, preprocess_equipped_img)
        elif key == RELIC_RARITY:
            # Get rarity by color matching
            rarity_sample = np.array(data)
            rarity_sample = rarity_sample[int(rarity_sample.shape[0] / 2)][
                int(rarity_sample.shape[1] / 2)
            ]
            return self._game_data.get_closest_rarity(rarity_sample)
        elif key == RELIC_SUBSTAT_NAMES:
            return image_to_string(
                data,
                " ABCDEFGHIKMPRSTacefikrt",
                6,
                True,
                preprocess_sub_stat_img,
                False,
            )
        elif key == RELIC_SUBSTAT_VALUES:
            return (
                image_to_string(
                    data, "0123456789S.%,", 6, True, preprocess_sub_stat_img, False
                )
                .replace("S", "5")
                .replace(",", ".")
                .replace("..", ".")
            )
        else:
            return data

    def parse(self, stats_dict: RelicDict, uid: int) -> dict:
        """Parses the relic data

        :param stats_dict: The stats dict
        :param uid: The relic UID
        :return: The parsed relic data
        """
        if self._interrupt_event.is_set():
            return {}

        try:
            for key in stats_dict:
                stats_dict[key] = self.extract_stats_data(key, stats_dict[key])

            (
                self._log(
                    f"Relic UID {uid}: Raw data: {filter_images_from_dict(stats_dict)}",
                    LogLevel.DEBUG,
                )
                if self._debug
                else None
            )

            name = stats_dict[RELIC_NAME]
            level = stats_dict[RELIC_LEVEL]
            main_stat_key = stats_dict[RELIC_MAINSTAT]
            lock = stats_dict[LOCK]
            discard = stats_dict[RELIC_DISCARD]
            rarity = stats_dict[RELIC_RARITY]
            equipped = stats_dict[EQUIPPED]
            substat_names = stats_dict[RELIC_SUBSTAT_NAMES]
            substat_vals = stats_dict[RELIC_SUBSTAT_VALUES]

            # Fix OCR errors
            name, _ = self._game_data.get_closest_relic_name(name)  # type: ignore
            main_stat_key, _ = self._game_data.get_closest_relic_main_stat(main_stat_key)  # type: ignore
            if not level or isinstance(level, Image):
                self._log(
                    f"Relic UID {uid}: Failed to extract level. Setting to 0.",
                    LogLevel.ERROR,
                )
                level = 0
            level = int(level)
            if not name:
                self._log(
                    f'Relic UID {uid}: Failed to extract name. Setting to "Musketeer\'s Wild Wheat Felt Hat".',
                    LogLevel.ERROR,
                )
                name = "Musketeer's Wild Wheat Felt Hat"

            # Substats
            while "\n\n" in substat_names:  # type: ignore
                substat_names = substat_names.replace("\n\n", "\n")  # type: ignore
            while "\n\n" in substat_vals:  # type: ignore
                substat_vals = substat_vals.replace("\n\n", "\n")  # type: ignore
            substat_names = substat_names.split("\n")  # type: ignore
            substat_vals = substat_vals.split("\n")  # type: ignore

            substats_res = self._parse_substats(substat_names, substat_vals, uid)
            self._validate_substats(substats_res, rarity, level, uid)  # type: ignore
            self._sort_substats(substats_res, uid)

            # Set and slot
            metadata = self._game_data.get_relic_meta_data(name)
            set_id = str(metadata[RELIC_SET_ID])
            set_name = metadata[RELIC_SET]
            slot_key = metadata[RELIC_SLOT]
            if slot_key == "Hands":
                main_stat_key = "ATK"
            elif slot_key == "Head":
                main_stat_key = "HP"
            elif not main_stat_key:
                self._log(
                    f"Relic UID {uid}: Failed to extract main stat. Setting to ATK.",
                    LogLevel.ERROR,
                )
                main_stat_key = "ATK"

            # Check if locked/discarded by image matching
            min_dim = min(lock.size)
            try:
                lock_img = self._lock_icon.resize((min_dim, min_dim))
                lock = locate(lock_img, lock, confidence=0.3) is not None
            except Exception:  # https://github.com/kel-z/HSR-Scanner/issues/41
                self._log(
                    f"Relic UID {uid}: Failed to parse lock. Setting to False.",
                    LogLevel.ERROR,
                )
                lock = False
            min_dim = min(discard.size)
            try:
                discard_img = self._discard_icon.resize((min_dim, min_dim))
                discard = locate(discard_img, discard, confidence=0.3) is not None
            except Exception:
                self._log(
                    f"Relic UID {uid}: Failed to parse discard. Setting to False.",
                    LogLevel.ERROR,
                )
                discard = False

            location = ""
            outfit_id = None
            if equipped == "Equipped":
                equipped_avatar = stats_dict[EQUIPPED_AVATAR]
                location, outfit_id = self._game_data.get_equipped_character(
                    equipped_avatar
                )
            elif (
                equipped == "Equippe"
            ):  # https://github.com/kel-z/HSR-Scanner/issues/88
                equipped_avatar = stats_dict[EQUIPPED_AVATAR_OFFSET]
                location, outfit_id = self._game_data.get_equipped_character(
                    equipped_avatar
                )

            if outfit_id:
                self._log(
                    f"Relic UID {uid}: Equipped character is {location} with outfit ID {outfit_id}.",
                    LogLevel.DEBUG,
                )

            result = {
                RELIC_SET_ID: set_id,
                RELIC_NAME: set_name,
                RELIC_SLOT: slot_key,
                RELIC_RARITY: rarity,
                RELIC_LEVEL: level,
                RELIC_MAINSTAT: main_stat_key,
                RELIC_SUBSTATS: substats_res,
                RELIC_LOCATION: location,
                LOCK: lock,
                RELIC_DISCARD: discard,
                "_uid": f"relic_{uid}",
            }

            self._update_signal.emit(IncrementType.RELIC_SUCCESS.value)

            return result
        except Exception as e:
            self._log(
                f"Failed to parse relic {uid}. stats_dict={stats_dict}, exception={e}",
                LogLevel.ERROR,
            )
            return {}

    def _parse_substats(
        self, names: list[str], vals: list[str], uid: int
    ) -> list[dict[str, int | float]]:
        """Parses the substats

        :param names: The substat names
        :param vals: The substat values
        :param uid: The relic UID
        :return: The parsed substats
        """
        self._log(
            f"Relic UID {uid}: Parsing substats. Substats: {names}, Values: {vals}",
            LogLevel.TRACE,
        )

        substats = []
        for i in range(len(names)):
            name = names[i]
            if not name:
                break

            name, dist = self._game_data.get_closest_relic_sub_stat(name)
            if dist > 3:
                self._log(
                    f"Relic UID {uid}: Substat {name} has a distance of {dist} from {names[i]}. Ignoring rest of substats.",
                    LogLevel.DEBUG,
                )
                break

            if i >= len(vals):
                self._log(
                    f"Relic UID {uid}: Failed to get value for substat: {name}.",
                    LogLevel.ERROR,
                )
                break
            val = vals[i]

            try:
                if "%" in val:
                    val = float(val[: val.index("%")])
                    name += "_"
                else:
                    val = int(val)
            except ValueError:
                if dist == 0:
                    self._log(
                        f"Relic UID {uid}: Failed to get value for substat: {name}. Error parsing substat value: {val}.",
                        LogLevel.ERROR,
                    )
                continue

            substats.append({"key": name, "value": val})

        return substats

    def _validate_substat(self, substat: dict[str, int | float], rarity: int) -> bool:
        """Validates the substat

        :param substat: The substat
        :param rarity: The rarity of the relic
        :return: True if the substat is valid, False otherwise
        """
        try:
            name = substat[RELIC_SUBSTAT_NAME]
            val = substat[RELIC_SUBSTAT_VALUE]
            if name not in SUBSTAT_ROLL_VALS[str(rarity)]:
                return False
            if str(val) not in SUBSTAT_ROLL_VALS[str(rarity)][name]:
                return False
        except KeyError:
            return False

        return True

    def _validate_substats(
        self,
        substats: list[dict[str, int | float]],
        rarity: int,
        level: int,
        uid: int,
    ) -> None:
        """Rudimentary substat validation on number of substats based on rarity and level

        :param substats: The substats
        :param rarity: The rarity of the relic
        :param level: The level of the relic
        :param uid: The relic UID
        """
        seen_substats = set()

        # check valid number of substats
        substats_len = len(substats)
        min_substats = min(rarity - 2 + int(level / 3), 4)
        if substats_len < min_substats:
            self._log(
                f"Relic UID {uid} has {substats_len} substat(s), but the minimum for rarity {rarity} and level {level} is {min_substats}.",
                LogLevel.ERROR,
            )
            return

        # check valid roll value total
        min_roll_value = round(min_substats * 0.8, 1)
        max_roll_value = round(rarity - 1 + int(level / 3), 1)
        total = 0
        for substat in substats:
            if substat[RELIC_SUBSTAT_NAME] in seen_substats:
                self._log(
                    f"Relic UID {uid}: More than one substat with key {substat[RELIC_SUBSTAT_NAME]} parsed.",
                    LogLevel.ERROR,
                )
                return
            if not self._validate_substat(substat, rarity):
                self._log(
                    f'Relic UID {uid}: Substat {substat[RELIC_SUBSTAT_NAME]} has illegal value "{substat[RELIC_SUBSTAT_VALUE]}" for rarity {rarity}.',
                    LogLevel.ERROR,
                )
                return

            roll_value = SUBSTAT_ROLL_VALS[str(rarity)][
                str(substat[RELIC_SUBSTAT_NAME])
            ][str(substat[RELIC_SUBSTAT_VALUE])]
            if isinstance(roll_value, list):
                # assume minimum
                roll_value = roll_value[0]
            total += roll_value

        total = round(total, 1)
        if total < min_roll_value:
            self._log(
                f"Relic UID {uid} has a roll value of {total}, but the minimum for rarity {rarity} and level {level} is {min_roll_value}.",
                LogLevel.ERROR,
            )
        elif total > max_roll_value:
            self._log(
                f"Relic UID {uid} has a roll value of {total}, but the maximum for rarity {rarity} and level {level} is {max_roll_value}.",
                LogLevel.ERROR,
            )

    def _sort_substats(self, substats: list[dict[str, int | float]], uid: int) -> None:
        """Sorts the substats

        :param substats: The substats
        :param uid: The relic UID
        """
        SORT_ORDER = [
            "HP",
            "ATK",
            "DEF",
            "HP_",
            "ATK_",
            "DEF_",
            "SPD",
            "CRIT Rate_",
            "CRIT DMG_",
            "Effect Hit Rate_",
            "Effect RES_",
            "Break Effect_",
        ]
        original = substats.copy()
        substats.sort(key=lambda x: SORT_ORDER.index(str(x[RELIC_SUBSTAT_NAME])))
        if original != substats:
            self._log(
                f"Relic UID {uid}: Newly upgraded relic detected. Substats have been sorted.",
            )

    def _log(self, msg: str, level: LogLevel = LogLevel.INFO) -> None:
        """Logs a message

        :param msg: The message to log
        :param level: The log level
        """
        if self._debug or level in [LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR]:
            self._log_signal.emit((msg, level))
