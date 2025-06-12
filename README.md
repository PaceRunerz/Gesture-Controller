# AI Gesture Controller with Interactive Screen Overlay

This project is a sophisticated, real-time gesture control application built with Python. It allows you to control your computer, particularly media applications like YouTube, using hand gestures captured through your webcam. It also features a transparent, interactive overlay with drawing and screenshot capabilities.

---

## Features 

- **Gesture Controls**:
  - ✊ Fist: Play/Pause
  - ✌️ Peace Sign: Drawing mode
  - 👍 Thumbs Up: Volume Up
  - 👎 Thumbs Down: Volume Down

- **AI Screenshot Tool**:
  - Capture any screen region
  - Copy to clipboard for AI analysis
  - Save with timestamp

- **Drawing Overlay**:
  - Annotate directly on screen
  - Customizable pen color/size
 
---

Gesture demo: ()

---

## ✨ Core Features

* **Real-Time Gesture Recognition**: Utilizes Google's MediaPipe to accurately detect hand landmarks and recognize gestures in real-time.
* **System & Media Control**: Control essential functions like play/pause and volume adjustment with simple hand movements.
* **Interactive Overlay UI**: A transparent, always-on-top window built with PyQt5 provides an interface without obstructing your view.
* **On-Screen Drawing**: Activate a drawing mode with a gesture and annotate anything on your screen.
* **Advanced Screenshot Tool**: Capture your entire screen, including any on-screen drawings, and save it to both a file and your clipboard.
* **Instant Visual Feedback**: On-screen notifications confirm which gesture has been recognized and what action has been taken.

---

## 🛠️ Tech Stack

* **Computer Vision**: OpenCV
* **Hand Tracking**: MediaPipe
* **GUI & Overlay**: PyQt5
* **System Automation**: PyAutoGUI
* **Numerical Operations**: NumPy
* **macOS Integration**: AppKit (for clipboard access)

---

## ⚠️ Platform Compatibility

This application is currently designed and optimized for **macOS**.

Key functionalities, such as system hotkeys (`pyautogui.hotkey('option', 'up')`) and clipboard integration (`AppKit.NSPasteboard`), are specific to the macOS environment. Adapting it for Windows or Linux would require modifying these parts of the code.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.7+
* A webcam connected to your computer.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/your-repo-name.git](https://github.com/YOUR_USERNAME/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *On Windows, use `venv\Scripts\activate`*

3.  **Install the required dependencies:**
    The project uses several powerful libraries. Install them using the provided `requirements.txt` file (you will need to create this file).
    ```bash
    pip install opencv-python mediapipe pyautogui numpy pyqt5
    ```
    For macOS, `pyobjc` is needed for `AppKit`:
    ```bash
    pip install pyobjc
    ```

---


## 🎨 Overlay Controls

The overlay provides buttons for manual control:

* **Screenshot**: Captures the entire screen, including your drawings. Saves a timestamped `.png` file and copies the image to the clipboard.
* **Draw**: Manually toggles the drawing mode. The button turns green when active.
* **Clear**: Erases all drawings from the overlay.

When in drawing mode, simply click and drag your mouse on the screen to draw.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` file for more information.

