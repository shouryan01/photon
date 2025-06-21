from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
)


def create_border_group(main_window):
    border_group = QGroupBox("Border Controls")
    border_group.setStyleSheet(
        """
        QGroupBox {
            font-weight: bold;
            color: #ffffff;
            border: 2px solid #404040;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """
    )
    border_layout = QVBoxLayout()

    # Top border slider
    top_layout = QHBoxLayout()
    top_label = QLabel("Top:")
    top_label.setFixedWidth(50)
    top_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
    main_window.top_slider = QSlider(Qt.Orientation.Horizontal)
    main_window.top_slider.setRange(0, 500)
    main_window.top_slider.setValue(0)
    main_window.top_slider.setStyleSheet(
        """
        QSlider::groove:horizontal {
            border: 1px solid #404040;
            height: 8px;
            background: #1e1e1e;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #4CAF50;
            border: 1px solid #4CAF50;
            width: 18px;
            margin: -2px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #45a049;
        }
    """
    )
    main_window.top_slider.valueChanged.connect(main_window.onSliderChanged)
    main_window.top_text_box = QLineEdit("0")
    main_window.top_text_box.setValidator(QIntValidator(0, 500))
    main_window.top_text_box.setFixedWidth(60)
    main_window.top_text_box.setStyleSheet(
        """
        QLineEdit {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 4px;
        }
        QLineEdit:focus {
            border: 1px solid #4CAF50;
        }
    """
    )
    main_window.top_text_box.textChanged.connect(main_window.onTextChanged)
    top_layout.addWidget(top_label)
    top_layout.addWidget(main_window.top_slider)
    top_layout.addWidget(main_window.top_text_box)

    # Bottom border slider
    bottom_layout = QHBoxLayout()
    bottom_label = QLabel("Bottom:")
    bottom_label.setFixedWidth(50)
    bottom_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
    main_window.bottom_slider = QSlider(Qt.Orientation.Horizontal)
    main_window.bottom_slider.setRange(0, 500)
    main_window.bottom_slider.setValue(0)
    main_window.bottom_slider.setStyleSheet(
        """
        QSlider::groove:horizontal {
            border: 1px solid #404040;
            height: 8px;
            background: #1e1e1e;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #4CAF50;
            border: 1px solid #4CAF50;
            width: 18px;
            margin: -2px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #45a049;
        }
    """
    )
    main_window.bottom_slider.valueChanged.connect(main_window.onSliderChanged)
    main_window.bottom_text_box = QLineEdit("0")
    main_window.bottom_text_box.setValidator(QIntValidator(0, 500))
    main_window.bottom_text_box.setFixedWidth(60)
    main_window.bottom_text_box.setStyleSheet(
        """
        QLineEdit {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 4px;
        }
        QLineEdit:focus {
            border: 1px solid #4CAF50;
        }
    """
    )
    main_window.bottom_text_box.textChanged.connect(main_window.onTextChanged)
    bottom_layout.addWidget(bottom_label)
    bottom_layout.addWidget(main_window.bottom_slider)
    bottom_layout.addWidget(main_window.bottom_text_box)

    # Left border slider
    left_layout = QHBoxLayout()
    left_label = QLabel("Left:")
    left_label.setFixedWidth(50)
    left_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
    main_window.left_slider = QSlider(Qt.Orientation.Horizontal)
    main_window.left_slider.setRange(0, 500)
    main_window.left_slider.setValue(0)
    main_window.left_slider.setStyleSheet(
        """
        QSlider::groove:horizontal {
            border: 1px solid #404040;
            height: 8px;
            background: #1e1e1e;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #4CAF50;
            border: 1px solid #4CAF50;
            width: 18px;
            margin: -2px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #45a049;
        }
    """
    )
    main_window.left_slider.valueChanged.connect(main_window.onSliderChanged)
    main_window.left_text_box = QLineEdit("0")
    main_window.left_text_box.setValidator(QIntValidator(0, 500))
    main_window.left_text_box.setFixedWidth(60)
    main_window.left_text_box.setStyleSheet(
        """
        QLineEdit {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 4px;
        }
        QLineEdit:focus {
            border: 1px solid #4CAF50;
        }
    """
    )
    main_window.left_text_box.textChanged.connect(main_window.onTextChanged)
    left_layout.addWidget(left_label)
    left_layout.addWidget(main_window.left_slider)
    left_layout.addWidget(main_window.left_text_box)

    # Right border slider
    right_layout = QHBoxLayout()
    right_label = QLabel("Right:")
    right_label.setFixedWidth(50)
    right_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
    main_window.right_slider = QSlider(Qt.Orientation.Horizontal)
    main_window.right_slider.setRange(0, 500)
    main_window.right_slider.setValue(0)
    main_window.right_slider.setStyleSheet(
        """
        QSlider::groove:horizontal {
            border: 1px solid #404040;
            height: 8px;
            background: #1e1e1e;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #4CAF50;
            border: 1px solid #4CAF50;
            width: 18px;
            margin: -2px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #45a049;
        }
    """
    )
    main_window.right_slider.valueChanged.connect(main_window.onSliderChanged)
    main_window.right_text_box = QLineEdit("0")
    main_window.right_text_box.setValidator(QIntValidator(0, 500))
    main_window.right_text_box.setFixedWidth(60)
    main_window.right_text_box.setStyleSheet(
        """
        QLineEdit {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 4px;
        }
        QLineEdit:focus {
            border: 1px solid #4CAF50;
        }
    """
    )
    main_window.right_text_box.textChanged.connect(main_window.onTextChanged)
    right_layout.addWidget(right_label)
    right_layout.addWidget(main_window.right_slider)
    right_layout.addWidget(main_window.right_text_box)

    border_layout.addLayout(top_layout)
    border_layout.addLayout(bottom_layout)
    border_layout.addLayout(left_layout)
    border_layout.addLayout(right_layout)

    # Add Save/Load buttons
    buttons_layout = QHBoxLayout()
    save_button = QPushButton("Save Settings")
    save_button.clicked.connect(main_window.saveBorderSettings)
    save_button.setStyleSheet(
        """
        QPushButton {
            font-size: 12px;
            padding: 10px 20px;
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:pressed {
            background-color: #1565C0;
        }
        """
    )
    load_button = QPushButton("Load Settings")
    load_button.clicked.connect(main_window.loadBorderSettings)
    load_button.setStyleSheet(
        """
        QPushButton {
            font-size: 12px;
            padding: 10px 20px;
            background-color: #FF9800;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #F57C00;
        }
        QPushButton:pressed {
            background-color: #E65100;
        }
        """
    )
    buttons_layout.addWidget(save_button)
    buttons_layout.addSpacing(10)
    buttons_layout.addWidget(load_button)

    border_layout.addLayout(buttons_layout)

    border_group.setLayout(border_layout)

    return border_group
