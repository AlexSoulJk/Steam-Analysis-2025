import logging
import logging.handlers


def setup_logger(source_name):
    # Создание логгера
    logger = logging.getLogger(f'my_app_{source_name}')
    logger.setLevel(logging.DEBUG)

    # Форматтер для всех обработчиков
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Обработчик для файла (с ротацией)
    file_handler = logging.handlers.RotatingFileHandler(
        f'app_{source_name}.log',
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding='utf-8'  # ← ДОБАВЬТЕ ЭТУ СТРОКУ
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Добавление обработчиков
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger