import logging
import os
from PyQt5.QtCore import Qt, QUrl, QTime, QSize, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSlider, QComboBox, QMessageBox, QStyle)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from src.ui.visualization import Visualization
import plotly.graph_objects as go
import numpy as np
from scipy.io import wavfile

class AudioWidget(QWidget):
    audio_loaded_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.audio_loaded = False
        self.current_recording_id = None
        self.player = QMediaPlayer(self)
        self.player.stateChanged.connect(self.on_state_changed)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.setNotifyInterval(50)

        self.visualization = Visualization()

        main_layout = QVBoxLayout(self)

        self.recording_combo_label = QLabel("Select Recording to Play:", self)
        main_layout.addWidget(self.recording_combo_label)

        self.recording_combo = QComboBox()
        self.recording_combo.currentIndexChanged.connect(self.on_recording_selected)
        main_layout.addWidget(self.recording_combo)

        controls_layout = QHBoxLayout()

        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_pause_btn.setIconSize(QSize(12, 12))
        self.play_pause_btn.setFixedSize(24, 24)
        self.play_pause_btn.setFlat(True)
        self.play_pause_btn.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_pause_btn)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.seek)
        controls_layout.addWidget(self.position_slider)

        self.time_label = QLabel("00:00.000 / 00:00.000", self)
        controls_layout.addWidget(self.time_label)

        main_layout.addLayout(controls_layout)

        self.waveform_view = QWebEngineView()
        main_layout.addWidget(self.waveform_view)

    def update_recording_list(self, recordings):
        self.recording_combo.clear()
        available_recordings = [r for r in recordings if os.path.exists(os.path.join('data', f"{r}.wav"))]

        if available_recordings:
            self.recording_combo.addItems(available_recordings)
            self.load_audio_for_current_selection()

        else:
            self.recording_combo.addItem("No recordings available")
            self.clear()

    def on_recording_selected(self):
        self.load_audio_for_current_selection()

    def clear(self):
        self.player.stop()
        self.audio_loaded = False
        self.current_recording_id = None
        self.position_slider.setValue(0)
        self.time_label.setText("00:00.000 / 00:00.000")
        self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.waveform_view.setHtml("")

    def load_audio_for_current_selection(self):
        if self.recording_combo.count() == 0:
            self.clear()
            return

        rec_id = self.recording_combo.currentText()
        self.current_recording_id = rec_id
        if rec_id == "No recordings available":
            self.clear()
            return

        audio_path = os.path.join('data', f"{rec_id}.wav")
        if os.path.exists(audio_path):
            self.load_audio(audio_path)
        else:
            self.show_message("No audio file found for this recording.")
            self.clear()

    def load_audio(self, audio_file_path):
        """Load audio player and waveform visualization"""
        try:
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_file_path)))
            self.player.stop()
            self.audio_loaded = True

            sample_rate, data = wavfile.read(audio_file_path)

            # Convert stereo to mono
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)

            # Downsample the data to max 10000 points
            target_points = 10000
            if len(data) > target_points:
                step = len(data) // target_points
                data = data[::step]
                time = np.linspace(0, len(data) / sample_rate, len(data))
            else:
                time = np.arange(len(data)) / sample_rate

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=time,
                y=data,
                mode='lines',
                name='waveform',
                line=dict(color='#1f77b4', width=1)
            ))

            fig.update_layout(
                showlegend=False,
                margin=dict(l=40, r=20, t=20, b=40),
                height=150,
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(
                    showgrid=True,
                    gridcolor='#eee',
                    zeroline=False
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#eee',
                    zeroline=False
                )
            )

            html = fig.to_html(
                include_plotlyjs='cdn',
                config={'displayModeBar': False}
            )

            self.waveform_view.setHtml(html)
            self.waveform_view.show()

            if self.current_recording_id:
                self.audio_loaded_signal.emit(self.current_recording_id)

        except Exception as e:
            logging.error(f"Failed to load audio or create waveform: {e}")
            QMessageBox.critical(self, 'Error', f"Failed to load audio: {str(e)}")
            self.clear()


    def show_message(self, message):
        QMessageBox.warning(self, "Audio Error", message)

    def toggle_playback(self):
        if not self.audio_loaded:
            self.show_message("No audio loaded.")
            return

        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def on_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def on_position_changed(self, position):
        self.position_slider.setValue(position)
        self.update_time_label()

    def on_duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_time_label()

    def seek(self, position):
        self.player.setPosition(position)

    def update_time_label(self):
        duration = self.player.duration()
        position = self.player.position()

        def format_milliseconds(ms):
            t = QTime(0, 0, 0)
            t = t.addMSecs(ms)
            return t.toString("mm:ss.zzz")

        current_time_str = format_milliseconds(position)
        total_time_str = format_milliseconds(duration) if duration > 0 else "00:00.000"
        self.time_label.setText(f"{current_time_str} / {total_time_str}")


    def update_waveform_visualization(self, audio_path):
        if not os.path.exists(audio_path):
            return

        try:
            fig = self.visualization.plot_audio_waveform(audio_path)
            html = fig.to_html(include_plotlyjs='cdn')
            self.waveform_view.setHtml(html)
            self.waveform_view.show()
        except Exception as e:
            logging.error(f"Failed to plot waveform: {e}")
            QMessageBox.critical(self, 'Error', f"Failed to plot waveform: {str(e)}")

