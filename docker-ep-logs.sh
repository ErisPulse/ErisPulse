#!/usr/bin/env bash
LOG_FILE="${ERISPULSE_LOG_FILE:-/app/logs/erispulse.log}"
if [ ! -f "${LOG_FILE}" ]; then
    echo "[ErisPulse] 日志文件不存在: ${LOG_FILE}"
    echo "[ErisPulse] 请确保配置 [ErisPulse.logger] 下已设置 log_files = [\"${LOG_FILE}\"]"
    exit 1
fi
tail -f "${LOG_FILE}" "$@"
