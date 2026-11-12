import urllib.request, numpy as np
import os, time, sqlite3, smtplib, winsound, threading
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
from email.mime.text import MIMEText
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify
import cv2
from ultralytics import YOLO

app = Flask(__name__)
app.secret_key = 'secure_sensor_secret_key'

ADMIN_USER = 'shreya'
ADMIN_PASS = 'pazuru'

SENDER_EMAIL = 'your_email@gmail.com'
SENDER_APP_PASSWORD = 'your_16_char_app_password'
ADMIN_RECEIVER_EMAIL = 'admin_receiver@gmail.com'
EMAIL_ENABLED = False

model = YOLO('yolov8n.pt')

cameras = {
    1: {'name': 'Camera 1 (Main)', 'url': '0'},
    2: {'name': 'Camera 2 (CCTV)', 'url': ''},
    3: {'name': 'Camera 3 (CCTV)', 'url': ''},
    4: {'name': 'Camera 4 (CCTV)', 'url': ''},
    5: {'name': 'Camera 5 (CCTV)', 'url': ''}
}
active_cam_id = 1
cap = cv2.VideoCapture(0)

threshold_limit = 10
current_count = 0
last_incident_time = 0
last_beep_time = 0
COOLDOWN_SECONDS = 30
DB_FILE = 'incidents.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('CREATE TABLE IF NOT EXISTS incidents (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, camera_name TEXT, count INTEGER, threshold INTEGER, status TEXT)')
    try:
        conn.execute('ALTER TABLE incidents ADD COLUMN camera_name TEXT DEFAULT "Camera 1"')
    except Exception:
        pass
    conn.commit()
    conn.close()

init_db()

def trigger_beep():
    global last_beep_time
    now = time.time()
    if now - last_beep_time > 1.2:
        last_beep_time = now
        threading.Thread(target=lambda: winsound.Beep(1500, 500), daemon=True).start()

def log_incident(cam_name, count, limit):
    conn = sqlite3.connect(DB_FILE)
    now_str = datetime.now().strftime('%d %b %Y, %I:%M:%S %p')
    conn.execute('INSERT INTO incidents (timestamp, camera_name, count, threshold, status) VALUES (?, ?, ?, ?, ?)', (now_str, cam_name, count, limit, 'Threshold Exceeded'))
    conn.commit()
    conn.close()

def send_email_alert(cam_name, count, limit):
    if not EMAIL_ENABLED:
        return
    try:
        msg = MIMEText(f'Alert on {cam_name}: {count} people detected (Limit: {limit}) at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.')
        msg['Subject'] = f'ALERT: {cam_name} Limit Exceeded ({count}/{limit})'
        msg['From'] = SENDER_EMAIL
        msg['To'] = ADMIN_RECEIVER_EMAIL
        with smtplib.SMTP_SSL('://gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, ADMIN_RECEIVER_EMAIL, msg.as_string())
    except Exception as e:
        print('Email failed:', e)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute('SELECT timestamp, COALESCE(camera_name, "Camera 1"), count, threshold, status FROM incidents ORDER BY id DESC LIMIT 50').fetchall()
    conn.close()
    return render_template('dashboard.html', threshold=threshold_limit, cameras=cameras, active_cam=active_cam_id, incidents=rows, total_incidents=len(rows))

@app.route('/set_threshold', methods=['POST'])
def set_threshold():
    global threshold_limit
    try:
        threshold_limit = max(0, int(request.form.get('threshold', 10)))
    except Exception:
        pass
    return redirect(url_for('dashboard'))

@app.route('/save_cameras', methods=['POST'])
def save_cameras():
    global cameras, active_cam_id, cap
    for i in range(1, 6):
        cameras[i]['url'] = str(request.form.get(f'cam_url_{i}', '')).strip()
    active_cam_id = int(request.form.get('active_cam', active_cam_id))
    target_url = cameras[active_cam_id]['url']
    if cap is not None:
        cap.release()
    if target_url.isdigit():
            cap = cv2.VideoCapture(int(target_url))
    elif target_url != '':
        cap = cv2.VideoCapture(target_url, cv2.CAP_FFMPEG) if target_url.startswith('rtsp') else cv2.VideoCapture(target_url)
    else:
        cap = None
    return redirect(url_for('dashboard'))

@app.route('/switch_cam/<int:cam_id>', methods=['POST'])
def switch_cam(cam_id):
    global active_cam_id, cap
    if cam_id in cameras:
        active_cam_id = cam_id
        target_url = cameras[cam_id]['url']
        if cap is not None:
            cap.release()
        if target_url.isdigit():
            cap = cv2.VideoCapture(int(target_url))
        elif target_url != '':
            cap = cv2.VideoCapture(target_url, cv2.CAP_FFMPEG) if target_url.startswith('rtsp') else cv2.VideoCapture(target_url)
        else:
            cap = None
    return redirect(url_for('dashboard'))

@app.route('/ring_alarm', methods=['POST'])
def ring_alarm():
    trigger_beep()
    return jsonify({'status': 'ringing'})

@app.route('/status')
def status():
    return jsonify({
        'count': current_count,
        'threshold': threshold_limit,
        'alarm': current_count > threshold_limit,
        'active_cam': cameras[active_cam_id]['name']
    })

def generate_frames():
    global current_count, last_incident_time
    while True:
        is_http = isinstance(cameras[active_cam_id]['url'], str) and cameras[active_cam_id]['url'].startswith('http')
        if not is_http and (cap is None or not cap.isOpened()):
            current_count = 0
            time.sleep(0.5)
            continue
        if isinstance(cameras[active_cam_id]['url'], str) and cameras[active_cam_id]['url'].startswith('http'):
            try:
                base = cameras[active_cam_id]['url'].replace('/video','').replace('https://','http://').rstrip('/')
                resp = urllib.request.urlopen(base + '/shot.jpg', timeout=2)
                arr = np.asarray(bytearray(resp.read()), dtype=np.uint8)
                frame = cv2.imdecode(arr, -1)
                success = frame is not None
            except Exception:
                success, frame = False, None
        else:
            success, frame = cap.read()
        if not success:
            current_count = 0
            time.sleep(0.2)
            continue
        results = model(frame, classes=[0], conf=0.60, verbose=False)
        person_count = len(results[0].boxes)
        current_count = person_count
        annotated_frame = results[0].plot()
        cam_label = cameras[active_cam_id]['name']
        if person_count > threshold_limit:
            trigger_beep()
            text = f'{cam_label} | ALERT ({person_count}/{threshold_limit})'
            cv2.putText(annotated_frame, text, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 5)
            cv2.putText(annotated_frame, text, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 2)
            now = time.time()
            if now - last_incident_time > COOLDOWN_SECONDS:
                last_incident_time = now
                log_incident(cam_label, person_count, threshold_limit)
                send_email_alert(cam_label, person_count, threshold_limit)
        else:
            text = f'{cam_label} | People: {person_count} / Limit: {threshold_limit}'
            cv2.putText(annotated_frame, text, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 5)
            cv2.putText(annotated_frame, text, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
        hd_frame = cv2.resize(annotated_frame, (960, 540))
        ret, buffer = cv2.imencode('.jpg', hd_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)






