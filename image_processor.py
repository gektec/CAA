# image_processor.py
from config import LEFT_BOTTOM_REGIONS, RIGHT_BOTTOM_REGIONS
from PIL import Image, ImageDraw
import numpy as np
import cv2


def crop_regions(image, regions):
    """
    Crop multiple regions from a PIL Image based on provided bounding boxes.
    """
    crops = []
    for (x, y, w, h) in regions:
        crop = image.crop((x, y, x + w, y + h))
        crops.append(crop)
    return crops


def preprocess_image_for_model(pil_img, size=(224, 224)):
    """
    Preprocess a PIL image for model prediction: resize, normalize.
    """
    img = np.array(pil_img)
    # Convert RGBA to RGB if needed
    if img.shape[-1] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    img = cv2.resize(img, size)
    img = img.astype('float32') / 255.0
    return np.expand_dims(img, axis=0)


def mask_circle(img, radius=56, fill=(0, 0, 0)):
    """
    Keep only a central circle of given radius in img, filling outside with `fill` color.
    """
    width, height = img.size
    cx, cy = width // 2, height // 2
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=255)
    background = Image.new('RGB', (width, height), fill)
    result = Image.composite(img, background, mask)
    draw2 = ImageDraw.Draw(result)
    # draw additional black circles at (80,100) and (10,100) with radius 10
    draw2.ellipse((90 - 22, 105 - 22, 90 + 22, 105 + 22), fill=fill)
    draw2.ellipse((22 - 22, 105 - 22, 22 + 22, 105 + 22), fill=fill)
    return result


def backup_img(pil_img, src_path=None, num=0, slot_name='', mode_name=''):
    """
    将图片备份到 backup 目录下，文件名提供必要信息，包括原文件名/路径、识别值、模式、时间戳等
    """
    os.makedirs('backup', exist_ok=True)
    basename = os.path.basename(src_path) if src_path else 'UNK.png'
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # 文件名示例：backup/UNK_num0_SLOT_mode_TIME.png
    outname = f"backup/{os.path.splitext(basename)[0]}_num{num}_{slot_name}_{mode_name}_{ts}.png"
    pil_img.save(outname)
    print(f"[INFO] 识别值为0，已备份图片到: {outname}")



