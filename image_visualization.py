import os
import shutil
import json
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton, QScrollArea, QLabel
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QFileSystemWatcher
import sys


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gallery")
        self.setWindowIcon(QIcon('WindowIcon/qt.png'))
        self.resize(1000, 850)

        self.setStyleSheet(""" 
                            QWidget {
                                background-color: #DDEFE3;
                            }
                            QPushButton {
                                    background-color: #87CEEB;
                                    color: black;
                                    padding: 8px 16px;
                                    border: none;
                                    font-weight: bold;
                                    font-size: 14px;
                                }
                                QPushButton:hover {
                                    background-color: #ADD8E6;
                                    cursor: pointer;
                                }
                                QScrollArea {
                                    border: 1px solid #ccc;
                                }
                                QLabel {
                                    background-color: #DDEFE3;
                                    border: 0.5px solid #ccc;
                                    margin: 10px;
                                }
                            """)

        main_layout = QVBoxLayout()
        scroll_layout = QHBoxLayout()

        self.left_scroll_area = QScrollArea()
        self.left_scroll_area.setWidgetResizable(True)
        self.right_scroll_area = QScrollArea()
        self.right_scroll_area.setWidgetResizable(True)

        self.left_widget = QWidget()
        self.left_layout = QGridLayout(self.left_widget)
        self.right_widget = QWidget()
        self.right_layout = QGridLayout(self.right_widget)

        self.left_widget.setLayout(self.left_layout)
        self.right_widget.setLayout(self.right_layout)
        self.left_scroll_area.setWidget(self.left_widget)
        self.right_scroll_area.setWidget(self.right_widget)

        scroll_layout.addWidget(self.left_scroll_area, 2)
        scroll_layout.addWidget(self.right_scroll_area, 1)

        main_layout.addLayout(scroll_layout)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Image")
        self.add_button.clicked.connect(self.save_image)
        self.select_folder = QPushButton("Select Folder")
        self.select_folder.clicked.connect(self.select_image_folder)
        self.delete_button = QPushButton("Delete Image")
        self.delete_button.clicked.connect(self.delete_image)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.select_folder)
        button_layout.addWidget(self.delete_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.image_folder = None
        self.selected_image_label = None
        self.selected_image_file = None

        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.directoryChanged.connect(self.change_folder)

        self.load_settings()
        self.display_image()

    def select_image_folder(self):
        selected_folder = QFileDialog.getExistingDirectory(self, "Select an image folder")
        if selected_folder:
            self.image_folder = selected_folder
            self.update_image()
            self.save_settings()

            if self.selected_image_label:
                self.selected_image_label.setStyleSheet('')
                self.selected_image_label = None
                self.selected_image_file = None

            self.file_watcher.addPath(self.image_folder)

    def save_image(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images(*.png *.jpg *.jpeg)")

        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            file_name = os.path.basename(file_path)

            destination_folder = self.image_folder
            destination_path = os.path.join(destination_folder, file_name)

            shutil.copy2(file_path, destination_path)
            os.utime(destination_path, None)
            self.update_image()

            if self.selected_image_label:
                self.selected_image_label.setStyleSheet('')
                self.selected_image_label = None
                self.selected_image_file = None

    def select_image_click(self, label, file):
        if self.selected_image_label == label:
            self.selected_image_label.setStyleSheet('')
            self.selected_image_label = None
            self.selected_image_file = None

        else:
            if self.selected_image_label:
                self.selected_image_label.setStyleSheet('')
            self.selected_image_label = label
            self.selected_image_file = file
            self.selected_image_label.setStyleSheet('border: 2px solid red')

    def delete_image(self):
        if self.selected_image_label and self.selected_image_file:
            os.remove(self.selected_image_file)
            self.left_layout.removeWidget(self.selected_image_label)
            self.selected_image_label.deleteLater()
            self.selected_image_label = None
            self.selected_image_file = None
            self.update_image()

    def display_image(self):
        self.auto_left_layout_reload()

        if self.image_folder is None or not os.path.exists(self.image_folder):
            return

        image_files = [file for file in os.listdir(self.image_folder) if file.endswith((".jpg", ".png", ".jpeg"))]

        image_files.sort(key=lambda file: os.path.getmtime(os.path.join(self.image_folder, file)), reverse=True)

        row = 0
        col = 0

        title_label = QLabel("Photo Gallery")
        title_label.setStyleSheet('font-weight: bold; font-size: 28px')
        title_label.setAlignment(Qt.AlignCenter)
        self.left_layout.addWidget(title_label, row, col, 1, 3)
        row += 2

        for image_file in image_files:
            image_path = os.path.join(self.image_folder, image_file)
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio)

            image_label = QLabel()
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            image_label.mousePressEvent = lambda event, label=image_label, file=image_path: self.select_image_click(
                label, file)
            self.left_layout.addWidget(image_label, row, col)

            name_label = QLabel(os.path.splitext(image_file)[0])
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("font-size: 14px; font-weight: bold")
            self.left_layout.addWidget(name_label, row + 1, col)

            col += 1

            if col == 3:
                col = 0
                row += 2
        self.display_recent_image()

    def display_recent_image(self):
        self.auto_right_layout_reload()

        if self.image_folder is None or not os.path.exists(self.image_folder):
            return

        image_files = [file for file in os.listdir(self.image_folder) if file.endswith((".jpg", ".png", ".jpeg"))]
        image_files.sort(key=lambda file: os.path.getmtime(os.path.join(self.image_folder, file)), reverse=True)

        row = 0
        col = 0

        title_label = QLabel("Recent Images")
        title_label.setStyleSheet('font-weight: bold; font-size: 20px')
        title_label.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(title_label, row, col, 1, 2)
        row += 2

        for image_file in image_files:
            image_path = os.path.join(self.image_folder, image_file)
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio)

            image_label = QLabel()
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            image_label.mousePressEvent = lambda event, label=image_label, file=image_path: self.select_image_click(
                label, file)
            self.right_layout.addWidget(image_label, row, col)

            name_label = QLabel(os.path.splitext(image_file)[0])
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("font-size: 14px; font-weight: bold")
            self.right_layout.addWidget(name_label, row+1, col)

            col += 1

            if col == 2:
                col = 0
                row += 2

            if row == 8:
                break

    def update_image(self):
        self.display_image()

    def auto_left_layout_reload(self):
        while self.left_layout.count():
            auto_load = self.left_layout.takeAt(0)
            if auto_load.widget():
                auto_load.widget().deleteLater()

    def auto_right_layout_reload(self):
        while self.right_layout.count():
            auto_load = self.right_layout.takeAt(0)
            if auto_load.widget():
                auto_load.widget().deleteLater()

    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as file:
                settings = json.load(file)
                self.image_folder = settings.get("image_folder")

    def save_settings(self):
        settings = {"image_folder": self.image_folder}
        with open("settings.json", "w") as file:
            json.dump(settings, file)

    def change_folder(self):
        self.update_image()


if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec_())
