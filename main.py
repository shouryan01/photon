import json
import os
import sys

from PyQt6.QtCore import QPoint, QRect, QRectF, Qt, QThread, pyqtSignal
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
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from border import create_border_group
from focal_length import analyze_focal_lengths_batched, analyze_focal_lengths_parallel

# from crop import create_crop_group


class FocalLengthWorker(QThread):
    """Worker thread for focal length analysis."""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, folder_path, max_workers=4, batch_size=100):
        super().__init__()
        self.folder_path = folder_path
        self.max_workers = max_workers
        self.batch_size = batch_size

    def run(self):
        try:
            # Always use the batched method for optimal performance
            result = analyze_focal_lengths_batched(
                self.folder_path,
                batch_size=self.batch_size,
                max_workers=self.max_workers,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class BatchWorker(QThread):
    """Worker thread for batch image processing."""

    finished = pyqtSignal(int, int)  # success_count, error_count
    progress = pyqtSignal(int)  # current progress
    error = pyqtSignal(str)

    def __init__(self, image_paths, output_dir, border_settings, max_workers=4):
        super().__init__()
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.border_settings = border_settings
        self.max_workers = max_workers

    def run(self):
        try:
            if len(self.image_paths) > 10 and self.max_workers > 1:
                # Use parallel processing for larger batches
                self._process_parallel()
            else:
                # Use sequential processing for smaller batches
                self._process_sequential()

        except Exception as e:
            self.error.emit(str(e))

    def _process_sequential(self):
        """Process images sequentially."""
        import cv2

        success_count = 0
        error_count = 0

        for i, image_path in enumerate(self.image_paths):
            try:
                # Load image
                image = cv2.imread(image_path)
                if image is None:
                    error_count += 1
                    continue

                # Apply border
                bordered_image = cv2.copyMakeBorder(
                    image,
                    self.border_settings["top"],
                    self.border_settings["bottom"],
                    self.border_settings["left"],
                    self.border_settings["right"],
                    cv2.BORDER_CONSTANT,
                    value=self.border_settings["color"],
                )

                # Generate output filename
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                extension = os.path.splitext(image_path)[1]
                output_path = os.path.join(
                    self.output_dir, f"{base_name}_bordered{extension}"
                )

                # Save image
                cv2.imwrite(output_path, bordered_image)
                success_count += 1

            except Exception as e:
                error_count += 1
                print(f"Error processing {image_path}: {str(e)}")

            # Emit progress
            self.progress.emit(i + 1)

        # Emit final results
        self.finished.emit(success_count, error_count)

    def _process_parallel(self):
        """Process images in parallel using ThreadPoolExecutor."""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed

        success_count = 0
        error_count = 0
        processed_count = 0
        lock = threading.Lock()

        def process_single_image(image_path):
            import cv2

            nonlocal success_count, error_count
            try:
                # Load image
                image = cv2.imread(image_path)
                if image is None:
                    with lock:
                        error_count += 1
                    return False

                # Apply border
                bordered_image = cv2.copyMakeBorder(
                    image,
                    self.border_settings["top"],
                    self.border_settings["bottom"],
                    self.border_settings["left"],
                    self.border_settings["right"],
                    cv2.BORDER_CONSTANT,
                    value=self.border_settings["color"],
                )

                # Generate output filename
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                extension = os.path.splitext(image_path)[1]
                output_path = os.path.join(
                    self.output_dir, f"{base_name}_bordered{extension}"
                )

                # Save image
                cv2.imwrite(output_path, bordered_image)

                with lock:
                    success_count += 1
                return True

            except Exception as e:
                print(f"Error processing {image_path}: {str(e)}")
                with lock:
                    error_count += 1
                return False

        # Process images in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(process_single_image, path): path
                for path in self.image_paths
            }

            # Process completed tasks
            for future in as_completed(future_to_path):
                processed_count += 1
                self.progress.emit(processed_count)

        # Emit final results
        self.finished.emit(success_count, error_count)


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
        # self.crop_mode = False
        # self.crop_start = None
        # self.crop_end = None
        # self.crop_rect = None

        # self.cropped_image = None

        # Batch processing values
        self.batch_images = []
        self.batch_output_dir = None
        self.processing_batch = False

        # Focal length analysis values
        self.focal_length_data = None
        self.focal_length_folder = None
        self.focal_worker = None

        # Shutter count analysis values
        self.shutter_count_data = None
        self.shutter_count_image_path = None
        self.shutter_worker = None

        # Batch processing worker
        self.batch_worker = None

        # Window dragging
        self.dragging = False
        self.drag_position = QPoint()

        # Tab management
        self.current_tab = 0
        self.tab_buttons = []

        self.initializeUI()

    def initializeUI(self):
        self.setWindowTitle("Photon")
        self.setGeometry(200, 200, 1200, 800)

        # Make window frameless
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Center the window on the screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 1200) // 2
        y = (screen.height() - 800) // 2
        self.setGeometry(x, y, 1200, 800)

        # Main container with background
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        main_container.setStyleSheet(
            """
            #mainContainer {
                background-color: #2b2b2b;
                border-radius: 10px;
                border: 1px solid #404040;
            }
        """
        )

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar with tabs
        title_bar = self.createTitleBar()
        main_layout.addWidget(title_bar)

        # Stacked widget for tab content
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("stackedWidget")
        self.stacked_widget.setStyleSheet(
            """
            #stackedWidget {
                background-color: #2b2b2b;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """
        )

        # Create tab content
        self.createMainTab()
        self.createFocalLengthTab()
        self.createShutterCountTab()

        main_layout.addWidget(self.stacked_widget)
        main_container.setLayout(main_layout)

        # Set the main container as the central widget
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(main_container)
        self.setLayout(container_layout)

    def createMainTab(self):
        # Content area for main tab
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet(
            """
            #contentWidget {
                background-color: #2b2b2b;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """
        )

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Left panel for controls
        left_panel_widget = QWidget()
        left_panel_widget.setFixedWidth(350)  # Fixed width for left panel
        left_panel = QVBoxLayout()
        left_panel.setContentsMargins(0, 0, 0, 0)

        # Image picker button
        self.pick_button = QPushButton("Pick Image", self)
        self.pick_button.setStyleSheet(
            """
            QPushButton {
                font-size: 16px;
                padding: 12px 24px;
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
            """
        )
        self.pick_button.clicked.connect(self.pickImage)

        # Download button
        self.download_button = QPushButton("Download Image", self)
        self.download_button.setStyleSheet(
            """
            QPushButton {
                font-size: 16px;
                padding: 12px 24px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
            """
        )
        self.download_button.clicked.connect(self.downloadImage)
        self.download_button.setEnabled(False)  # Disabled until image is loaded

        # Border color controls
        color_group = QGroupBox("Border Color")
        color_group.setStyleSheet(
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
        color_layout = QHBoxLayout()

        self.border_color_label = QLabel("Color:")
        self.border_color_label.setStyleSheet(
            "font-weight: bold; margin: 5px; color: #ffffff;"
        )

        self.color_button = QPushButton("")
        self.color_button.setFixedSize(40, 30)
        self.color_button.setStyleSheet(
            """
            QPushButton {
                background-color: white;
                border: 2px solid #555;
                border-radius: 6px;
            }
            QPushButton:hover {
                border: 2px solid #777;
            }
        """
        )
        self.color_button.clicked.connect(self.pickColor)

        self.color_name_label = QLabel("White")
        self.color_name_label.setStyleSheet("margin: 5px; color: #ffffff;")

        color_layout.addWidget(self.border_color_label)
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_name_label)
        color_layout.addStretch()
        color_group.setLayout(color_layout)

        # Border controls
        border_group = create_border_group(self)

        # Crop controls
        # crop_group = create_crop_group(self)

        # Batch processing controls
        batch_group = self.createBatchGroup()

        # Add controls to left panel
        # Create horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.pick_button)
        button_layout.addWidget(self.download_button)

        left_panel.addLayout(button_layout)
        left_panel.addWidget(color_group)
        left_panel.addWidget(border_group)
        # left_panel.addWidget(crop_group)
        left_panel.addWidget(batch_group)
        left_panel.addStretch()

        left_panel_widget.setLayout(left_panel)

        # Right panel for image display
        right_panel = QVBoxLayout()

        # Image display widget - now resizable
        self.image_widget = QLabel()
        self.image_widget.setMinimumSize(400, 300)  # Minimum size instead of fixed
        self.image_widget.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #555;
                border-radius: 8px;
                background-color: #1e1e1e;
            }
        """
        )
        self.image_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Enable mouse events for crop selection
        # self.image_widget.setMouseTracking(True)
        # self.image_widget.mousePressEvent = self.imageMousePressEvent
        # self.image_widget.mouseMoveEvent = self.imageMouseMoveEvent
        # self.image_widget.mouseReleaseEvent = self.imageMouseReleaseEvent

        # Connect resize event to update image
        self.image_widget.resizeEvent = self.imageResizeEvent

        right_panel.addWidget(self.image_widget)

        # Add panels to content layout
        content_layout.addWidget(left_panel_widget)  # Fixed width widget
        content_layout.addLayout(right_panel, 1)  # Stretch factor for right panel

        content_widget.setLayout(content_layout)
        self.stacked_widget.addWidget(content_widget)

    def createFocalLengthTab(self):
        # Content area for Focal Length Analysis tab
        focal_widget = QWidget()
        focal_widget.setObjectName("focalWidget")
        focal_widget.setStyleSheet(
            """
            #focalWidget {
                background-color: #2b2b2b;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """
        )

        focal_layout = QHBoxLayout()
        focal_layout.setContentsMargins(20, 20, 20, 20)

        # Left panel for controls
        left_panel_widget = QWidget()
        left_panel_widget.setFixedWidth(350)
        left_panel = QVBoxLayout()
        left_panel.setContentsMargins(0, 0, 0, 0)

        # Folder selection button
        self.select_folder_button = QPushButton("Select Image Folder", self)
        self.select_folder_button.setStyleSheet(
            """
            QPushButton {
                font-size: 16px;
                padding: 12px 24px;
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
            """
        )
        self.select_folder_button.clicked.connect(self.selectFocalLengthFolder)

        # Analyze button
        self.analyze_button = QPushButton("Analyze Focal Lengths", self)
        self.analyze_button.setStyleSheet(
            """
            QPushButton {
                font-size: 16px;
                padding: 12px 24px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
            """
        )
        self.analyze_button.clicked.connect(self.analyzeFocalLengths)
        self.analyze_button.setEnabled(False)

        # Progress bar
        self.focal_progress = QProgressBar()
        self.focal_progress.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 5px;
                text-align: center;
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """
        )
        self.focal_progress.setVisible(False)

        # Loading label
        self.loading_label = QLabel("")
        self.loading_label.setStyleSheet(
            """
            color: #4CAF50;
            font-size: 14px;
            font-weight: bold;
            text-align: center;
        """
        )
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setVisible(False)

        # Status label
        self.focal_status_label = QLabel("No folder selected")
        self.focal_status_label.setStyleSheet("color: #ffffff; font-size: 12px;")

        # Results group
        results_group = QGroupBox("Analysis Results")
        results_group.setStyleSheet(
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
        results_layout = QVBoxLayout()

        self.results_label = QLabel("No analysis performed yet")
        self.results_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        self.results_label.setWordWrap(True)

        results_layout.addWidget(self.results_label)
        results_group.setLayout(results_layout)

        # Add controls to left panel
        left_panel.addWidget(self.select_folder_button)
        left_panel.addWidget(self.analyze_button)
        left_panel.addWidget(self.focal_progress)
        left_panel.addWidget(self.loading_label)
        left_panel.addWidget(self.focal_status_label)
        left_panel.addWidget(results_group)
        left_panel.addStretch()

        left_panel_widget.setLayout(left_panel)

        # Right panel for histogram
        right_panel = QVBoxLayout()

        # Histogram widget
        self.histogram_widget = QLabel()
        self.histogram_widget.setMinimumSize(400, 300)
        self.histogram_widget.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #555;
                border-radius: 8px;
                background-color: #1e1e1e;
            }
        """
        )
        self.histogram_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.histogram_widget.setText("Histogram will appear here after analysis")

        right_panel.addWidget(self.histogram_widget)

        # Add panels to content layout
        focal_layout.addWidget(left_panel_widget)
        focal_layout.addLayout(right_panel, 1)

        focal_widget.setLayout(focal_layout)
        self.stacked_widget.addWidget(focal_widget)

    def createShutterCountTab(self):
        # Content area for Shutter Count Analysis tab
        shutter_widget = QWidget()
        shutter_widget.setObjectName("shutterWidget")
        shutter_widget.setStyleSheet(
            """
            #shutterWidget {
                background-color: #2b2b2b;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """
        )

        shutter_layout = QHBoxLayout()
        shutter_layout.setContentsMargins(20, 20, 20, 20)

        # Left panel for controls
        left_panel_widget = QWidget()
        left_panel_widget.setFixedWidth(350)
        left_panel = QVBoxLayout()
        left_panel.setContentsMargins(0, 0, 0, 0)

        # Image selection button
        self.select_shutter_image_button = QPushButton("Select Image", self)
        self.select_shutter_image_button.setStyleSheet(
            """
            QPushButton {
                font-size: 16px;
                padding: 12px 24px;
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
            """
        )
        self.select_shutter_image_button.clicked.connect(self.selectShutterCountImage)

        # Progress bar
        self.shutter_progress = QProgressBar()
        self.shutter_progress.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 5px;
                text-align: center;
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """
        )
        self.shutter_progress.setVisible(False)

        # Loading label
        self.shutter_loading_label = QLabel("")
        self.shutter_loading_label.setStyleSheet(
            """
            color: #4CAF50;
            font-size: 14px;
            font-weight: bold;
            text-align: center;
        """
        )
        self.shutter_loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shutter_loading_label.setVisible(False)

        # Status label
        self.shutter_status_label = QLabel("No image selected")
        self.shutter_status_label.setStyleSheet("color: #ffffff; font-size: 12px;")

        # Add controls to left panel
        left_panel.addWidget(self.select_shutter_image_button)
        left_panel.addWidget(self.shutter_progress)
        left_panel.addWidget(self.shutter_loading_label)
        left_panel.addWidget(self.shutter_status_label)
        left_panel.addStretch()

        left_panel_widget.setLayout(left_panel)

        # Right panel for shutter count display
        right_panel = QVBoxLayout()

        # Shutter count display widget
        self.shutter_count_display = QLabel()
        self.shutter_count_display.setMinimumSize(400, 300)
        self.shutter_count_display.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #555;
                border-radius: 8px;
                background-color: #1e1e1e;
                color: #4CAF50;
                font-size: 72px;
                font-weight: bold;
            }
        """
        )
        self.shutter_count_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shutter_count_display.setText("--")

        right_panel.addWidget(self.shutter_count_display)

        # Add panels to content layout
        shutter_layout.addWidget(left_panel_widget)
        shutter_layout.addLayout(right_panel, 1)

        shutter_widget.setLayout(shutter_layout)
        self.stacked_widget.addWidget(shutter_widget)

    def createTitleBar(self):
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)  # Back to original height
        title_bar.setStyleSheet(
            """
            #titleBar {
                background-color: #1e1e1e;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid #404040;
            }
        """
        )

        # Add mouse event handlers to title bar for dragging
        title_bar.mousePressEvent = self.titleBarMousePressEvent
        title_bar.mouseMoveEvent = self.titleBarMouseMoveEvent
        title_bar.mouseReleaseEvent = self.titleBarMouseReleaseEvent

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(15, 0, 15, 0)

        # App title
        title_label = QLabel("Photon")
        title_label.setStyleSheet(
            """
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
        """
        )

        # Tab buttons in center
        tab_layout = QHBoxLayout()
        tab_layout.setSpacing(5)
        tab_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create tab buttons
        # self.createTabButton("Border Control", 0, tab_layout)
        # self.createTabButton("Optimal Prime", 1, tab_layout)
        # self.createTabButton("Shutter Count", 2, tab_layout)

        # Window controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        # Minimize button
        minimize_btn = QPushButton("−")
        minimize_btn.setFixedSize(20, 20)
        minimize_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """
        )
        minimize_btn.clicked.connect(self.showMinimized)

        # Maximize button
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(20, 20)
        self.maximize_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """
        )
        self.maximize_btn.clicked.connect(self.toggleMaximize)

        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #e81123;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f1707a;
            }
        """
        )
        close_btn.clicked.connect(self.close)

        controls_layout.addWidget(minimize_btn)
        controls_layout.addWidget(self.maximize_btn)
        controls_layout.addWidget(close_btn)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addLayout(tab_layout)
        title_layout.addStretch()
        title_layout.addLayout(controls_layout)

        title_bar.setLayout(title_layout)
        return title_bar

    def createTabButton(self, text, tab_index, layout):
        tab_button = QPushButton(text)
        tab_button.setFixedSize(120, 30)
        tab_button.setCheckable(True)

        # Set initial state
        if tab_index == 0:
            tab_button.setChecked(True)

        tab_button.clicked.connect(lambda: self.switchTab(tab_index))

        # Style the tab button
        tab_button.setStyleSheet(
            """
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:checked {
                background-color: #2196F3;
            }
            QPushButton:checked:hover {
                background-color: #1976D2;
            }
        """
        )

        layout.addWidget(tab_button)
        self.tab_buttons.append(tab_button)

    def switchTab(self, tab_index):
        # Update tab button states
        for i, button in enumerate(self.tab_buttons):
            button.setChecked(i == tab_index)

        # Switch to the selected tab
        self.current_tab = tab_index
        self.stacked_widget.setCurrentIndex(tab_index)

    def toggleMaximize(self):
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")

    def titleBarMousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def titleBarMouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def titleBarMouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

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
        self.right_border = max(0, min(self.right_border, self.right_slider.maximum()))

        # Update sliders
        self.top_slider.setValue(self.top_border)
        self.bottom_slider.setValue(self.bottom_border)
        self.left_slider.setValue(self.left_border)
        self.right_slider.setValue(self.right_border)

        # Update the image display
        self.updateBorder()

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
                    border: 2px solid #555;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    border: 2px solid #777;
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
        import cv2

        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            return

        self.current_image_path = image_path
        self.download_button.setEnabled(True)  # Enable download button
        # self.crop_button.setEnabled(True)  # Enable crop button

        # # Update crop button styling to match "Enter Crop Mode" state
        # self.crop_button.setText("Enter Crop Mode")
        # self.crop_button.setStyleSheet(
        #     """
        #     QPushButton {
        #         font-size: 14px;
        #         padding: 8px 16px;
        #         background-color: #FF9800;
        #         color: white;
        #         border: none;
        #         border-radius: 5px;
        #     }
        #     QPushButton:hover {
        #         background-color: #F57C00;
        #     }
        #     QPushButton:pressed {
        #         background-color: #E65100;
        #     }
        #     """
        # )

        self.updateBorder()

    def updateBorder(self):
        if self.original_image is None:
            return

        import cv2

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
        # if self.crop_mode and self.crop_rect:
        #     painter = QPainter(scaled_pixmap)

        #     # Create a semi-transparent overlay for the area outside the crop
        #     path = QPainterPath()
        #     path.addRect(QRectF(scaled_pixmap.rect()))
        #     path.addRect(QRectF(self.crop_rect))

        #     painter.setPen(Qt.PenStyle.NoPen)
        #     painter.setBrush(QColor(0, 0, 0, 100))  # Semi-transparent black
        #     painter.drawPath(path)

        #     # Draw the yellow border for the crop rectangle
        #     painter.setBrush(Qt.BrushStyle.NoBrush)
        #     painter.setPen(QPen(QColor(255, 255, 0), 2))  # Yellow border
        #     painter.drawRect(self.crop_rect)

        #     painter.end()

        self.image_widget.setPixmap(scaled_pixmap)

    def downloadImage(self):
        if self.original_image is None:
            return

        import cv2

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
            "Save Settings",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            with open(file_path, "w") as f:
                json.dump(settings, f, indent=4)

    def loadBorderSettings(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Settings",
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

            # Temporarily disconnect signals to prevent conflicts
            self.top_slider.valueChanged.disconnect()
            self.bottom_slider.valueChanged.disconnect()
            self.left_slider.valueChanged.disconnect()
            self.right_slider.valueChanged.disconnect()
            self.top_text_box.textChanged.disconnect()
            self.bottom_text_box.textChanged.disconnect()
            self.left_text_box.textChanged.disconnect()
            self.right_text_box.textChanged.disconnect()

            # Update UI
            self.top_slider.setValue(self.top_border)
            self.bottom_slider.setValue(self.bottom_border)
            self.left_slider.setValue(self.left_border)
            self.right_slider.setValue(self.right_border)

            self.top_text_box.setText(str(self.top_border))
            self.bottom_text_box.setText(str(self.bottom_border))
            self.left_text_box.setText(str(self.left_border))
            self.right_text_box.setText(str(self.right_border))

            # Reconnect signals
            self.top_slider.valueChanged.connect(self.onSliderChanged)
            self.bottom_slider.valueChanged.connect(self.onSliderChanged)
            self.left_slider.valueChanged.connect(self.onSliderChanged)
            self.right_slider.valueChanged.connect(self.onSliderChanged)
            self.top_text_box.textChanged.connect(self.onTextChanged)
            self.bottom_text_box.textChanged.connect(self.onTextChanged)
            self.left_text_box.textChanged.connect(self.onTextChanged)
            self.right_text_box.textChanged.connect(self.onTextChanged)

            # Update color
            b, g, r = self.border_color
            color = QColor(r, g, b)
            self.color_button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {color.name()};
                    border: 2px solid #555;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    border: 2px solid #777;
                }}
            """
            )
            self.color_name_label.setText(color.name())

            # Update the image
            self.updateBorder()

    # def toggleCropMode(self):
    #     if self.original_image is None:
    #         return

    #     self.crop_mode = not self.crop_mode

    #     if self.crop_mode:
    #         self.crop_button.setText("Disable Crop Mode")
    #         self.crop_button.setStyleSheet(
    #             """
    #             QPushButton {
    #                 font-size: 14px;
    #                 padding: 8px 16px;
    #                 background-color: #E65100;
    #                 color: white;
    #                 border: none;
    #                 border-radius: 5px;
    #             }
    #             QPushButton:hover {
    #                 background-color: #BF360C;
    #             }
    #             QPushButton:pressed {
    #                 background-color: #8D6E63;
    #             }
    #             """
    #         )
    #         self.image_widget.setCursor(QCursor(Qt.CursorShape.CrossCursor))
    #     else:
    #         self.crop_button.setText("Enter Crop Mode")
    #         self.crop_button.setStyleSheet(
    #             """
    #             QPushButton {
    #                 font-size: 14px;
    #                 padding: 8px 16px;
    #                 background-color: #FF9800;
    #                 color: white;
    #                 border: none;
    #                 border-radius: 5px;
    #             }
    #             QPushButton:hover {
    #                 background-color: #F57C00;
    #             }
    #             QPushButton:pressed {
    #                 background-color: #E65100;
    #             }
    #             """
    #         )
    #         self.image_widget.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
    #         self.cancelCrop()

    # def imageMousePressEvent(self, event):
    #     if not self.crop_mode or self.original_image is None:
    #         return

    #     if event.button() == Qt.MouseButton.LeftButton:
    #         self.crop_start = event.pos()
    #         self.crop_end = None
    #         self.crop_rect = None
    #         self.apply_crop_button.setEnabled(False)

    # def imageMouseMoveEvent(self, event):
    #     if not self.crop_mode or self.original_image is None or not self.crop_start:
    #         return

    #     self.crop_end = event.pos()
    #     self.updateCropDisplay()

    # def imageMouseReleaseEvent(self, event):
    #     if not self.crop_mode or self.original_image is None or not self.crop_start:
    #         return

    #     if event.button() == Qt.MouseButton.LeftButton:
    #         self.crop_end = event.pos()
    #         self.updateCropDisplay()

    #         # Enable crop action buttons if we have a valid selection
    #         if (
    #             self.crop_rect
    #             and self.crop_rect.width() > 10
    #             and self.crop_rect.height() > 10
    #         ):
    #             self.apply_crop_button.setEnabled(True)

    #         # Stop tracking mouse for crop once selection is made
    #         self.crop_start = None

    # def updateCropDisplay(self):
    #     if not self.crop_start or not self.crop_end:
    #         return

    #     # Calculate crop rectangle
    #     x1, y1 = min(self.crop_start.x(), self.crop_end.x()), min(
    #         self.crop_start.y(), self.crop_end.y()
    #     )
    #     x2, y2 = max(self.crop_start.x(), self.crop_end.x()), max(
    #         self.crop_start.y(), self.crop_end.y()
    #     )

    #     # Ensure crop rectangle is within image bounds
    #     widget_size = self.image_widget.size()
    #     x1 = max(0, min(x1, widget_size.width()))
    #     y1 = max(0, min(y1, widget_size.height()))
    #     x2 = max(0, min(x2, widget_size.width()))
    #     y2 = max(0, min(y2, widget_size.height()))

    #     self.crop_rect = QRect(x1, y1, x2 - x1, y2 - y1)

    #     # Update the display with crop overlay
    #     self.updateBorder()

    # def applyCrop(self):
    #     if not self.crop_rect or self.original_image is None:
    #         return

    #     # Get the current image (with borders applied)
    #     current_image = cv2.copyMakeBorder(
    #         self.original_image,
    #         self.top_border,
    #         self.bottom_border,
    #         self.left_border,
    #         self.right_border,
    #         cv2.BORDER_CONSTANT,
    #         value=self.border_color,
    #     )

    #     # Calculate crop coordinates in the full image
    #     widget_size = self.image_widget.size()
    #     pixmap_size = (
    #         self.image_widget.pixmap().size()
    #         if self.image_widget.pixmap()
    #         else widget_size
    #     )

    #     # Calculate scaling factors
    #     scale_x = current_image.shape[1] / pixmap_size.width()
    #     scale_y = current_image.shape[0] / pixmap_size.height()

    #     # Calculate crop coordinates in the full image
    #     crop_x = int(self.crop_rect.x() * scale_x)
    #     crop_y = int(self.crop_rect.y() * scale_y)
    #     crop_width = int(self.crop_rect.width() * scale_x)
    #     crop_height = int(self.crop_rect.height() * scale_y)

    #     # Ensure crop coordinates are within image bounds
    #     crop_x = max(0, min(crop_x, current_image.shape[1] - 1))
    #     crop_y = max(0, min(crop_y, current_image.shape[0] - 1))
    #     crop_width = min(crop_width, current_image.shape[1] - crop_x)
    #     crop_height = min(crop_height, current_image.shape[0] - crop_y)

    #     # Apply the crop
    #     self.cropped_image = current_image[
    #         crop_y : crop_y + crop_height, crop_x : crop_x + crop_width
    #     ]

    #     # Update the original image to the cropped version
    #     self.original_image = self.cropped_image.copy()

    #     # Reset border values
    #     self.top_border = 0
    #     self.bottom_border = 0
    #     self.left_border = 0
    #     self.right_border = 0

    #     # Update sliders and text boxes
    #     self.top_slider.setValue(0)
    #     self.bottom_slider.setValue(0)
    #     self.left_slider.setValue(0)
    #     self.right_slider.setValue(0)
    #     self.top_text_box.setText("0")
    #     self.bottom_text_box.setText("0")
    #     self.left_text_box.setText("0")
    #     self.right_text_box.setText("0")

    #     # Exit crop mode
    #     self.toggleCropMode()

    #     # Update display
    #     self.updateBorder()

    # def cancelCrop(self):
    #     self.crop_start = None
    #     self.crop_end = None
    #     self.crop_rect = None
    #     self.apply_crop_button.setEnabled(False)
    #     self.updateBorder()

    def imageResizeEvent(self, event):
        self.updateBorder()

    def createBatchGroup(self):
        batch_group = QGroupBox("Batch Processing")
        batch_group.setStyleSheet(
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
        batch_layout = QVBoxLayout()

        # Select images button
        self.select_images_button = QPushButton("Select Images for Batch")
        self.select_images_button.setStyleSheet(
            """
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #6A1B9A;
            }
        """
        )
        self.select_images_button.clicked.connect(self.selectBatchImages)

        # Select output directory button
        self.select_output_button = QPushButton("Select Output Directory")
        self.select_output_button.setStyleSheet(
            """
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
                background-color: #607D8B;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
            QPushButton:pressed {
                background-color: #37474F;
            }
        """
        )
        self.select_output_button.clicked.connect(self.selectBatchOutputDir)

        # Process batch button
        self.process_batch_button = QPushButton("Process Batch")
        self.process_batch_button.setStyleSheet(
            """
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
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
        self.process_batch_button.clicked.connect(self.processBatch)
        self.process_batch_button.setEnabled(False)

        # Cancel batch button
        self.cancel_batch_button = QPushButton("Cancel")
        self.cancel_batch_button.setStyleSheet(
            """
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """
        )
        self.cancel_batch_button.clicked.connect(self.cancelBatchProcessing)
        self.cancel_batch_button.setVisible(False)

        # Progress bar
        self.batch_progress = QProgressBar()
        self.batch_progress.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 5px;
                text-align: center;
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """
        )
        self.batch_progress.setVisible(False)

        # Status label
        self.batch_status_label = QLabel("No images selected")
        self.batch_status_label.setStyleSheet("color: #ffffff; font-size: 12px;")

        # Output directory label
        self.output_dir_label = QLabel("No output directory selected")
        self.output_dir_label.setStyleSheet("color: #ffffff; font-size: 12px;")

        # Create horizontal layout for process and cancel buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.process_batch_button)
        button_layout.addWidget(self.cancel_batch_button)

        batch_layout.addWidget(self.select_images_button)
        batch_layout.addWidget(self.select_output_button)
        batch_layout.addLayout(button_layout)
        batch_layout.addWidget(self.batch_progress)
        batch_layout.addWidget(self.batch_status_label)
        batch_layout.addWidget(self.output_dir_label)

        batch_group.setLayout(batch_layout)
        return batch_group

    def selectBatchImages(self):
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self,
            "Select Images for Batch Processing",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)",
        )

        if file_paths:
            self.batch_images = file_paths
            self.batch_status_label.setText(f"{len(file_paths)} images selected")
            self.updateBatchButtonState()

    def selectBatchOutputDir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory for Batch Processing"
        )

        if dir_path:
            self.batch_output_dir = dir_path
            # Show only the last part of the path for display
            display_path = os.path.basename(dir_path)
            if len(dir_path) > 30:
                display_path = "..." + dir_path[-27:]
            self.output_dir_label.setText(f"Output: {display_path}")
            self.updateBatchButtonState()

    def updateBatchButtonState(self):
        # Enable process button only if both images and output directory are selected
        can_process = len(self.batch_images) > 0 and self.batch_output_dir is not None
        self.process_batch_button.setEnabled(can_process)

    def processBatch(self):
        if not self.batch_images or not self.batch_output_dir:
            return

        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Batch Processing",
            f"Process {len(self.batch_images)} images with current border settings?\n\n"
            f"Top: {self.top_border}, Bottom: {self.bottom_border}\n"
            f"Left: {self.left_border}, Right: {self.right_border}\n"
            f"Color: RGB{self.border_color[::-1]}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Start batch processing
        self.processing_batch = True
        self.batch_progress.setVisible(True)
        self.batch_progress.setMaximum(len(self.batch_images))
        self.batch_progress.setValue(0)

        # Disable buttons during processing
        self.select_images_button.setEnabled(False)
        self.select_output_button.setEnabled(False)
        self.process_batch_button.setEnabled(False)
        self.cancel_batch_button.setVisible(True)

        # Process images
        # Create and start worker thread with optimized defaults
        self.batch_worker = BatchWorker(
            self.batch_images,
            self.batch_output_dir,
            {
                "top": self.top_border,
                "bottom": self.bottom_border,
                "left": self.left_border,
                "right": self.right_border,
                "color": self.border_color,
            },
            max_workers=4,  # Use 4 threads for parallel processing
        )
        self.batch_worker.finished.connect(self.onBatchProcessingComplete)
        self.batch_worker.progress.connect(self.onBatchProgressUpdate)
        self.batch_worker.error.connect(self.onBatchProcessingError)
        self.batch_worker.start()

    def onBatchProcessingComplete(self, success_count, error_count):
        """Handle completion of batch processing."""
        self.batch_progress.setVisible(False)
        self.select_images_button.setEnabled(True)
        self.select_output_button.setEnabled(True)
        self.cancel_batch_button.setVisible(False)
        self.processing_batch = False

        # Show results
        message = "Batch processing complete!\n\n"
        message += f"Successfully processed: {success_count} images\n"
        if error_count > 0:
            message += f"Failed to process: {error_count} images"

        QMessageBox.information(self, "Batch Processing Complete", message)

        # Update button state
        self.updateBatchButtonState()

    def onBatchProgressUpdate(self, value):
        """Update the progress bar during batch processing."""
        self.batch_progress.setValue(value)
        QApplication.processEvents()  # Allow UI updates

    def onBatchProcessingError(self, error_message):
        """Handle errors in batch processing."""
        QMessageBox.critical(
            self,
            "Error",
            f"An error occurred during batch processing:\n{error_message}",
        )
        self.batch_progress.setVisible(False)
        self.select_images_button.setEnabled(True)
        self.select_output_button.setEnabled(True)
        self.process_batch_button.setEnabled(True)
        self.cancel_batch_button.setVisible(False)
        self.processing_batch = False
        self.updateBatchButtonState()

    def cancelBatchProcessing(self):
        """Cancel the current batch processing operation."""
        if self.batch_worker and self.batch_worker.isRunning():
            self.batch_worker.quit()
            self.batch_worker.wait()

        self.batch_progress.setVisible(False)
        self.select_images_button.setEnabled(True)
        self.select_output_button.setEnabled(True)
        self.cancel_batch_button.setVisible(False)
        self.processing_batch = False
        self.updateBatchButtonState()

    def selectFocalLengthFolder(self):
        """Select a folder containing images for focal length analysis."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Folder with Images for Focal Length Analysis"
        )

        if dir_path:
            self.focal_length_folder = dir_path
            # Show only the last part of the path for display
            display_path = os.path.basename(dir_path)
            if len(dir_path) > 30:
                display_path = "..." + dir_path[-27:]
            self.focal_status_label.setText(f"Selected: {display_path}")
            self.analyze_button.setEnabled(True)

    def analyzeFocalLengths(self):
        """Analyze focal lengths in the selected folder and create histogram."""
        if not self.focal_length_folder:
            return

        # Show progress
        self.focal_progress.setVisible(True)
        self.focal_progress.setRange(0, 0)  # Indeterminate progress
        self.loading_label.setText("Processing images...")
        self.loading_label.setVisible(True)
        self.analyze_button.setEnabled(False)
        self.select_folder_button.setEnabled(False)
        self.focal_status_label.setText("Analyzing images... Please wait.")

        # Create and start worker thread with optimized defaults
        self.focal_worker = FocalLengthWorker(
            self.focal_length_folder,
            max_workers=4,
            batch_size=100,
        )
        self.focal_worker.finished.connect(self.onFocalAnalysisComplete)
        self.focal_worker.error.connect(self.onFocalAnalysisError)
        self.focal_worker.start()

    def onFocalAnalysisComplete(self, result):
        """Handle completion of focal length analysis."""
        import time

        self.focal_length_data = result

        # Update results display
        if self.focal_length_data["images_with_focal_length"] > 0:
            results_text = "Analysis Complete!\n\n"
            results_text += (
                f"Total images found: {self.focal_length_data['total_images']}\n"
            )
            results_text += f"Unique focal lengths: {len(set(self.focal_length_data['focal_lengths']))}"

            self.results_label.setText(results_text)

            # Create and display histogram
            self.createHistogram()
        else:
            self.results_label.setText(
                "No images with focal length data found in the selected folder."
            )
            self.histogram_widget.setText("No data to display")

        # Hide progress and re-enable buttons
        self.focal_progress.setVisible(False)
        self.loading_label.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.select_folder_button.setEnabled(True)
        self.focal_status_label.setText(
            f"Selected: {os.path.basename(self.focal_length_folder)}"
        )

    def onFocalAnalysisError(self, error_message):
        """Handle errors in focal length analysis."""
        QMessageBox.critical(
            self, "Error", f"An error occurred during analysis:\n{error_message}"
        )
        self.results_label.setText("Analysis failed. Please try again.")

        # Hide progress and re-enable buttons
        self.focal_progress.setVisible(False)
        self.loading_label.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.select_folder_button.setEnabled(True)
        self.focal_status_label.setText(
            f"Selected: {os.path.basename(self.focal_length_folder)}"
        )

    def createHistogram(self):
        """Create a histogram from the focal length data."""
        if not self.focal_length_data or not self.focal_length_data["focal_lengths"]:
            return

        import numpy as np
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure

        # Create matplotlib figure with dark theme
        fig = Figure(figsize=(10, 6), facecolor="#2b2b2b")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#2b2b2b")

        # Set dark theme colors
        ax.spines["bottom"].set_color("#ffffff")
        ax.spines["top"].set_color("#ffffff")
        ax.spines["right"].set_color("#ffffff")
        ax.spines["left"].set_color("#ffffff")
        ax.tick_params(axis="x", colors="#ffffff")
        ax.tick_params(axis="y", colors="#ffffff")
        ax.xaxis.label.set_color("#ffffff")
        ax.yaxis.label.set_color("#ffffff")
        ax.title.set_color("#ffffff")

        # Create histogram with individual focal lengths as bins
        focal_lengths = self.focal_length_data["focal_lengths"]
        unique_focal_lengths = sorted(list(set(focal_lengths)))

        # Count occurrences for each focal length
        counts = [focal_lengths.count(fl) for fl in unique_focal_lengths]

        # Create bar plot instead of histogram
        bars = ax.bar(
            range(len(unique_focal_lengths)),
            counts,
            color="#4CAF50",
            alpha=0.7,
            edgecolor="#ffffff",
        )

        # Set x-axis labels to show every focal length
        ax.set_xticks(range(len(unique_focal_lengths)))
        ax.set_xticklabels(
            [f"{fl}mm" for fl in unique_focal_lengths], rotation=90, ha="center"
        )

        ax.set_xlabel("Focal Length (mm)")
        ax.set_ylabel("Number of Images")
        ax.set_title("Focal Length Distribution")

        # Adjust layout to prevent label cutoff
        fig.tight_layout()

        # Convert matplotlib figure to QPixmap
        canvas = FigureCanvas(fig)
        canvas.draw()

        # Get the RGBA buffer from the figure
        w, h = canvas.get_width_height()
        buf = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8)
        buf.shape = (h, w, 4)  # RGBA has 4 channels

        # Convert RGBA to RGB by dropping the alpha channel
        rgb_buf = buf[:, :, :3].copy()  # Make a copy to ensure contiguous memory

        # Convert to QImage and then QPixmap
        q_image = QImage(rgb_buf.tobytes(), w, h, w * 3, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        # Scale to fit the widget while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.histogram_widget.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.histogram_widget.setPixmap(scaled_pixmap)

    def selectShutterCountImage(self):
        """Select a single image for shutter count analysis."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image for Shutter Count Analysis",
            "",
            "Image Files (*.jpg *.jpeg *.png *.tiff *.tif *.cr2 *.nef *.arw *.dng)",
        )

        if file_path:
            self.shutter_count_image_path = file_path
            # Show only the filename for display
            display_name = os.path.basename(file_path)
            if len(display_name) > 30:
                display_name = "..." + display_name[-27:]
            self.shutter_status_label.setText(f"Selected: {display_name}")

            # Clear the shutter count display
            self.shutter_count_display.setText("--")

            # Automatically start processing
            self.analyzeShutterCounts()

    def analyzeShutterCounts(self):
        """Get shutter count from the selected image using exiftool."""
        if not self.shutter_count_image_path:
            return

        # Show progress
        self.shutter_progress.setVisible(True)
        self.shutter_progress.setRange(0, 0)  # Indeterminate progress
        self.shutter_loading_label.setText("Reading shutter count...")
        self.shutter_loading_label.setVisible(True)
        self.select_shutter_image_button.setEnabled(False)
        self.shutter_status_label.setText("Reading EXIF data... Please wait.")

        try:
            # Use exiftool to get shutter count
            import subprocess

            # Run exiftool command
            result = subprocess.run(
                ["exiftool", "-ShutterCount", self.shutter_count_image_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Parse the output
                output_lines = result.stdout.strip().split("\n")
                shutter_count = None

                for line in output_lines:
                    if "Shutter Count" in line:
                        # Extract the number from the line
                        parts = line.split(":")
                        if len(parts) >= 2:
                            shutter_count = parts[1].strip()
                            break

                if shutter_count:
                    # Display the shutter count in the large number display
                    self.shutter_count_display.setText(shutter_count)
                else:
                    self.shutter_count_display.setText("N/A")
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.shutter_count_display.setText("ERROR")

        except subprocess.TimeoutExpired:
            self.shutter_count_display.setText("TIMEOUT")
        except FileNotFoundError:
            self.shutter_count_display.setText("NO EXIFTOOL")
        except Exception:
            self.shutter_count_display.setText("ERROR")

        # Hide progress and re-enable buttons
        self.shutter_progress.setVisible(False)
        self.shutter_loading_label.setVisible(False)
        self.select_shutter_image_button.setEnabled(True)
        self.shutter_status_label.setText(
            f"Selected: {os.path.basename(self.shutter_count_image_path)}"
        )

    def closeEvent(self, event):
        """Clean up worker threads when closing the window."""
        if self.focal_worker and self.focal_worker.isRunning():
            self.focal_worker.quit()
            self.focal_worker.wait()
        if self.batch_worker and self.batch_worker.isRunning():
            self.batch_worker.quit()
            self.batch_worker.wait()
        if self.shutter_worker and self.shutter_worker.isRunning():
            self.shutter_worker.quit()
            self.shutter_worker.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    sys.exit(app.exec())
