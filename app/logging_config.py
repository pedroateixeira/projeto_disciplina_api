"""
Configura os logs estruturados em JSON
"""

import logging
import sys
from datetime import datetime, timezone

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Formatter customizado que adiciona campos extras a cada log
    """

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)  # mantem o extra={...}
        log_record["timestamp"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        log_record["level"] = record.levelname
        log_record["service"] = "api-iris"
        log_record["logger"] = record.name


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configura e retorna um logger em formato json
    Args:
    level: nivel minimo de log (DEBUG, INFO, WARNING, ERROR)

    returns:
    logger configurado em json
    """
    logger = logging.getLogger("api")
    logger.setLevel(getattr(logging, level.upper()))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomJsonFormatter("%(message)s"))

    logger.handlers = []
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = setup_logging()
