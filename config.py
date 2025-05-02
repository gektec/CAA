# config.py
import os

# ADB 工具路径，默认使用环境变量中的 adb
ADB_PATH = 'adb'

# 定义左下角截取的三个区域，格式为 (x, y, width, height)
LEFT_BOTTOM_REGIONS = [
    (474, 910, 112, 112),
    (594, 910, 112, 112),
    (714, 910, 112, 112),
]

LEFT_BOTTOM_NUMS = [
    (562, 1000, 40, 30),
    (682, 1000, 40, 30),
    (802, 1000, 40, 30),
]


# 定义右下角截取的三个区域
RIGHT_BOTTOM_REGIONS = [
    (1093, 910, 112, 112),
    (1213, 910, 112, 112),
    (1333, 910, 112, 112),
]

RIGHT_BOTTOM_NUMS = [
    (1090, 1000, 40, 30),
    (1210, 1000, 40, 30),
    (1330, 1000, 40, 30),
]

MAP_REGION = (720, 250, 480, 160)

#定义模式判断区域
MODE_REGION = (0, 0, 300, 100)


# 点击后或循环等待时间（秒）
WAIT_TIME = 1 

DATA_DIR = 'results.csv'

FULL_SCREENSHOT_PATH = 'captures/screenshot.png'

TEMP_PATH = 'temp/'

BACKUP_PATH = 'backup/'

CARD_PATTERN_DIR = 'patterns/slots'

MODE_PATTERN_DIR='patterns/mods'

MAP_PATTERN_DIR='patterns/maps'

DIGIT_PATTERN_DIR = 'patterns/digits'

CARD_OUTPUT_DIR = 'captures/slots'