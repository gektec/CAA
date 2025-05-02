# Android 自动化操作与数据采集框架

## 目录结构

```
.
├── config.py            # 配置文件：ADB路径、截图区域、点击坐标
├── adb_controller.py    # ADB 操作：截图、点击、等待
├── image_processor.py   # 图像处理：裁剪、分类、OCR 识别
├── ml_trainer.py        # 机器学习模块：训练、保存模型
├── main.py              # 入口脚本：流程编排
├── requirements.txt     # Python 依赖列表
└── README.md            # 项目说明
```

## 使用方法

1. 安装依赖:

   ```bash
   pip install -r requirements.txt
   ```

2. 配置 `config.py` 中的坐标和 ADB 路径
3. 确保已启动 Android 模拟器并能使用 `adb` 连接
4. 运行脚本:

   ```bash
   python main.py
   ```

脚本会循环执行以下操作：

- 获取模拟器截图
- 裁剪左下/右下三个区域，识别卡牌类别和数量
- 裁剪胜率区域，OCR 识别胜率数值
- 执行点击操作，等待下一轮
- 收集并保存数据，用于训练机器学习模型

## 扩展说明

- 分类模型逻辑请在 `image_processor.py` 中实现
- OCR 识别依赖 `pytesseract`，请安装对应的系统包（Tesseract-OCR）
- 训练逻辑请在 `ml_trainer.py` 中实现并调整超参数 



帮我完善全部流程：根据截取的模式与patterns/mods的对比决定按键。每秒点击一次。在main时点击(1750, 900)，在select时点击(1500, 800) 然后隔0.5秒点击(1760, 900)，在ingame时，开始使用slot_capture截取slots，然后点击(960, 680)，并开始每0.5秒截取一次win，直到interm。在clearing时点击(1800, 1000)，在outside和home时报错并退出。完成一次循环后控制台输出一个信号。