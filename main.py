# main.py
import sys
import os
import time
from adb_controller import take_screenshot, tap
from recognizer import match_pattern
import card_capture
from config import MODE_REGION, WAIT_TIME, MODE_PATTERN_DIR, DATA_DIR
import csv
from train_models import train_and_select_best
import numpy as np
import random
import re
from logger import setup_logger



#TODO: 局内保持匹配地图，成功后才导出数据


def double_tap(x,y):
    tap(x,y)
    time.sleep(0.2)
    tap(x,y)

def make_feature_vec(header, test_records):
    """
    把test_records转换为特征向量（header对应顺序）。
    """
    # 建一个名字到分数的字典
    counts = {name: 0 for name in header}
    for name, value in test_records:
        if name in counts:
            counts[name] += value  # 有的单位同名会多次出现
        # else: 可以忽略‘empty1’，也可以把所有 empty 系列都映射成0，不影响
    # 返回特征向量（有序）
    return [counts[name] for name in header]

def main():
    
    logger = setup_logger()
    
    correct_predictions = 0   # 预测正确次数
    total_predictions = 0     # 总预测次数
    # Prepare CSV file for recording slot info and results
    
    model, X_test, y_test = train_and_select_best(DATA_DIR)
    
    header = [
        'knight','small_rock','baseball','dog','ice','crocodile','snowball','gatlin','sheep','boxer','sarkaz','neon','mouse','shield','pig','jesselton','bleeding','acid','sax','spider','beast','pompeii','samii','aoe_wizard','hermit_crab','candlestick','boom','big_rock','sailer','reborn','bite','reddao','zizai','zaaro', 'coral', 'small_axe','big_crab','flower','pirate','fast_axe','saw_machine','kicker','mortar','rpg','sarkaz_wizard','big_axe','stabber','door','sandman','water_cannon','archer','swimmer','bear','ice_boom','fast_hammer','small_reddao'
    ]
    
    
    logger.info("Starting automation loop. Press Ctrl+C to stop.")
    
    
    while True:
        
        img = take_screenshot()
        if img is None:
            logger.error("Failed to capture screenshot")
            continue
        # Determine current mode
        mode = match_pattern(img.crop(MODE_REGION), MODE_PATTERN_DIR, 0)
        if mode == 'home':
            double_tap(1750,350)
        elif mode == 'outside':
            logger.critical(f"detected '{mode}' state. Exiting.")  # 此处用 error 显示
            sys.exit(1)
        elif mode == 'main':
            logger.info("State: main")
            while True:
                double_tap(1750, 900)
                time.sleep(WAIT_TIME)
                img = take_screenshot()
                if img is None:
                    continue
                if match_pattern(img.crop(MODE_REGION), MODE_PATTERN_DIR, 0) != 'main':
                    break
        elif mode == 'select':
            logger.info("State: select")
            
            # 联机
            # double_tap(500, 900)
            # time.sleep(1)
            # 联机2
            # double_tap(1000, 900)
            # time.sleep(1)
            # 单机
            double_tap(1500, 800)
            
            
            time.sleep(0.5)
            double_tap(1760, 900)
            time.sleep(0.5)
        elif mode in ('ingame', 'ingame2', 'ingame3', 'ingame4'):
            logger.info("State: ingame")
            # Capture slot info for both sides
            time.sleep(0.5)
            left_slot_info, right_slot_info = card_capture.main()
            
            # 预测结果
            test_records = []
            for name, count in left_slot_info:
                test_records.append((name, count or 0))
            for name, count in right_slot_info:
                test_records.append((name, -(count or 0)))
            test_feature = make_feature_vec(header, test_records)
            test_feature_np = np.array(test_feature).reshape(1, -1)
            y_pred = model.predict(test_feature_np)
            prob = model.predict_proba(test_feature_np)
            predicted = y_pred[0]
            logger.warning(f"Predicted {'WIN' if y_pred[0]==1 else 'LOSE'}, Probability: {prob[0][1]:.2%}")  # 重要输出用WARNING

            # # 联机模式
            # time.sleep(random.random() * 5 + 6)
            # if y_pred[0] == 1:
            #     double_tap(960, 680)
            #     time.sleep(0.5)
            #     double_tap(300, 950)
            # else:
            #     double_tap(960, 680)
            #     time.sleep(0.5)
            #     double_tap(1580, 950)  
            # # 单机模式
            double_tap(960, 680)


            result = None
            while True:
                img = take_screenshot()
                if img is None:
                    logger.error("Failed to capture screenshot")
                    continue
                # 直接用 detect_mode 判断 win/lose
                state = match_pattern(img.crop(MODE_REGION), MODE_PATTERN_DIR, 0) 
                if state == 'win':
                    result = 'win'
                    logger.warning("Detected WIN\n")
                    break
                elif state == 'lose':
                    result = 'lose'
                    logger.warning("Detected LOSE\n")
                    break
                # 还没到胜/败界面则继续轮询
                time.sleep(0.3)
            # —— 检测完毕 —— 
            # Prepare records with negative counts for the losing side
            
            total_predictions += 1
            
            if total_predictions % 100 == 0 and total_predictions > 1:
                model, X_test, y_test = train_and_select_best(DATA_DIR)
                logger.error("New model trained and selected")
            
            # 实际结果映射成数字：'win'->1, 'lose'->0
            actual = 1 if result == 'win' else 0
            if predicted == actual:
                correct_predictions += 1
                
            logger.warning(f"Accuracy: {correct_predictions / total_predictions:.2%}, {correct_predictions}/{total_predictions}")  # 重要输出用WARNING
            
            records = []
            if result == 'win':
                resultnum = 1
                for name, count in left_slot_info:
                    records.append((name, count or 0))
                for name, count in right_slot_info:
                    records.append((name, -(count or 0)))
            elif result == 'lose':
                resultnum = 0
                for name, count in left_slot_info:
                    records.append((name, -(count or 0)))
                for name, count in right_slot_info:
                    records.append((name, count or 0))
            
            if 999 in (count for name, count in records):
                logger.critical("Wrong Number (999), output ancelled")
                continue
            
            if resultnum != predicted:
                logger.warning(f"Detected wrong result, Records: {records}")
            else:
                logger.info(f"Detected correct result, Records: {records}")

            record_dict = dict(records)

            # 校验：非 emptyxxx 的槽位 count 不能是 0
            skip_write = False
            for name, count in records:
                # name 不匹配 empty + 数字/字母，且 count==0
                if not re.match(r'^empty[0-9A-Za-z]+$', name) and count == 0:
                    logger.critical(f"Non‐empty slot '{name}' has zero count, skipping this record.")
                    skip_write = True
                    break
                
                
            if skip_write:
                continue

            else:
            # 写 CSV
                write_header = False
                if not os.path.exists(DATA_DIR) or os.path.getsize(DATA_DIR) == 0:
                    write_header = True
                else:
                    with open(DATA_DIR, 'r', newline='') as f:
                        reader = csv.reader(f)
                        try:
                            first_row = next(reader)
                            if first_row != header:
                                write_header = True
                        except StopIteration:
                            write_header = True

                with open(DATA_DIR, 'a', newline='') as f:
                    writer = csv.writer(f)
                    if write_header:
                        writer.writerow(header)
                    writer.writerow([record_dict.get(name, 0) for name in header])

        elif mode in ('clearing', 'clearing2'):
            logger.info("State: clearing")
            while True:
                double_tap(1800, 1000)
                time.sleep(WAIT_TIME)
                img = take_screenshot()
                if img is None:
                    continue
                if match_pattern(img.crop(MODE_REGION), MODE_PATTERN_DIR, 0) != 'clearing':
                    break
            logger.error("Cycle completed")
        elif mode in ('loading', 'interm','interm2','prepare','win','lose','nomode'):
            continue
        else:
            logger.info(f"Unknown mode '{mode}', waiting.")
            time.sleep(WAIT_TIME)


if __name__ == '__main__':
    
    main()
