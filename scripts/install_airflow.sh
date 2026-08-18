#!/usr/bin/env bash
set -euo pipefail

AIRFLOW_VERSION="${AIRFLOW_VERSION:-3.3.0}"
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

python -m pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
python -m pip install -e .
python -m pip check

printf 'Installed Apache Airflow %s with constraints for Python %s.\n' \
  "${AIRFLOW_VERSION}" "${PYTHON_VERSION}"
