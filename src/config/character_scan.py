from config.const import (
    ABUNDANCE,
    ASCENSION_OFFSET_X,
    ASCENSION_START,
    ASPECT_16_9,
    DESTRUCTION,
    DETAILS_BUTTON,
    EIDOLONS_BUTTON,
    ERUDITION,
    HARMONY,
    HUNT,
    NIHILITY,
    PRESERVATION,
    REMEMBRANCE,
    TRACES,
    TRACES_BUTTON,
)
from models.const import (
    ABILITY_1,
    ABILITY_2,
    ABILITY_3,
    STAT_1,
    STAT_10,
    STAT_2,
    STAT_3,
    STAT_4,
    STAT_5,
    STAT_6,
    STAT_7,
    STAT_8,
    STAT_9,
)


CHARACTER_NAV_DATA = {
    ASPECT_16_9: {
        ASCENSION_START: (0.78125, 0.203),
        ASCENSION_OFFSET_X: 0.01328,
        DETAILS_BUTTON: (0.13, 0.143),
        TRACES_BUTTON: (0.13, 0.315),
        EIDOLONS_BUTTON: (0.13, 0.49),
        TRACES: {
            HUNT: {
                ABILITY_1: (0.5020833333333333, 0.6833333333333333),
                ABILITY_2: (0.6635, 0.6879),
                ABILITY_3: (0.5828, 0.3166),
                STAT_1: (0.58958, 0.8185),
                STAT_2: (0.451, 0.599),
                STAT_3: (0.3963, 0.5037),
                STAT_4: (0.7255, 0.6),
                STAT_5: (0.7255, 0.59629),
                STAT_6: (0.7807, 0.5037),
                STAT_7: (0.7239, 0.3805),
                STAT_8: (0.58854, 0.2259),
                STAT_9: (0.49948, 0.25277),
                STAT_10: (0.6786, 0.25277),
            },
            ERUDITION: {
                ABILITY_1: (0.45156, 0.541666),
                ABILITY_2: (0.715625, 0.53889),
                ABILITY_3: (0.5828, 0.22),
                STAT_1: (0.5161, 0.7509),
                STAT_2: (0.3989, 0.5472),
                STAT_3: (0.4156, 0.6555),
                STAT_4: (0.4156, 0.43426),
                STAT_5: (0.7744, 0.54537),
                STAT_6: (0.759375, 0.6555),
                STAT_7: (0.759375, 0.4352),
                STAT_8: (0.4984, 0.25),
                STAT_9: (0.67864, 0.2481),
                STAT_10: (0.6588, 0.74537),
            },
            HARMONY: {
                ABILITY_1: (0.414, 0.56389),
                ABILITY_2: (0.752083, 0.56389),
                ABILITY_3: (0.5838, 0.3315),
                STAT_1: (0.5901, 0.819),
                STAT_2: (0.3828, 0.47685),
                STAT_3: (0.446875, 0.40925),
                STAT_4: (0.509895, 0.79444),
                STAT_5: (0.72656, 0.67685),
                STAT_6: (0.66718, 0.63981),
                STAT_7: (0.67031, 0.79444),
                STAT_8: (0.5911, 0.22685),
                STAT_9: (0.50468, 0.25277),
                STAT_10: (0.67604, 0.2537),
            },
            PRESERVATION: {
                ABILITY_1: (0.497395, 0.8037037),
                ABILITY_2: (0.665625, 0.803703),
                ABILITY_3: (0.5822916, 0.321296296),
                STAT_1: (0.589583, 0.8),
                STAT_2: (0.435416, 0.66296),
                STAT_3: (0.38333, 0.55185),
                STAT_4: (0.45208, 0.44444),
                STAT_5: (0.743229, 0.66481),
                STAT_6: (0.795833, 0.550925),
                STAT_7: (0.727083, 0.4462962),
                STAT_8: (0.589583, 0.229629),
                STAT_9: (0.499479, 0.255555),
                STAT_10: (0.6796875, 0.2537),
            },
            DESTRUCTION: {
                ABILITY_1: (0.4901041666666667, 0.7046296296296296),
                ABILITY_2: (0.6734375, 0.7),
                ABILITY_3: (0.596875, 0.3022222222222222),
                STAT_1: (0.5890625, 0.813889),
                STAT_2: (0.4395833, 0.63425925),
                STAT_3: (0.396875, 0.5366666666666666),
                STAT_4: (0.4375, 0.41851),
                STAT_5: (0.7395833, 0.63796296),
                STAT_6: (0.7921875, 0.5462962962962963),
                STAT_7: (0.741666, 0.42037),
                STAT_8: (0.58958333, 0.229629),
                STAT_9: (0.50052, 0.256481),
                STAT_10: (0.6791666, 0.25555),
            },
            NIHILITY: {
                ABILITY_1: (0.436871875, 0.4256944444),
                ABILITY_2: (0.731640625, 0.4215277),
                ABILITY_3: (0.5859375, 0.22291666),
                STAT_1: (0.590234375, 0.7034722),
                STAT_2: (0.38125, 0.5458333),
                STAT_3: (0.4359375, 0.6569444),
                STAT_4: (0.489453125, 0.76875),
                STAT_5: (0.798828, 0.5465277),
                STAT_6: (0.744921875, 0.6569444),
                STAT_7: (0.691796875, 0.7680555),
                STAT_8: (0.50078125, 0.2527777),
                STAT_9: (0.680859375, 0.25257777),
                STAT_10: (0.590625, 0.80763888),
            },
            ABUNDANCE: {
                ABILITY_1: (0.472265, 0.720138),
                ABILITY_2: (0.694140, 0.71875),
                ABILITY_3: (0.584375, 0.2159723),
                STAT_1: (0.630859, 0.802777),
                STAT_2: (0.749218, 0.616666),
                STAT_3: (0.778515, 0.527777),
                STAT_4: (0.722656, 0.4354166),
                STAT_5: (0.433203125, 0.618055),
                STAT_6: (0.40390625, 0.52708333),
                STAT_7: (0.459765625, 0.43541666),
                STAT_8: (0.67890625, 0.2576388),
                STAT_9: (0.504296875, 0.2583333),
                STAT_10: (0.550390625, 0.80416666),
            },
            REMEMBRANCE: {
                ABILITY_1: (0.7921875, 0.5145833333333333),
                ABILITY_2: (0.604296875, 0.8006944444444445),
                ABILITY_3: (0.526171875, 0.3784722222222222),
                STAT_1: (0.78125, 0.6451388888888889),
                STAT_2: (0.77421875, 0.39166666666666666),
                STAT_3: (0.4109375, 0.5194444444444445),
                STAT_4: (0.43125, 0.64375),
                STAT_5: (0.43203125, 0.39166666666666666),
                STAT_6: (0.534375, 0.7902777777777777),
                STAT_7: (0.675, 0.7916666666666666),
                STAT_8: (0.494921875, 0.27291666666666664),
                STAT_9: (0.563671875, 0.21875),
                STAT_10: (0.64453125, 0.21666666666666667),
            },
        },
    }
}
