import os
from adb_controller import take_screenshot
from image_processor import crop_regions, mask_circle
from config import LEFT_BOTTOM_REGIONS, RIGHT_BOTTOM_REGIONS, LEFT_BOTTOM_NUMS, RIGHT_BOTTOM_NUMS
from recognizer import match_pattern, ocr_number
from config import CARD_PATTERN_DIR, CARD_OUTPUT_DIR 

def main():
    # Prepare output directory
    output_dir = CARD_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    # Take a screenshot
    img = take_screenshot()
    if img is None:
        print('Failed to take screenshot')
        # Return empty slot info lists to indicate failure
        return [], []

    # Save full screenshot
    full_path = os.path.join(output_dir, 'full_screenshot.png')
    img.save(full_path)
    # print(f'Saved full screenshot to {full_path}')

    # Crop and save left bottom regions
    left_crops = crop_regions(img, LEFT_BOTTOM_REGIONS)
    left_masked = []
    for idx, crop in enumerate(left_crops, start=1):
        masked_img = mask_circle(crop)
        left_masked.append(masked_img)
        path = os.path.join(output_dir, f'left_{idx}_masked.png')
        masked_img.save(path)
        # print(f'Saved masked left region {idx} to {path}')
        

    # Crop and save right bottom regions
    right_crops = crop_regions(img, RIGHT_BOTTOM_REGIONS)
    right_masked = []
    for idx, crop in enumerate(right_crops, start=1):
        masked_img = mask_circle(crop)
        right_masked.append(masked_img)
        path = os.path.join(output_dir, f'right_{idx}_masked.png')
        masked_img.save(path)
        # print(f'Saved masked right region {idx} to {path}')

    # Crop and save left bottom numeric regions
    left_num_crops = crop_regions(img, LEFT_BOTTOM_NUMS)
    for idx, crop in enumerate(left_num_crops, start=1):
        path = os.path.join(output_dir, f'left_num_{idx}.png')
        crop.save(path)
        # print(f'Saved left bottom number region {idx} to {path}')

    # Crop and save right bottom numeric regions
    right_num_crops = crop_regions(img, RIGHT_BOTTOM_NUMS)
    for idx, crop in enumerate(right_num_crops, start=1):
        path = os.path.join(output_dir, f'right_num_{idx}.png')
        crop.save(path)
        # print(f'Saved right bottom number region {idx} to {path}')

    # Match slot patterns to get names and counts for left side
    left_slot_info = []
    for idx, crop in enumerate(left_masked):
        name = match_pattern(crop, CARD_PATTERN_DIR, 1)
        count = None
        if idx < len(left_num_crops):
            count = ocr_number(left_num_crops[idx])
        left_slot_info.append((name, count))

    # Match slot patterns to get names and counts for right side
    right_slot_info = []
    for idx, crop in enumerate(right_masked):
        name = match_pattern(crop, CARD_PATTERN_DIR, 1)
        count = None
        if idx < len(right_num_crops):
            count = ocr_number(right_num_crops[idx])
        right_slot_info.append((name, count))

    return left_slot_info, right_slot_info


if __name__ == '__main__':
    main() 