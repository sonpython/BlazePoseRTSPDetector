#!/usr/bin/env bash
# Đọc input_source từ cấu hình Add-on
INPUT_SOURCE=$(jq --raw-output '.input_source' /data/options.json)

# Khởi động máy chủ Flask để phát video
python3 /detect.py "$INPUT_SOURCE"
