import os
import wave
import logging
import numpy as np

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox, QStyle
)
import pyqtgraph as pg


class AudioWidget(QWidget):
    audio_loaded_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFocusPolicy(Qt.StrongFocus)

        self.audio_loaded = False
        self.current_recording_id = None

        self.player = QMediaPlayer(self)
        self.player.stateChanged.connect(self.on_state_changed)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.setNotifyInterval(50)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        top_layout = QHBoxLayout()
        self.recording_label = QLabel("Select Recording:")
        self.recording_combo = QComboBox()
        self.recording_combo.currentIndexChanged.connect(self.on_recording_selected)

        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setFixedSize(30, 30)
        self.play_pause_btn.setIconSize(QSize(20, 20))
        self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_pause_btn.clicked.connect(self.toggle_playback)

        top_layout.addWidget(self.recording_label)
        top_layout.addWidget(self.recording_combo)
        top_layout.addStretch()
        top_layout.addWidget(self.play_pause_btn)
        main_layout.addLayout(top_layout)

        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setMouseEnabled(x=True, y=False)

        # Configure grid and axis styles
        plot_item = self.plot_widget.getPlotItem()
        plot_item.showGrid(x=True, y=True, alpha=0.3)

        transparent_pen = pg.mkPen(color=(0, 0, 0, 0))
        plot_item.getAxis('bottom').setPen(transparent_pen)
        plot_item.getAxis('left').setPen(transparent_pen)

        font = pg.QtGui.QFont("Arial", 10)
        plot_item.getAxis('bottom').setStyle(tickFont=font)
        plot_item.getAxis('left').setStyle(tickFont=font)

        main_layout.addWidget(self.plot_widget)

        self.waveform_curve = None
        self.playhead_line = None
        self.wave_y_data = None
        self.plot_widget.scene().sigMouseClicked.connect(self.on_plot_clicked)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.toggle_playback()
            event.accept()
        else:
            super().keyPressEvent(event)

    def update_recording_list(self, recordings):
        """Update the recording selection combo box."""
        self.recording_combo.clear()
        available = [r for r in recordings if os.path.exists(os.path.join('data', f"{r}.wav"))]
        if available:
            self.recording_combo.addItems(available)
            self.load_audio_for_current_selection()
        else:
            self.recording_combo.addItem("No recordings available")
            self.clear()

    def on_recording_selected(self):
        self.load_audio_for_current_selection()

    def clear(self):
        """Reset everything."""
        self.player.stop()
        self.audio_loaded = False
        self.current_recording_id = None
        self.plot_widget.clear()
        self.waveform_curve = None
        self.playhead_line = None
        self.wave_y_data = None

    def load_audio_for_current_selection(self):
        """Load the selected .wav file."""
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
            self.show_message(f"No audio file found for {rec_id}")
            self.clear()

    def load_audio(self, audio_file_path):
        """Load the .wav file and extract waveform data."""
        try:
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_file_path)))
            self.player.stop()
            self.audio_loaded = True

            with wave.open(audio_file_path, 'rb') as wf:
                n_channels = wf.getnchannels()
                n_frames = wf.getnframes()
                data = wf.readframes(n_frames)

            samples = np.frombuffer(data, dtype=np.int16)
            if n_channels > 1:  # Stereo: average channels
                samples = samples.reshape(-1, n_channels).mean(axis=1).astype(np.int16)

            self.wave_y_data = samples

        except Exception as e:
            logging.error(f"Failed to load audio: {e}")
            QMessageBox.critical(self, 'Error', f"Failed to load audio:\n{str(e)}")
            self.clear()

    def show_message(self, msg):
        QMessageBox.warning(self, "Audio Error", msg)

    def on_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def on_position_changed(self, pos_ms):
        if self.playhead_line:
            self.playhead_line.setPos(pos_ms / 1000.0)

    def on_duration_changed(self, duration_ms):
        if not self.audio_loaded or self.wave_y_data is None:
            return

        duration_s = duration_ms / 1000.0
        wave_y = self.wave_y_data

        max_points = 20000
        step = max(1, len(wave_y) // max_points)
        wave_y_down = wave_y[::step]
        wave_x_down = np.linspace(0, duration_s, len(wave_y_down))

        self.plot_widget.clear()

        pen_wave = pg.mkPen(color='#1f77b4', width=1)
        self.waveform_curve = self.plot_widget.plot(wave_x_down, wave_y_down, pen=pen_wave)

        pen_playhead = pg.mkPen(color='r', width=2)
        self.playhead_line = pg.InfiniteLine(
            pos=0, angle=90, pen=pen_playhead, movable=False
        )
        self.plot_widget.addItem(self.playhead_line)

    def toggle_playback(self):
        if not self.audio_loaded:
            self.show_message("No audio loaded.")
            return
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def on_plot_clicked(self, mouse_event):
        """Seek to the clicked position on the waveform."""
        if not self.audio_loaded or self.playhead_line is None:
            return
        pos = mouse_event.scenePos()
        mp = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        x_val = mp.x()

        duration_ms = self.player.duration()
        if duration_ms <= 0:
            return
        duration_s = duration_ms / 1000.0

        if 0 <= x_val <= duration_s:
            self.player.setPosition(int(x_val * 1000))
