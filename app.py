from queue import Queue
import threading
from flask import Flask, render_template,Response
from flask_socketio import SocketIO, join_room, leave_room, emit
import cv2

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
rtsp_url = 'rtsp://suvrat:123456@192.168.130.193:6677/h264_pcm.sdp'
camera = cv2.VideoCapture(rtsp_url)

frame_queue = Queue()

def generate_frames():
    camera = cv2.VideoCapture(rtsp_url)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            frame_queue.put(frame)

@app.route('/')
def index():
    return render_template('index.html')

def video_stream():
    while True:
        # Retrieve frames from the queue
        frame = frame_queue.get()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        

@app.route('/ipcameravideo')
def ipcameravideo():
    return Response(video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('join')
def handle_join(roomId):
    selected_room = [sid for sid, namespace in socketio.server.manager.rooms.items() if roomId in namespace]
    number_of_clients = len(selected_room) if selected_room else 0

    if number_of_clients == 0:
        print(f"Creating room {roomId} and emitting room_created socket event")
        join_room(roomId)
        emit('room_created', roomId)
    elif number_of_clients == 1:
        print(f"Joining room {roomId} and emitting room_joined socket event")
        join_room(roomId)
        emit('room_joined', roomId)
    else:
        print(f"Can't join room {roomId}, emitting full_room socket event")
        emit('full_room', roomId)

@socketio.on('start_call')
def start_call(roomId):
    print(f"Broadcasting start_call event to peers in room {roomId}")
    emit('start_call', room=roomId, broadcast=True)

@socketio.on('webrtc_offer')
def webrtc_offer(data):
    print(f"Broadcasting webrtc_offer event to peers in room {data['roomId']}")
    emit('webrtc_offer', data['sdp'], room=data['roomId'])

@socketio.on('webrtc_answer')
def webrtc_answer(data):
    print(f"Broadcasting webrtc_answer event to peers in room {data['roomId']}")
    emit('webrtc_answer', data['sdp'], room=data['roomId'])

@socketio.on('webrtc_ice_candidate')
def webrtc_ice_candidate(data):
    print(f"Broadcasting webrtc_ice_candidate event to peers in room {data['roomId']}")
    emit('webrtc_ice_candidate', data, room=data['roomId'])

if __name__ == '__main__':
    threading.Thread(target=generate_frames).start()
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
