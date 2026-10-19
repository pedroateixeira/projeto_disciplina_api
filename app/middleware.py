"""
Middleware para logging e metricas para logging automatico
"""

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_config import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que loga as requisicoes automaticamente

    adiciona:
    trace_id: ID unico para rastrear todas as requisicoes
    latency_ms: tempo de resposta em milisegundos
    headers de resposta com trace_id e tempo
    """

    async def dispatch(self, request, call_next):

        trace_id = str(uuid.uuid4())[:8]
        request.state.trace_id = trace_id
        start_time = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "request_completed",
            extra={
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
                "client_ip": request.client.host if request.client else None,
            },
        )

        response.headers["X-Trace-ID"] = trace_id
        response.header["X-Response-Time-Ms"] = str(round(latency_ms, 2))
        return response
