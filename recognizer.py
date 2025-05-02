import os
from pathlib import Path
from PIL import Image
from typing import List, Optional, Dict
from functools import lru_cache
import cv2
import numpy as np
import re
import logging
from config import CARD_OUTPUT_DIR, DIGIT_PATTERN_DIR, TEMP_PATH, CARD_PATTERN_DIR, BACKUP_PATH
import time
import shutil

BINARYZATION_THRESHOLD = 210

logger = logging.getLogger("my_logger")


def match_pattern(pil_img,
                      pattern_dir,
                      important=1,
                      threshold=0.8):
    """
    在 pil_img 中用 RGB 模板匹配寻找最佳匹配。

    参数：
      pil_img    -- PIL.Image 对象
      pattern_dir-- 模板图片所在目录（.png）
      threshold  -- 匹配阈值，float
      important  -- 整数标志，1 表示“重要”：若 < threshold，则先 logger.critical 再返回 None；
                    0 表示“不重要”：若 < threshold，直接返回 'nomatch'

    返回：
      best_name  -- 匹配度 ≥ threshold 时的模板名（去掉 .png 后缀）
    """
    # 1. 转成 numpy 数组并保留 RGB 三通道
    img = np.array(pil_img)
    if img.ndim == 3:
        img = img[:, :, :3]
    else:
        # 如果是单通道也强制转成三通道（复制三次），以兼容彩色模板
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    best_name = None
    best_val = 0.0

    # 2. 遍历目录中所有 .png 模板
    for fname in os.listdir(pattern_dir):
        if not fname.lower().endswith('.png'):
            continue
        tpl_path = os.path.join(pattern_dir, fname)
        template = cv2.imread(tpl_path, cv2.IMREAD_COLOR_RGB)
        if template is None:
            continue

        # 3. 执行归一化系数模板匹配
        res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        if max_val > best_val:
            best_val = max_val
            best_name = os.path.splitext(fname)[0]

    # 4. 判断返回
    if best_val >= threshold:
        return best_name
    else:
        if important == 1:
            logger.critical(f"No match above threshold. Best match: {best_name} ({best_val:.3f})")
            raise Exception("No Card Find")
            # return None
        else:
            return 'nomatch'

DIGIT_FN_RE = re.compile(r"^(\d)\w*\.png$")

@lru_cache(maxsize=1)
def load_digit_templates(pattern_dir: str) -> List[Dict]:
    """
    只在第一次调用时加载所有模板：
    返回 [{'digit': '0', 'tpl': ndarray, 'w':.., 'h':..}, ...]
    """
    templates = []
    for fn in os.listdir(pattern_dir):
        m = DIGIT_FN_RE.match(fn)
        if not m:
            continue
        digit = m.group(1)
        path = os.path.join(pattern_dir, fn)
        tpl = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        tpl = cv2.threshold(tpl, BINARYZATION_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
        if tpl is None:
            continue
        h, w = tpl.shape
        # save_debug_image(tpl, f"template_{digit}")
        templates.append({'digit': digit, 'tpl': tpl, 'w': w, 'h': h})
    return templates

def save_debug_image(img: np.ndarray, step: str):
    """
    将单通道或三通道的 numpy 图像保存到 config.TEMP_PATH，
    文件名中带上 step 标识和毫秒级时间戳，避免重名。
    """
    os.makedirs(TEMP_PATH, exist_ok=True)
    ts = int(time.time() * 1000)
    fname = f"{step}_{ts}.png"
    path = os.path.join(TEMP_PATH, fname)
    # cv2.imwrite 接受单通道或三通道 BGR 图
    cv2.imwrite(path, img)
    return path

def ocr_number(
    pil_img: Image.Image,
    pattern_dir = DIGIT_PATTERN_DIR,
    threshold: float = 0.8,
    n: int = 2,
) -> Optional[int]:
    """
    识别最多 n 个白色数字，保存每一步的调试图像，并打印最高匹配度。
    """
    # 0. 原图
    img = np.array(pil_img)
    # save_debug_image(img, "step1_orig")

    # 1. 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if img.ndim == 3 else img
    # save_debug_image(gray, "step2_gray")

    # 2. Otsu 二值化
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    _, bw = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    save_debug_image(bw, "step3_bw_otsu")

    # 3. 开运算去噪
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    # bw_open = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel)
    # save_debug_image(bw_open, "step4_bw_open")
    
    bw_open = bw

    # 4. 白色像素太少，直接 0
    total = bw_open.size
    if total > 0 and cv2.countNonZero(bw_open) / total < 0.02:
        return 0

    # 5. 模板匹配，收集局部峰值
    raw_matches = []
    for info in load_digit_templates(pattern_dir):
        tpl = info['tpl']
        res = cv2.matchTemplate(bw_open, tpl, cv2.TM_CCOEFF_NORMED)
        # 可视化匹配分数图（选用归一化到 [0,255]）
        heat = (np.clip(res, 0, 1) * 255).astype(np.uint8)
        # save_debug_image(heat, f"heat_digit_{info['digit']}")

        # 找局部极大
        dil = cv2.dilate(res, np.ones((3,3), np.uint8))
        mask = (res == dil) & (res >= threshold)
        ys, xs = np.where(mask)
        for (y, x) in zip(ys, xs):
            raw_matches.append({
                'digit': info['digit'],
                'score': float(res[y, x]),
                'pt': (x, y),
                'w': info['w'],
                'h': info['h'],
            })

    if not raw_matches:
        return None

    #! 6. 打印最高匹配度
    highest = max(m['score'] for m in raw_matches)
    # logger.warning(f"[OCR] Highest match score: {highest:.4f}")
    if highest <= 0.9:
        logger.error(f"[OCR] Warning: Highest match score is low ({highest:.4f})")
        os.makedirs(BACKUP_PATH, exist_ok=True)
        for item in os.listdir(CARD_OUTPUT_DIR):
            src = os.path.join(CARD_OUTPUT_DIR, item)
            dst = os.path.join(BACKUP_PATH, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
                

    # 7. 全局按置信度降序，做 NMS
    raw_matches.sort(key=lambda x: x['score'], reverse=True)
    pts = np.array([m['pt'] for m in raw_matches], dtype=np.float32)
    ws = np.array([m['w'] for m in raw_matches], dtype=np.float32)
    hs = np.array([m['h'] for m in raw_matches], dtype=np.float32)

    selected = []
    used = np.zeros(len(raw_matches), dtype=bool)
    for i, m in enumerate(raw_matches):
        if used[i]:
            continue
        selected.append(m)
        if len(selected) >= n:
            break
        dx = np.abs(pts[:,0] - m['pt'][0])
        dy = np.abs(pts[:,1] - m['pt'][1])
        overlap = (dx < 0.5 * np.maximum(ws, m['w'])) & \
                  (dy < 0.5 * np.maximum(hs, m['h']))
        used = used | overlap

    if not selected:
        return None

    # 8. 按 x 排序，拼数字
    selected.sort(key=lambda x: x['pt'][0])
    s = ''.join(m['digit'] for m in selected)
    if int(s) == 0:
        logger.critical(f"WRONG OCR number: {s}")
        return 999
    try:
        return int(s)
    except ValueError:
        return None