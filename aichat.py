from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
                           QScrollArea, QTextEdit, QHBoxLayout, QComboBox, QLabel, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QColor, QPalette

from ollama import chat as ollama_chat, list as ollama_list

import typing
import json
import os
from typing import List, Dict, Literal

MODEL_OPTIONS = sorted([x.model.split(":")[0] for x in ollama_list().models if x.model])

SAVE_FILE_PATH = os.path.join(os.path.expanduser("~"), "pythonaichatpreferences.json")

def load_save_data() -> dict[str, typing.Any]:
    try:
        with open(SAVE_FILE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_save_data(data: dict[str, typing.Any]):
    print(f"Saving save data to {SAVE_FILE_PATH}")
    print(f"model: {data.get('model')}")
    with open(SAVE_FILE_PATH, "w") as f:
        json.dump(data, f)

loaded_state = load_save_data()
save_data: dict[str, typing.Any] = {}
if (load_model := loaded_state.get("model")):
    print(f"Pre-selecting model from save file: {load_model}")
    save_data["model"] = load_model
del loaded_state # Dont keep the variable loaded

class MessageWidget(QFrame):
    """Widget for displaying a single message"""

    edited = pyqtSignal(str, int)  # Signal to emit when message is edited (new_text, message_id)
    delete_signal = pyqtSignal(int)  # Signal to emit when message is deleted (message_id)

    def __init__(self, text: str, role: str, message_id: int, parent=None):
        super().__init__(parent)
        self.message_id = message_id
        self.role = role

        # Set up the frame appearance
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        # Set background color based on sender
        palette = self.palette()
        if role == "user":
            palette.setColor(QPalette.ColorRole.Base, QColor(15, 67, 91))
        elif role == "assistant":
            palette.setColor(QPalette.ColorRole.Base, QColor(63, 10, 33))
        elif role == "system":
            palette.setColor(QPalette.ColorRole.Base, QColor(10, 10, 10))
        else:
            # Deep red for unknown role
            palette.setColor(QPalette.ColorRole.Base, QColor(200, 0, 0))
            print(f"Unknown role: {role}")
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Create layout
        layout = QVBoxLayout(self)

        # Top Section, Label + Delete button
        top_layout = QHBoxLayout()

        name_label = QLabel(self.role)
        name_label.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(name_label)

        delete_button = QPushButton("🚫")
        delete_button.clicked.connect(self.delete_message)
        delete_button.setFixedWidth(20)
        top_layout.addWidget(delete_button)

        layout.addLayout(top_layout)

        # Add editable text area - using a custom QTextEdit that auto-resizes
        self.text_edit = AutoResizingTextEdit(text)
        self.text_edit.setPlainText(text)
        self.text_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_edit)

        # Set minimum width but allow height to be dynamic
        self.setMinimumWidth(200)

    def on_text_changed(self):
        """Emit signal when text is edited"""
        self.edited.emit(self.text_edit.toPlainText(), self.message_id)

    def delete_message(self):
        """Delete the message"""
        self.delete_signal.emit(self.message_id)


