#!/usr/bin/env python3
"""
Harvey Local Audio - Desktop Management Application
Easy-to-use GUI for managing the audio server
"""

import sys
import os
import subprocess
import threading
import time
import yaml
import psutil
import pyperclip
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QComboBox,
    QSlider, QLineEdit, QTabWidget, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QPalette


class ServerManager(QObject):
    """Manages the backend server process"""

    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str, bool)  # status, is_running

    def __init__(self, backend_path: Path):
        super().__init__()
        self.backend_path = backend_path
        self.process: Optional[subprocess.Popen] = None
        self.running = False

    def start_server(self):
        """Start the backend server"""
        if self.running:
            self.log_signal.emit("Server is already running")
            return

        try:
            # Start server process
            python_exe = sys.executable
            main_script = self.backend_path / "main.py"

            self.log_signal.emit(f"Starting server: {main_script}")

            self.process = subprocess.Popen(
                [python_exe, str(main_script)],
                cwd=str(self.backend_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            self.running = True
            self.status_signal.emit("Running", True)
            self.log_signal.emit("Server started successfully")

            # Start log monitoring thread
            threading.Thread(target=self._monitor_output, daemon=True).start()

        except Exception as e:
            self.log_signal.emit(f"Failed to start server: {e}")
            self.status_signal.emit("Stopped", False)

    def stop_server(self):
        """Stop the backend server"""
        if not self.running:
            self.log_signal.emit("Server is not running")
            return

        try:
            self.log_signal.emit("Stopping server...")

            if self.process:
                # Terminate process
                self.process.terminate()

                # Wait for clean shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.log_signal.emit("Force killing server...")
                    self.process.kill()

                self.process = None

            self.running = False
            self.status_signal.emit("Stopped", False)
            self.log_signal.emit("Server stopped")

        except Exception as e:
            self.log_signal.emit(f"Error stopping server: {e}")

    def _monitor_output(self):
        """Monitor server output logs"""
        if not self.process:
            return

        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log_signal.emit(line.rstrip())

                if not self.running:
                    break

        except Exception as e:
            self.log_signal.emit(f"Log monitoring error: {e}")

    def is_running(self) -> bool:
        """Check if server is running"""
        if self.process:
            return self.process.poll() is None
        return False


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Harvey Local Audio - Server Manager")
        self.setMinimumSize(900, 700)

        # Paths
        self.app_dir = Path(__file__).parent
        self.backend_dir = self.app_dir.parent / "backend"
        self.config_path = self.backend_dir / "config.yaml"
        self.api_key_path = self.backend_dir / ".api_key"

        # Server manager
        self.server_manager = ServerManager(self.backend_dir)
        self.server_manager.log_signal.connect(self.append_log)
        self.server_manager.status_signal.connect(self.update_status)

        # Load config
        self.config = self.load_config()

        # Setup UI
        self.setup_ui()

        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_server_status)
        self.status_timer.start(2000)  # Check every 2 seconds

    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Header
        header = QLabel("Harvey Local Audio Server")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Server control section
        control_group = self.create_control_section()
        layout.addWidget(control_group)

        # Tabs
        tabs = QTabWidget()

        # Connection tab
        connection_tab = self.create_connection_tab()
        tabs.addTab(connection_tab, "Connection Info")

        # Configuration tab
        config_tab = self.create_config_tab()
        tabs.addTab(config_tab, "Voice Configuration")

        # Logs tab
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, "Server Logs")

        # Instructions tab
        instructions_tab = self.create_instructions_tab()
        tabs.addTab(instructions_tab, "How to Connect")

        layout.addWidget(tabs)

    def create_control_section(self) -> QGroupBox:
        """Create server control section"""
        group = QGroupBox("Server Control")

        layout = QVBoxLayout()

        # Status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))

        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Server")
        self.start_btn.clicked.connect(self.start_server)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-size: 14px;")
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Server")
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px; font-size: 14px;")
        button_layout.addWidget(self.stop_btn)

        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def create_connection_tab(self) -> QWidget:
        """Create connection information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # WebSocket URL
        url_group = QGroupBox("WebSocket URL")
        url_layout = QVBoxLayout()

        host = self.config['server']['host']
        if host == "0.0.0.0":
            host = "localhost"

        port = self.config['server']['port']
        ws_url = f"ws://{host}:{port}/ws/audio"

        self.url_input = QLineEdit(ws_url)
        self.url_input.setReadOnly(True)
        self.url_input.setStyleSheet("font-family: monospace; font-size: 12px; padding: 8px;")
        url_layout.addWidget(self.url_input)

        copy_url_btn = QPushButton("Copy URL")
        copy_url_btn.clicked.connect(lambda: self.copy_to_clipboard(ws_url))
        url_layout.addWidget(copy_url_btn)

        url_group.setLayout(url_layout)
        layout.addWidget(url_group)

        # API Key
        api_key_group = QGroupBox("API Key")
        api_key_layout = QVBoxLayout()

        api_key = self.get_api_key()

        self.api_key_input = QLineEdit(api_key)
        self.api_key_input.setReadOnly(True)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setStyleSheet("font-family: monospace; font-size: 12px; padding: 8px;")
        api_key_layout.addWidget(self.api_key_input)

        key_buttons = QHBoxLayout()

        show_key_btn = QPushButton("Show/Hide Key")
        show_key_btn.clicked.connect(self.toggle_api_key_visibility)
        key_buttons.addWidget(show_key_btn)

        copy_key_btn = QPushButton("Copy Key")
        copy_key_btn.clicked.connect(lambda: self.copy_to_clipboard(api_key))
        key_buttons.addWidget(copy_key_btn)

        regenerate_key_btn = QPushButton("Regenerate Key")
        regenerate_key_btn.clicked.connect(self.regenerate_api_key)
        key_buttons.addWidget(regenerate_key_btn)

        api_key_layout.addLayout(key_buttons)

        api_key_group.setLayout(api_key_layout)
        layout.addWidget(api_key_group)

        # Server info
        info_group = QGroupBox("Server Information")
        info_layout = QVBoxLayout()

        info_text = f"""
        <b>LLM Model:</b> {self.config['llm']['model']}<br>
        <b>STT Model:</b> Whisper {self.config['stt']['model']}<br>
        <b>TTS Voice:</b> {self.config['tts']['voice']}<br>
        <b>Sample Rate:</b> {self.config['audio']['sample_rate']} Hz
        """

        info_label = QLabel(info_text)
        info_label.setStyleSheet("padding: 10px;")
        info_layout.addWidget(info_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()

        return widget

    def create_config_tab(self) -> QWidget:
        """Create voice configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Voice selection
        voice_group = QGroupBox("Voice Settings")
        voice_layout = QVBoxLayout()

        voice_layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems([
            "en_US-lessac-medium",
            "en_US-amy-medium",
            "en_US-danny-low",
            "en_US-kathleen-low",
            "en_US-ljspeech-medium"
        ])
        self.voice_combo.setCurrentText(self.config['tts']['voice'])
        voice_layout.addWidget(self.voice_combo)

        voice_layout.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(int(self.config['tts']['speed'] * 100))
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.setTickInterval(10)

        self.speed_label = QLabel(f"{self.config['tts']['speed']:.2f}x")
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v/100:.2f}x")
        )

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        voice_layout.addLayout(speed_layout)

        save_voice_btn = QPushButton("Save Voice Settings")
        save_voice_btn.clicked.connect(self.save_voice_config)
        voice_layout.addWidget(save_voice_btn)

        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

        # LLM settings
        llm_group = QGroupBox("LLM Settings")
        llm_layout = QVBoxLayout()

        llm_layout.addWidget(QLabel("Temperature:"))
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(0)
        self.temp_slider.setMaximum(200)
        self.temp_slider.setValue(int(self.config['llm']['temperature'] * 100))

        self.temp_label = QLabel(f"{self.config['llm']['temperature']:.2f}")
        self.temp_slider.valueChanged.connect(
            lambda v: self.temp_label.setText(f"{v/100:.2f}")
        )

        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_label)
        llm_layout.addLayout(temp_layout)

        llm_layout.addWidget(QLabel("System Prompt:"))
        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setPlainText(self.config['conversation']['system_prompt'])
        self.system_prompt_input.setMaximumHeight(100)
        llm_layout.addWidget(self.system_prompt_input)

        save_llm_btn = QPushButton("Save LLM Settings")
        save_llm_btn.clicked.connect(self.save_llm_config)
        llm_layout.addWidget(save_llm_btn)

        llm_group.setLayout(llm_layout)
        layout.addWidget(llm_group)

        layout.addStretch()

        return widget

    def create_logs_tab(self) -> QWidget:
        """Create server logs tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 11px; background-color: #1e1e1e; color: #d4d4d4;")
        layout.addWidget(self.log_text)

        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_btn)

        return widget

    def create_instructions_tab(self) -> QWidget:
        """Create connection instructions tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setHtml("""
        <h2>How to Connect to Harvey Local Audio</h2>

        <h3>JavaScript/Node.js Example</h3>
        <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8765/ws/audio', {
  headers: {
    'X-API-Key': 'your-api-key-here'
  }
});

ws.on('open', () => {
  console.log('Connected to Harvey Audio');

  // Send audio data
  const audioBuffer = fs.readFileSync('audio.wav');
  ws.send(JSON.stringify({
    type: 'audio',
    data: audioBuffer.toString('base64'),
    format: 'wav',
    sample_rate: 16000
  }));
});

ws.on('message', (data) => {
  const response = JSON.parse(data);
  console.log('Response:', response.text);
  // Handle response.audio
});
        </pre>

        <h3>Python Example</h3>
        <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
import websockets
import asyncio
import json
import base64

async def connect():
    uri = "ws://localhost:8765/ws/audio"
    headers = {"X-API-Key": "your-api-key-here"}

    async with websockets.connect(uri, extra_headers=headers) as ws:
        # Send audio
        with open("audio.wav", "rb") as f:
            audio_data = base64.b64encode(f.read()).decode()

        await ws.send(json.dumps({
            "type": "audio",
            "data": audio_data,
            "format": "wav",
            "sample_rate": 16000
        }))

        # Receive response
        response = json.loads(await ws.recv())
        print(f"Response: {response['text']}")

asyncio.run(connect())
        </pre>

        <h3>Message Format</h3>
        <p><b>Send Audio:</b></p>
        <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
{
  "type": "audio",
  "data": "&lt;base64-encoded-audio&gt;",
  "format": "wav",
  "sample_rate": 16000
}
        </pre>

        <p><b>Receive Response:</b></p>
        <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
{
  "type": "audio_response",
  "transcription": "User's speech transcription",
  "text": "AI response text",
  "audio": "&lt;base64-encoded-audio&gt;",
  "latency_ms": 350
}
        </pre>
        """)

        layout.addWidget(instructions)

        return widget

    def load_config(self) -> dict:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load config: {e}")
            return {}

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save config: {e}")

    def get_api_key(self) -> str:
        """Get API key"""
        try:
            if self.api_key_path.exists():
                with open(self.api_key_path, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass

        return "Not generated yet - start server to generate"

    def start_server(self):
        """Start the server"""
        self.server_manager.start_server()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_server(self):
        """Stop the server"""
        self.server_manager.stop_server()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def append_log(self, message: str):
        """Append message to log"""
        self.log_text.append(message)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_status(self, status: str, is_running: bool):
        """Update server status"""
        self.status_label.setText(status)

        if is_running:
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.status_label.setStyleSheet("font-weight: bold; color: red;")

    def check_server_status(self):
        """Check if server is still running"""
        if self.server_manager.is_running():
            if not self.stop_btn.isEnabled():
                self.update_status("Running", True)
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
        else:
            if self.stop_btn.isEnabled():
                self.update_status("Stopped", False)
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)

    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        pyperclip.copy(text)
        QMessageBox.information(self, "Copied", "Copied to clipboard!")

    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def regenerate_api_key(self):
        """Regenerate API key"""
        reply = QMessageBox.question(
            self,
            "Regenerate API Key",
            "This will invalidate the current API key. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            import secrets

            new_key = secrets.token_urlsafe(32)

            with open(self.api_key_path, 'w') as f:
                f.write(new_key)

            self.api_key_input.setText(new_key)
            QMessageBox.information(self, "Success", "API key regenerated!")

    def save_voice_config(self):
        """Save voice configuration"""
        self.config['tts']['voice'] = self.voice_combo.currentText()
        self.config['tts']['speed'] = self.speed_slider.value() / 100

        self.save_config()
        QMessageBox.information(self, "Success", "Voice configuration saved!")

    def save_llm_config(self):
        """Save LLM configuration"""
        self.config['llm']['temperature'] = self.temp_slider.value() / 100
        self.config['conversation']['system_prompt'] = self.system_prompt_input.toPlainText()

        self.save_config()
        QMessageBox.information(self, "Success", "LLM configuration saved!")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
