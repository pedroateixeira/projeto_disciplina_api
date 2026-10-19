"""
Configura os logs estruturados em JSON
"""

import logging
import sys
from datetime import datetime
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Formatter customizado que adiciona campos extras a cada log
    """

    def add_fields(self, log_record, record, message_dict):
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        log_record["level"] = record.levelname
        log_record["service"] = "api-iris"
        log_record["logger"] = record.name

        if not log_record.get("message"):
            log_record["message"] = record.getMessage()


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configura e retorna um logger em formato json
    Args:
    level: nivel minimo de log (DEBUG, INFO, WARNING, ERROR)

    returns:
    logger configurado em json
    """
    logger = logging.getLoger("api")
    logger.setLevel(getattr(logging, level.upper()))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
    )

    logger.handlers = []
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = setup_logging()
