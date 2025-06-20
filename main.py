import os
import sys

import cv2
import numpy as np
from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QColorDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.original_image = None
        self.current_image_path = None
        self.border_color = [255, 255, 255]  # Default white border

        # Border values
        self.top_border = 0
        self.bottom_border = 0
        self.left_border = 0
        self.right_border = 0

        self.initializeUI()

    def initializeUI(self):
        self.setWindowTitle("Photon")
        self.setGeometry(200, 200, 1200, 800)

        # Center the window on the screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 1200) // 2
        y = (screen.height() - 800) // 2
        self.setGeometry(x, y, 1200, 800)

        main_layout = QHBoxLayout()

        # Left panel for controls
        left_panel = QVBoxLayout()

        # Image picker button
        self.pick_button = QPushButton("Pick an Image", self)
        self.pick_button.setStyleSheet(
            """
            QPushButton {
                font-size: 16px;
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        self.pick_button.clicked.connect(self.pickImage)

        # Download button
        self.download_button = QPushButton("Download Image", self)
        self.download_button.setStyleSheet(
            """
            QPushButton {
                font-size: 16px;
                padding: 10px 20px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
            """
        )
        self.download_button.clicked.connect(self.downloadImage)
        self.download_button.setEnabled(False)  # Disabled until image is loaded

        # Border color controls
        color_group = QGroupBox("Border Color")
        color_layout = QHBoxLayout()

        self.border_color_label = QLabel("Color:")
        self.border_color_label.setStyleSheet("font-weight: bold; margin: 5px;")

        self.color_button = QPushButton("")
        self.color_button.setFixedSize(40, 30)
        self.color_button.setStyleSheet(
            """
            QPushButton {
                background-color: white;
                border: 2px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                border: 2px solid #999;
            }
        """
        )
        self.color_button.clicked.connect(self.pickColor)

        self.color_name_label = QLabel("White")
        self.color_name_label.setStyleSheet("margin: 5px;")

        color_layout.addWidget(self.border_color_label)
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_name_label)
        color_layout.addStretch()
        color_group.setLayout(color_layout)

        # Border controls
        border_group = QGroupBox("Border Controls")
        border_layout = QVBoxLayout()

        # Top border slider
        top_layout = QHBoxLayout()
        top_label = QLabel("Top:")
        top_label.setFixedWidth(40)
        self.top_slider = QSlider(Qt.Orientation.Horizontal)
        self.top_slider.setRange(0, 500)
        self.top_slider.setValue(0)
        self.top_slider.valueChanged.connect(self.onSliderChanged)
        self.top_text_box = QLineEdit("0")
        self.top_text_box.setFixedWidth(50)
        self.top_text_box.textChanged.connect(self.onTextChanged)

        top_layout.addWidget(top_label)
        top_layout.addWidget(self.top_slider)
        top_layout.addWidget(self.top_text_box)

        # Bottom border slider
        bottom_layout = QHBoxLayout()
        bottom_label = QLabel("Bottom:")
        bottom_label.setFixedWidth(40)
        self.bottom_slider = QSlider(Qt.Orientation.Horizontal)
        self.bottom_slider.setRange(0, 1000)
        self.bottom_slider.setValue(0)
        self.bottom_slider.valueChanged.connect(self.onSliderChanged)
        self.bottom_text_box = QLineEdit("0")
        self.bottom_text_box.setFixedWidth(50)
        self.bottom_text_box.textChanged.connect(self.onTextChanged)

        bottom_layout.addWidget(bottom_label)
        bottom_layout.addWidget(self.bottom_slider)
        bottom_layout.addWidget(self.bottom_text_box)

        # Left border slider
        left_layout = QHBoxLayout()
        left_label = QLabel("Left:")
        left_label.setFixedWidth(40)
        self.left_slider = QSlider(Qt.Orientation.Horizontal)
        self.left_slider.setRange(0, 500)
        self.left_slider.setValue(0)
        self.left_slider.valueChanged.connect(self.onSliderChanged)
        self.left_text_box = QLineEdit("0")
        self.left_text_box.setFixedWidth(50)
        self.left_text_box.textChanged.connect(self.onTextChanged)

        left_layout.addWidget(left_label)
        left_layout.addWidget(self.left_slider)
        left_layout.addWidget(self.left_text_box)

        # Right border slider
        right_layout = QHBoxLayout()
        right_label = QLabel("Right:")
        right_label.setFixedWidth(40)
        self.right_slider = QSlider(Qt.Orientation.Horizontal)
        self.right_slider.setRange(0, 500)
        self.right_slider.setValue(0)
        self.right_slider.valueChanged.connect(self.onSliderChanged)
        self.right_text_box = QLineEdit("0")
        self.right_text_box.setFixedWidth(50)
        self.right_text_box.textChanged.connect(self.onTextChanged)

        right_layout.addWidget(right_label)
        right_layout.addWidget(self.right_slider)
        right_layout.addWidget(self.right_text_box)

        border_layout.addLayout(top_layout)
        border_layout.addLayout(bottom_layout)
        border_layout.addLayout(left_layout)
        border_layout.addLayout(right_layout)
        border_group.setLayout(border_layout)

        # Add controls to left panel
        left_panel.addWidget(self.pick_button)
        left_panel.addWidget(self.download_button)
        left_panel.addWidget(color_group)
        left_panel.addWidget(border_group)
        left_panel.addStretch()

        # Right panel for image display
        right_panel = QVBoxLayout()

        # Image display widget with fixed size
        self.image_widget = QLabel()
        self.image_widget.setFixedSize(600, 400)  # Fixed display size
        self.image_widget.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 5px;
                background-color: transparent;
            }
        """
        )
        self.image_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_panel.addWidget(self.image_widget)

        # Add panels to main layout
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)

        self.setLayout(main_layout)

    def onSliderChanged(self):
        # Update border values from sliders
        self.top_border = self.top_slider.value()
        self.bottom_border = self.bottom_slider.value()
        self.left_border = self.left_slider.value()
        self.right_border = self.right_slider.value()

        # Update text boxes
        self.top_text_box.setText(str(self.top_border))
        self.bottom_text_box.setText(str(self.bottom_border))
        self.left_text_box.setText(str(self.left_border))
        self.right_text_box.setText(str(self.right_border))

        # Update the image display
        self.updateBorder()

    def onTextChanged(self):
        try:
            # Update border values from text boxes
            self.top_border = int(self.top_text_box.text() or 0)
            self.bottom_border = int(self.bottom_text_box.text() or 0)
            self.left_border = int(self.left_text_box.text() or 0)
            self.right_border = int(self.right_text_box.text() or 0)

            # Clamp values to slider ranges
            self.top_border = max(0, min(self.top_border, self.top_slider.maximum()))
            self.bottom_border = max(
                0, min(self.bottom_border, self.bottom_slider.maximum())
            )
            self.left_border = max(0, min(self.left_border, self.left_slider.maximum()))
            self.right_border = max(
                0, min(self.right_border, self.right_slider.maximum())
            )

            # Update sliders
            self.top_slider.setValue(self.top_border)
            self.bottom_slider.setValue(self.bottom_border)
            self.left_slider.setValue(self.left_border)
            self.right_slider.setValue(self.right_border)

            # Update the image display
            self.updateBorder()
        except ValueError:
            # If invalid input, ignore the change
            pass

    def pickColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            # Convert Qt color to BGR for OpenCV
            self.border_color = [color.blue(), color.green(), color.red()]

            # Update color button appearance
            self.color_button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {color.name()};
                    border: 2px solid #ccc;
                    border-radius: 5px;
                }}
                QPushButton:hover {{
                    border: 2px solid #999;
                }}
            """
            )

            # Update color name label
            self.color_name_label.setText(color.name())

            # Update the border if an image is loaded
            self.updateBorder()

    def pickImage(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select an Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            self.loadImage(file_path)

    def loadImage(self, image_path):
        # Load image with OpenCV
        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            return

        self.current_image_path = image_path
        self.download_button.setEnabled(True)  # Enable download button
        self.updateBorder()

    def updateBorder(self):
        if self.original_image is None:
            return

        # Apply border using OpenCV to the original full-resolution image
        bordered_image = cv2.copyMakeBorder(
            self.original_image,
            self.top_border,
            self.bottom_border,
            self.left_border,
            self.right_border,
            cv2.BORDER_CONSTANT,
            value=self.border_color,
        )

        # Convert BGR to RGB for Qt
        rgb_image = cv2.cvtColor(bordered_image, cv2.COLOR_BGR2RGB)

        # Convert to QImage
        height, width, channel = rgb_image.shape
        bytes_per_line = 3 * width
        q_image = QImage(
            rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888
        )

        # Convert to QPixmap
        pixmap = QPixmap.fromImage(q_image)

        # Scale the image to fit the widget while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.image_widget.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.image_widget.setPixmap(scaled_pixmap)

    def downloadImage(self):
        if self.original_image is None:
            return

        # Apply border using OpenCV to the original full-resolution image
        bordered_image = cv2.copyMakeBorder(
            self.original_image,
            self.top_border,
            self.bottom_border,
            self.left_border,
            self.right_border,
            cv2.BORDER_CONSTANT,
            value=self.border_color,  # Use selected border color
        )

        # Save the full-resolution image with borders
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            cv2.imwrite(file_path, bordered_image)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    sys.exit(app.exec())
