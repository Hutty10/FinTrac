#!/usr/bin/env bash
# start_celery.sh
# Usage: ./start_celery.sh [worker|beat|all]

APP_MODULE="src.celery_app"
LOG_LEVEL="info"

function start_worker() {
    echo "Starting Celery worker..."
    celery -A $APP_MODULE worker --loglevel=$LOG_LEVEL
}

function start_beat() {
    echo "Starting Celery beat..."
    celery -A $APP_MODULE beat --loglevel=$LOG_LEVEL 
}

function start_all() {
    echo "Starting both Celery worker and beat..."
    start_worker &
    start_beat &
    wait
}

case "$1" in
    worker)
        start_worker
        ;;
    beat)
        start_beat
        ;;
    all)
        start_all
        ;;
    *)
        echo "Usage: $0 {worker|beat|all}"
        exit 1
        ;;
esac
