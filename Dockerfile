FROM python:3.11-slim

# Cài đặt FFmpeg và các thư viện cần thiết
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt các thư viện cần thiết
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy mã và các file cần thiết
COPY run.sh /run.sh
COPY detect.py /detect.py

# Thiết lập quyền cho script
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
