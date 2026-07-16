# services/logging_service.py

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import constants as const


class Logger:
    _logger = None

    @classmethod
    def initialize(
        cls
    ):
        """
        Initializes the application logger.
        Call once during application startup.
        """

        if cls._logger is not None:
            return

        Path(Path(const.LOGGING_FILE).parent).mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger("InventoryApp")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = RotatingFileHandler(
            const.LOGGING_FILE,
            maxBytes=5 * 1024 * 1024,   # 5 MB
            backupCount=5,
            encoding="utf-8",
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        cls._logger = logger

    @classmethod
    def debug(cls, message: str):
        if cls._logger is None:
            cls.initialize()
        cls._logger.debug(message, stacklevel=2)

    @classmethod
    def info(cls, message: str):
        if cls._logger is None:
            cls.initialize()
        cls._logger.info(message, stacklevel=2)

    @classmethod
    def warning(cls, message: str):
        if cls._logger is None:
            cls.initialize()
        cls._logger.warning(message, stacklevel=2)

    @classmethod
    def error(cls, message: str):
        if cls._logger is None:
            cls.initialize()
        cls._logger.error(message, stacklevel=2)

    @classmethod
    def exception(cls, message: str):
        """
        Logs the current exception including full traceback.
        Must be called inside an except block.
        """
        if cls._logger is None:
            cls.initialize()
        cls._logger.exception(message, stacklevel=2)