class AutoResizingTextEdit(QTextEdit):
    """A QTextEdit that automatically adjusts its height to fit its content"""

    def __init__(self, text:str="", parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.textChanged.connect(self.adjust_height)

        # Initial adjustment
        QTimer.singleShot(25, self.adjust_height)

    def adjust_height(self):
        """Adjust the height to fit the content"""
        try:
            # Calculate required height
            doc = self.document()
            if doc is not None:
                size = doc.size()
                document_height = size.height()
                margins = self.contentsMargins()
                height = int(document_height + margins.top() + margins.bottom() + 5)  # Add a small buffer

                # Set the height
                self.setMinimumHeight(height)
                self.setMaximumHeight(height)
        except Exception:
            # Fallback if any error occurs
            pass

    def sizeHint(self) -> QSize:
        """Override sizeHint to provide a better default size"""
        size = super().sizeHint()
        try:
            doc = self.document()
            if doc is not None:
                doc_size = doc.size()
                document_height = doc_size.height()
                margins = self.contentsMargins()
                size.setHeight(int(document_height + margins.top() + margins.bottom() + 5))
        except Exception:
            # Fallback if any error occurs
            pass
        return size


class ChatArea(QScrollArea):
    """Scrollable area containing chat messages"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up scroll area properties
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget and layout for messages
        self.container = QWidget()
        self.message_layout = QVBoxLayout(self.container)
        self.message_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.message_layout.setSpacing(10)

        self.setWidget(self.container)

        # Store messages
        self.messages: list[MessageWidget] = []
        self.next_message_id = 0

    def add_message(self, text: str, role: Literal["user", "assistant", "system"]) -> MessageWidget:
        """Add a new message to the chat"""
        if text.lower().startswith("s:"):
            role = "system"
            text = text[2:].strip()
        message_widget = MessageWidget(text, role, self.next_message_id)
        message_widget.edited.connect(self.on_message_edited)
        message_widget.delete_signal.connect(self.on_message_deleted)

        self.message_layout.addWidget(message_widget)
        self.messages.append(message_widget)
        self.next_message_id += 1

        # Defer scrolling to the next event loop cycle after rendering is complete
        QTimer.singleShot(33, self.scroll_to_bottom)

        return message_widget

    def scroll_to_bottom(self):
        """Scroll to the bottom of the chat area"""
        scrollbar = self.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def on_message_edited(self, new_text: str, message_id: int):
        """Handle when a message is edited"""
        # This could be used to update a message store or trigger other actions
        pass

    def on_message_deleted(self, message_id: int):
        """Handle when a message is deleted"""
        # Find the message widget by its ID and remove it from the layout and the messages list
        for i, message_widget in enumerate(self.messages):
            if message_widget.message_id == message_id:
                self.message_layout.removeWidget(message_widget)
                message_widget.deleteLater()  # Properly delete the widget
                del self.messages[i]  # Remove from the messages list
                break


class MainWindow(QMainWindow):
    """Chat window"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Chat Application")
        self.resize(800, 600)

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Chat area (top section)
        self.chat_area = ChatArea()
        main_layout.addWidget(self.chat_area, 1)  # 1 is the stretch factor

        # Bottom area
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)

        # Model selection
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(MODEL_OPTIONS)
        self.model_combo.setCurrentText(save_data.get("model", ""))
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        bottom_layout.addLayout(model_layout)

        # Input area
        input_layout = QHBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Type your message here...")
        self.input_text.setMaximumHeight(100)

        self.button_layout = QVBoxLayout()

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.prompt_button = QPushButton("Prompt")
        self.prompt_button.clicked.connect(self.pull_response)
        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.print_messages)

        self.button_layout.addWidget(self.send_button)
        self.button_layout.addWidget(self.prompt_button)
        self.button_layout.addWidget(self.print_button)

        input_layout.addWidget(self.input_text)
        input_layout.addLayout(self.button_layout)
        bottom_layout.addLayout(input_layout)

        main_layout.addWidget(bottom_widget)

        self.setCentralWidget(main_widget)

        # Add some example messages
        start_with_message = False
        if start_with_message:
            self.chat_area.add_message("Hello! How can I help you today?", role="assistant")

    def send_message(self):
        """Send a message from the input area"""
        message_text = self.input_text.toPlainText().strip()
        if not message_text:
            return

        # Add user message
        self.chat_area.add_message(message_text, role="user")

        # Clear input
        self.input_text.clear()

    def pull_response(self):
        """Send a prompt from the input area"""
        ollama_messages: List[Dict[str, str]] = []
        selected_model = self.model_combo.currentText()

        for message in self.chat_area.messages:
            ollama_messages.append({
                "role": message.role,
                "content": message.text_edit.toPlainText()
            })

        # Create an empty assistant message first
        message_widget = self.chat_area.add_message("", role="assistant")

        response = ollama_chat(
            model=selected_model,
            messages=ollama_messages,
            stream=True
        )

        # Process UI events to ensure the message widget is displayed
        QApplication.processEvents()
        
        str_builder = ""
        for chunk in response:
            if chunk.message.content:
                str_builder += chunk.message.content
                # Update the message text as chunks arrive
                message_widget.text_edit.setPlainText(str_builder)
                # Process UI events to keep the interface responsive
                QApplication.processEvents()
                # Ensure the latest content is visible
                self.chat_area.scroll_to_bottom()

    def print_messages(self):
        """Print the messages to the console"""
        print("--------------------------------")
        for message in self.chat_area.messages:
            print(f"{message.role}: {message.text_edit.toPlainText()}")
        print("--------------------------------")

    def simulate_ai_response(self, user_message, model):
        """Simulate an AI response (for demonstration)"""
        # In a real app, this would call an API
        response = f"You selected the {model} model. This is a simulated response to: '{user_message}'"
        self.chat_area.add_message(response, role="assistant")
    
    def on_model_changed(self, model: str):
        save_data["model"] = model


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
    save_save_data(save_data)


