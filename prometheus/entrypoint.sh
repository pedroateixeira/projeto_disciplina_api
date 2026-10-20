#!/usr/bin/env sh
set -eu

: "${PORT:=9090}"
: "${SCRAPE_INTERVAL:=15s}"
: "${API_SCHEME:=https}"
: "${API_TARGET:?Defina API_TARGET (ex: api-iris-v2.onrender.com)}"
: "${METRICS_PATH:=/metrics}"

cat >/etc/prometheus/prometheus.yml <<EOF
global:
  scrape_interval: ${SCRAPE_INTERVAL}

scrape_configs:
  - job_name: "api-iris-v2"
    scheme: ${API_SCHEME}
    metrics_path: ${METRICS_PATH}
    static_configs:
      - targets: ["${API_TARGET}"]

rule_files:
  - /etc/prometheus/alerts.yml
EOF

exec /bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.listen-address="0.0.0.0:${PORT}"
