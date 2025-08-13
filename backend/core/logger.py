import logging
import colorlog
from colorlog import StreamHandler


def get_logger(name: str = "app") -> logging.Logger:
    """Returns a colorized logger instance with the given name."""
    handler: StreamHandler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )

    logger: logging.Logger = colorlog.getLogger(name)
    # Prevent adding multiple handlers if get_logger is called multiple times
    if not logger.hasHandlers():
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
