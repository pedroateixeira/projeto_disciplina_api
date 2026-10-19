"""
Metricas customizadas com prometheus
define contadores, histogramas e gauges de monitoramento

"""

from prometheus_client import Counter, Gauge, Histogram

PREDICTIONS_TOTAL = Counter(
    "iris_predictions_total",
    "Total de predicoes realizadas",
    ["classe", "user"],
)

LOGIN_ATTEMPTS = Counter(
    "login_attempts_total", "total de tentativas de login", ["status"]
)
ERROS_TOTAL = Counter("api_erros_total", "total de erros", ["endpoint", "error_type"])

PREDICTION_LATENCY = Histogram(
    "iris_prediction_latency_seconds",
    "latencia das predições em segundos",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

MODEL_LOADED = Gauge("model_loaded", "indica se o modelo está carregado (1) ou nao (0)")
AVG_CONFIDENCE = Gauge(
    "prediction_avg_confidence", "confiança media das ultimas predicoes"
)
