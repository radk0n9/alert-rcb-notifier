#!/bin/sh
set -e

exec python app/main.py ${APP_ARGS:-}
