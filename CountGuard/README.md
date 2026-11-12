# 🚨 Real-Time People Counting & Threshold Alert System

A real-time **Computer Vision and Web-Based Monitoring System** that uses **YOLOv11n, OpenCV, and Flask** to detect and count people from a live camera feed.

When the number of detected people exceeds a predefined threshold, the system automatically sends an **email notification to the administrator**. The processed camera feed is simultaneously streamed through a Flask web application.

---

## 📌 Overview

The system is designed for environments where monitoring the number of people in a particular area is important.

The application:

1. Captures live video from a webcam.
2. Processes each frame using **YOLOv11n**.
3. Detects objects belonging to the `person` class.
4. Counts the detected people.
5. Compares the count with a configurable threshold.
6. Displays bounding boxes around detected people.
7. Sends an email alert when the threshold is exceeded.
8. Provides real-time monitoring through a Flask web interface.

---

## ✨ Features

* 🎥 **Real-Time Camera Monitoring**
* 👤 **Person Detection using YOLOv11n**
* 🔢 **Real-Time People Counting**
* 🚨 **Automatic Threshold Detection**
* 📧 **Email Alerts using Gmail SMTP**
* 🌐 **Flask Web Dashboard**
* 📡 **Live MJPEG Video Streaming**
* 📊 **Real-Time Count API**
* 🟩 **Bounding Box Visualization**
* 🔐 **Environment Variable Based Credentials**
* ⏱️ **Email Alert Cooldown**

---

## 🧠 System Architecture

```text
                    ┌─────────────────┐
                    │     Webcam      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     OpenCV      │
                    │ VideoCapture(0) │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    YOLOv11n     │
                    │ Object Detection│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Filter "person" │
                    │  Class Objects  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  People Count   │
                    └────────┬────────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
                  ▼                     ▼
          Count ≤ Threshold       Count > Threshold
                  │                     │
                  ▼                     ▼
               NORMAL              🚨 ALERT
                                        │
                                        ▼
                                ┌──────────────┐
                                │ Email via    │
                                │ Gmail SMTP   │
                                └──────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Flask Web Server │
                    └────────┬────────┘
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
             Live Video             /count API
```

---

## 🛠️ Tech Stack

| Technology              | Purpose                             |
| ----------------------- | ----------------------------------- |
| **Python**              | Core application development        |
| **YOLOv11n**            | Real-time person detection          |
| **Ultralytics**         | YOLO model implementation           |
| **OpenCV**              | Camera capture and image processing |
| **Flask**               | Web server and API                  |
| **SMTP**                | Email communication                 |
| **Gmail**               | Alert delivery                      |
| **HTML/CSS/JavaScript** | Web interface                       |
| **python-dotenv**       | Environment variable management     |

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Utkarshsingh201/CountGuard.git
```

Navigate into the project:

```bash
cd People-Counting-Alert
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 📦 YOLO Model

This project uses the lightweight:

```text
YOLOv11n
```

model for real-time object detection.

The code loads the model using:

```python
model = YOLO("yolo11n.pt")
```

Place the model file in the project directory:

```text
yolo11n.pt
```

For public repositories, avoid committing large model files directly if repository size is a concern.

---

# 🔐 Email Configuration

The system uses environment variables to protect email credentials.

Create a `.env` file:

```env
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_google_app_password
RECEIVER_EMAIL=admin@example.com
```

The application reads these values using:

```python
os.getenv()
```

### Gmail Authentication

For Gmail, use a **Google App Password** instead of your regular Gmail password.

Never hard-code your email password inside the Python source code.

---

# 🎯 Configure the Threshold

The maximum allowed number of people can be configured using:

```python
THRESHOLD = 1
```

For example:

```python
THRESHOLD = 5
```

With a threshold of `5`:

```text
0 → NORMAL
1 → NORMAL
2 → NORMAL
3 → NORMAL
4 → NORMAL
5 → NORMAL
6 → 🚨 THRESHOLD EXCEEDED
```

The alert condition is:

```python
people_count > THRESHOLD
```

---

# 🚀 Running the Application

Start the Flask server:

```bash
python app.py
```

The terminal should display something similar to:

```text
 * Running on http://127.0.0.1:5000
```

Open the address in your browser:

```text
http://127.0.0.1:5000
```

Make sure your webcam is available because the application uses:

```python
cv2.VideoCapture(0)
```

---

# 🌐 Flask Endpoints

## `/`

Displays the main web interface.

```text
GET /
```

---

## `/video`

Provides the live camera stream.

```text
GET /video
```

The endpoint returns an MJPEG stream containing the processed camera frames.

---

## `/count`

Returns the current people count and system status.

Example response:

```json
{
    "count": 4,
    "status": "EXCEEDED",
    "email": "✅ Email Sent to Admin"
}
```

Possible status values:

```text
NORMAL
EXCEEDED
```

---

# 📧 Email Alert

When:

```text
People Count > Threshold
```

the system generates an email containing:

```text
🚨 ALERT: Threshold Exceeded!

WARNING!

Live People Count: 4
Allowed Limit: 3

Immediate action required.
```

The email is sent through Gmail's SMTP server:

```text
smtp.gmail.com
Port: 587
```

with TLS encryption enabled.

---

# ⏱️ Alert Cooldown

The application includes a cooldown mechanism:

```python
ALERT_COOLDOWN = 5
```

This prevents an email from being sent on every single video frame.

The system waits for the cooldown period before sending another alert while the threshold remains exceeded.

---

# 🔄 Detection Pipeline

Each frame follows this pipeline:

```text
Camera
   ↓
Frame Capture
   ↓
YOLOv11n Inference
   ↓
Object Detection
   ↓
Filter Person Class
   ↓
Count People
   ↓
Draw Bounding Boxes
   ↓
Threshold Comparison
   ↓
Email Alert if Required
   ↓
Flask Video Stream
```

---

# 📊 Example

Suppose:

```python
THRESHOLD = 1
```

and the camera detects:

```text
Person 1
Person 2
```

The system calculates:

```text
People Count = 2
Threshold = 1
```

Therefore:

```text
2 > 1
```

Result:

```text
🚨 THRESHOLD EXCEEDED
```

and an email notification is sent to the configured administrator.

---

# 💡 Use Cases

The system can be adapted for:

* 🏢 Office occupancy monitoring
* 🏫 Classroom monitoring
* 🏭 Industrial safety monitoring
* 🛒 Store occupancy monitoring
* 🚪 Restricted-area monitoring
* 🏥 Hospital area monitoring
* 🎫 Event and venue monitoring
* 🏢 Building capacity monitoring

---

# 📌 Key Project Highlights

### Computer Vision

* Real-time object detection
* Person classification
* Bounding-box detection
* Live video processing

### Backend Development

* Flask web application
* HTTP endpoints
* MJPEG video streaming
* JSON API

### Automation

* Threshold-based monitoring
* Automated email notification
* Real-time status reporting


### Skills Demonstrated

`Python` `YOLOv11` `OpenCV` `Flask` `Computer Vision` `REST API` `SMTP` `Real-Time Video Processing`

