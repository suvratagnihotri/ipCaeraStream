import cv2
from flask import Flask, Response

# Replace 'your_username' and 'your_password' with your actual camera credentials
rtsp_url = 'rtsp://suvrat:123456@192.168.130.193:6677/h264_pcm.sdp'

app = Flask(__name__)
camera = cv2.VideoCapture(rtsp_url)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/ipcameravideo')
def index():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=5001)
