import logging



def setup_logger():
    class ColorFormatter(logging.Formatter):
        COLORS = {
        'DEBUG': '\033[37m',    # 灰色
        'INFO': '\033[0m',      # 默认色
        'WARNING': '\033[33m',  # 黄色，重要信息用黄色高亮
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
        RESET = '\033[0m'

        def format(self, record):
            color = self.COLORS.get(record.levelname, self.RESET)
            message = super().format(record)
            return f"{color}{message}{self.RESET}"

    logger = logging.getLogger("my_logger")
    logger.setLevel(logging.DEBUG)

# 控制台输出，带颜色
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = ColorFormatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# 文件输出，不带颜色
    log_file = "app.log"
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    formatter_no_color = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter_no_color)
    logger.addHandler(fh)
    return logger
