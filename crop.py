from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout


def create_crop_group(main_window):
    crop_group = QGroupBox("Crop Controls")
    crop_group.setStyleSheet(
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
    crop_layout = QVBoxLayout()

    # Crop mode toggle and apply crop buttons in horizontal layout
    crop_buttons_layout = QHBoxLayout()

    main_window.crop_button = QPushButton("Enable Crop Mode", main_window)
    main_window.crop_button.setStyleSheet(
        """
        QPushButton {
            font-size: 14px;
            padding: 10px 20px;
            background-color: #FF9800;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #F57C00;
        }
        QPushButton:pressed {
            background-color: #E65100;
        }
        QPushButton:disabled {
            background-color: #555;
            color: #888;
        }
        """
    )
    main_window.crop_button.clicked.connect(main_window.toggleCropMode)
    main_window.crop_button.setEnabled(False)  # Disabled until image is loaded

    main_window.apply_crop_button = QPushButton("Apply Crop", main_window)
    main_window.apply_crop_button.setStyleSheet(
        """
        QPushButton {
            font-size: 14px;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        QPushButton:disabled {
            background-color: #555;
            color: #888;
        }
        """
    )
    main_window.apply_crop_button.clicked.connect(main_window.applyCrop)
    main_window.apply_crop_button.setEnabled(False)

    crop_buttons_layout.addWidget(main_window.crop_button)
    crop_buttons_layout.addWidget(main_window.apply_crop_button)
    crop_layout.addLayout(crop_buttons_layout)
    crop_group.setLayout(crop_layout)

    return crop_group
