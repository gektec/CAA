import os
import sys
import time
import datetime
import subprocess

# -------------------------------------------------------------------
# 配置区
START_TIME = datetime.time(hour=5, minute=0)     # 每天 05:00 启动
STOP_TIME  = datetime.time(hour=3, minute=30)    # 次日 03:30 停止

CHECK_INTERVAL = 30    # 秒，轮询间隔
# -------------------------------------------------------------------

# 得到脚本目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# venv 下的 python 可执行文件
PYTHON_EXE = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")

# 要启动的脚本
TARGET_SCRIPT = os.path.join(BASE_DIR, "main.py")

# Windows 下新开控制台的标志
CREATE_NEW_CONSOLE = 0x00000010

def is_active_period(now_time):
    """
    当 START_TIME <= STOP_TIME 时，活动期为 START_TIME <= now <= STOP_TIME
    当 START_TIME > STOP_TIME 时（跨午夜），活动期为 now >= START_TIME 或 now < STOP_TIME
    """
    if START_TIME <= STOP_TIME:
        return START_TIME <= now_time < STOP_TIME
    else:
        return now_time >= START_TIME or now_time < STOP_TIME

def main():
    proc = None
    print("Watchdog 启动，监控脚本：", TARGET_SCRIPT)
    try:
        while True:
            now = datetime.datetime.now().time()
            active = is_active_period(now)

            # 如果在活动期，且脚本未运行，则启动
            if active:
                if proc is None or proc.poll() is not None:
                    print(f"{datetime.datetime.now()} - 当前在活动期，启动脚本。")
                    # 用 venv 下的 python.exe 启动 target_script.py，另开一个控制台窗口
                    proc = subprocess.Popen(
                        [PYTHON_EXE, TARGET_SCRIPT],
                        creationflags=CREATE_NEW_CONSOLE
                    )
                else:
                    # 已在运行中
                    pass
            else:
                # 非活动期，若脚本在运行，则停止
                if proc is not None and proc.poll() is None:
                    print(f"{datetime.datetime.now()} - 当前不在活动期，停止脚本。")
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    proc = None

            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("Watchdog 收到终止信号，退出前会停止子进程。")
        if proc and proc.poll() is None:
            proc.terminate()
    print("Watchdog 已退出。")

if __name__ == "__main__":
    main()
