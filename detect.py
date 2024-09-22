import cv2
import subprocess
import numpy as np
import mediapipe as mp
import asyncio
from quart import Quart, Response
import sys

# Flask App được thay bằng Quart để hỗ trợ async
app = Quart(__name__)

# URL RTSP của camera IP (lấy từ tham số hoặc tùy chọn mặc định)
rtsp_url = sys.argv[1]

# Sử dụng FFmpeg để mở RTSP stream và chuyển mã từ H.265 sang H.264
ffmpeg_command = [
    'ffmpeg',
    '-rtsp_transport', 'udp',  # Sử dụng giao thức UDP
    '-i', rtsp_url,
    '-f', 'rawvideo',          # Định dạng đầu ra
    '-pix_fmt', 'bgr24',       # Định dạng pixel phù hợp cho OpenCV
    '-an', '-s', '640x480',    # Thiết lập kích thước khung hình để tránh quá tải
    '-r', '15',                # Thiết lập FPS
    'pipe:1'                   # Xuất đầu ra vào pipe
]

# Khởi tạo BlazePose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Khởi chạy FFmpeg và mở kết nối tới OpenCV thông qua pipe
ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, bufsize=10**8)


async def generate():
    """Hàm sinh ra từng khung hình được mã hóa MJPEG dưới dạng async"""
    while True:
        # Sử dụng asyncio để đọc dữ liệu từ pipe một cách non-blocking
        raw_frame = await asyncio.to_thread(ffmpeg_process.stdout.read, 640 * 480 * 3)
        if len(raw_frame) == 0:
            print("Kết thúc stream hoặc có lỗi xảy ra.")
            break

        # Chuyển đổi dữ liệu thành mảng Numpy
        frame = np.frombuffer(raw_frame, np.uint8).reshape((480, 640, 3))

        # Tạo một bản sao của frame để có thể ghi
        frame_copy = frame.copy()

        # Chuyển đổi khung hình thành định dạng RGB cho Mediapipe
        frame_rgb = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB)

        # Phát hiện tư thế bằng BlazePose
        results = await asyncio.to_thread(pose.process, frame_rgb)

        # Vẽ các keypoint tư thế trên khung hình
        if results.pose_landmarks:
            await asyncio.to_thread(
                mp.solutions.drawing_utils.draw_landmarks,
                frame_copy, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
            )

        # Mã hóa khung hình thành MJPEG
        ret, jpeg = cv2.imencode('.jpg', frame_copy)
        if not ret:
            continue

        # Tạo luồng MJPEG và gửi khung hình
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

        # # Điều chỉnh để kiểm soát tốc độ xử lý
        # await asyncio.sleep(0.1)


@app.route('/video_feed')
async def video_feed():
    """Đường dẫn phát trực tiếp MJPEG stream"""
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    # Sử dụng asyncio để chạy Quart một cách async
    app.run(host='0.0.0.0', port=5001)  # Chạy trên cổng khác 5000 để tránh xung đột
