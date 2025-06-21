import json
import os
import sys

import cv2
import numpy as np
from PyQt6.QtCore import QPoint, QRect, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
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

from border import create_border_group
from crop import create_crop_group


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

        # Crop values
        self.crop_mode = False
        self.crop_start = None
        self.crop_end = None
        self.crop_rect = None
        self.cropped_image = None

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
        self.pick_button = QPushButton("Pick Image", self)
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
        border_group = create_border_group(self)

        # Crop controls
        crop_group = create_crop_group(self)

        # Add controls to left panel
        # Create horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.pick_button)
        button_layout.addWidget(self.download_button)

        left_panel.addLayout(button_layout)
        left_panel.addWidget(color_group)
        left_panel.addWidget(border_group)
        left_panel.addWidget(crop_group)
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

        # Enable mouse events for crop selection
        self.image_widget.setMouseTracking(True)
        self.image_widget.mousePressEvent = self.imageMousePressEvent
        self.image_widget.mouseMoveEvent = self.imageMouseMoveEvent
        self.image_widget.mouseReleaseEvent = self.imageMouseReleaseEvent

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
        self.crop_button.setEnabled(True)  # Enable crop button
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

        # Convert BGR to RGBA for Qt to support transparency
        rgba_image = cv2.cvtColor(bordered_image, cv2.COLOR_BGR2RGBA)

        # Convert to QImage
        height, width, channel = rgba_image.shape
        bytes_per_line = 4 * width
        q_image = QImage(
            rgba_image.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGBA8888,
        )

        # Convert to QPixmap
        pixmap = QPixmap.fromImage(q_image)

        # Scale the image to fit the widget while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.image_widget.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Draw crop selection overlay if in crop mode
        if self.crop_mode and self.crop_rect:
            painter = QPainter(scaled_pixmap)

            # Create a semi-transparent overlay for the area outside the crop
            path = QPainterPath()
            path.addRect(QRectF(scaled_pixmap.rect()))
            path.addRect(QRectF(self.crop_rect))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 100))  # Semi-transparent black
            painter.drawPath(path)

            # Draw the yellow border for the crop rectangle
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 0), 2))  # Yellow border
            painter.drawRect(self.crop_rect)

            painter.end()

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

    def saveBorderSettings(self):
        settings = {
            "top_border": self.top_border,
            "bottom_border": self.bottom_border,
            "left_border": self.left_border,
            "right_border": self.right_border,
            "border_color": self.border_color,
        }

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Border Settings",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            with open(file_path, "w") as f:
                json.dump(settings, f, indent=4)

    def loadBorderSettings(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Border Settings",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            with open(file_path, "r") as f:
                settings = json.load(f)

            # Update border values
            self.top_border = settings.get("top_border", 0)
            self.bottom_border = settings.get("bottom_border", 0)
            self.left_border = settings.get("left_border", 0)
            self.right_border = settings.get("right_border", 0)
            self.border_color = settings.get("border_color", [255, 255, 255])

            # Update UI
            self.top_slider.setValue(self.top_border)
            self.bottom_slider.setValue(self.bottom_border)
            self.left_slider.setValue(self.left_border)
            self.right_slider.setValue(self.right_border)

            self.top_text_box.setText(str(self.top_border))
            self.bottom_text_box.setText(str(self.bottom_border))
            self.left_text_box.setText(str(self.left_border))
            self.right_text_box.setText(str(self.right_border))

            # Update color
            b, g, r = self.border_color
            color = QColor(r, g, b)
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
            self.color_name_label.setText(color.name())

            # Update the image
            self.updateBorder()

    def toggleCropMode(self):
        if self.original_image is None:
            return

        self.crop_mode = not self.crop_mode

        if self.crop_mode:
            self.crop_button.setText("Disable Crop Mode")
            self.crop_button.setStyleSheet(
                """
                QPushButton {
                    font-size: 14px;
                    padding: 8px 16px;
                    background-color: #E65100;
                    color: white;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #BF360C;
                }
                QPushButton:pressed {
                    background-color: #8D6E63;
                }
                """
            )
            self.image_widget.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.crop_button.setText("Enter Crop Mode")
            self.crop_button.setStyleSheet(
                """
                QPushButton {
                    font-size: 14px;
                    padding: 8px 16px;
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
                QPushButton:pressed {
                    background-color: #E65100;
                }
                """
            )
            self.image_widget.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.cancelCrop()

    def imageMousePressEvent(self, event):
        if not self.crop_mode or self.original_image is None:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.crop_start = event.pos()
            self.crop_end = None
            self.crop_rect = None
            self.apply_crop_button.setEnabled(False)

    def imageMouseMoveEvent(self, event):
        if not self.crop_mode or self.original_image is None or not self.crop_start:
            return

        self.crop_end = event.pos()
        self.updateCropDisplay()

    def imageMouseReleaseEvent(self, event):
        if not self.crop_mode or self.original_image is None or not self.crop_start:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.crop_end = event.pos()
            self.updateCropDisplay()

            # Enable crop action buttons if we have a valid selection
            if (
                self.crop_rect
                and self.crop_rect.width() > 10
                and self.crop_rect.height() > 10
            ):
                self.apply_crop_button.setEnabled(True)

            # Stop tracking mouse for crop once selection is made
            self.crop_start = None

    def updateCropDisplay(self):
        if not self.crop_start or not self.crop_end:
            return

        # Calculate crop rectangle
        x1, y1 = min(self.crop_start.x(), self.crop_end.x()), min(
            self.crop_start.y(), self.crop_end.y()
        )
        x2, y2 = max(self.crop_start.x(), self.crop_end.x()), max(
            self.crop_start.y(), self.crop_end.y()
        )

        # Ensure crop rectangle is within image bounds
        widget_size = self.image_widget.size()
        x1 = max(0, min(x1, widget_size.width()))
        y1 = max(0, min(y1, widget_size.height()))
        x2 = max(0, min(x2, widget_size.width()))
        y2 = max(0, min(y2, widget_size.height()))

        self.crop_rect = QRect(x1, y1, x2 - x1, y2 - y1)

        # Update the display with crop overlay
        self.updateBorder()

    def applyCrop(self):
        if not self.crop_rect or self.original_image is None:
            return

        # Get the current image (with borders applied)
        current_image = cv2.copyMakeBorder(
            self.original_image,
            self.top_border,
            self.bottom_border,
            self.left_border,
            self.right_border,
            cv2.BORDER_CONSTANT,
            value=self.border_color,
        )

        # Calculate crop coordinates in the full image
        widget_size = self.image_widget.size()
        pixmap_size = (
            self.image_widget.pixmap().size()
            if self.image_widget.pixmap()
            else widget_size
        )

        # Calculate scaling factors
        scale_x = current_image.shape[1] / pixmap_size.width()
        scale_y = current_image.shape[0] / pixmap_size.height()

        # Calculate crop coordinates in the full image
        crop_x = int(self.crop_rect.x() * scale_x)
        crop_y = int(self.crop_rect.y() * scale_y)
        crop_width = int(self.crop_rect.width() * scale_x)
        crop_height = int(self.crop_rect.height() * scale_y)

        # Ensure crop coordinates are within image bounds
        crop_x = max(0, min(crop_x, current_image.shape[1] - 1))
        crop_y = max(0, min(crop_y, current_image.shape[0] - 1))
        crop_width = min(crop_width, current_image.shape[1] - crop_x)
        crop_height = min(crop_height, current_image.shape[0] - crop_y)

        # Apply the crop
        self.cropped_image = current_image[
            crop_y : crop_y + crop_height, crop_x : crop_x + crop_width
        ]

        # Update the original image to the cropped version
        self.original_image = self.cropped_image.copy()

        # Reset border values
        self.top_border = 0
        self.bottom_border = 0
        self.left_border = 0
        self.right_border = 0

        # Update sliders and text boxes
        self.top_slider.setValue(0)
        self.bottom_slider.setValue(0)
        self.left_slider.setValue(0)
        self.right_slider.setValue(0)
        self.top_text_box.setText("0")
        self.bottom_text_box.setText("0")
        self.left_text_box.setText("0")
        self.right_text_box.setText("0")

        # Exit crop mode
        self.toggleCropMode()

        # Update display
        self.updateBorder()

    def cancelCrop(self):
        self.crop_start = None
        self.crop_end = None
        self.crop_rect = None
        self.apply_crop_button.setEnabled(False)
        self.updateBorder()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    sys.exit(app.exec())
