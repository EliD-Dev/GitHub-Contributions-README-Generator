"""
Reusable UI components
"""
import webbrowser
import urllib.parse
from PyQt6.QtWidgets import QInputDialog
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import Qt


class CustomWebEnginePage(QWebEnginePage):
    """Custom web page to intercept links"""
    def __init__(self, parent_app):
        super().__init__()
        self.parent_app = parent_app
        
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        url_str = url.toString()
        # Intercept qt-bridge calls
        if url_str.startswith("qt-bridge://openurl"):
            parsed = urllib.parse.urlparse(url_str)
            query = urllib.parse.parse_qs(parsed.query)
            if 'url' in query:
                external_url = query['url'][0]
                self.parent_app.open_link_in_browser(external_url)
            return False
        # Allow normal loading
        elif navigation_type == QWebEnginePage.NavigationType.NavigationTypeTyped:
            return True
        elif navigation_type == QWebEnginePage.NavigationType.NavigationTypeReload:
            return True
        return True


def open_link_in_browser(url):
    """Open links in default browser instead of preview widget"""
    if isinstance(url, str):
        webbrowser.open(url)
    elif hasattr(url, 'toString'):
        webbrowser.open(url.toString())
    else:
        webbrowser.open(str(url))


def show_themed_input_dialog(parent, title, label, default_text="", styles=None):
    """Show themed input dialog"""
    if styles is None:
        styles = {
            'dialog_bg': 'white',
            'dialog_text': 'black',
            'repo_frame_bg': '#f9f9f9',
            'repo_frame_border': '#ddd',
            'close_btn_bg': '#0078d7',
            'edit_btn_bg': '#ffc107'
        }
    
    input_dialog = QInputDialog(parent)
    input_dialog.setWindowTitle(title)
    input_dialog.setLabelText(label)
    input_dialog.setTextValue(default_text)
    
    # Appliquer le style selon le thème
    input_dialog.setStyleSheet(f"""
        QInputDialog {{
            background-color: {styles['dialog_bg']};
            color: {styles['dialog_text']};
        }}
        QLabel {{
            color: {styles['dialog_text']};
        }}
        QLineEdit {{
            background-color: {styles['repo_frame_bg']};
            color: {styles['dialog_text']};
            border: 1px solid {styles['repo_frame_border']};
            border-radius: 4px;
            padding: 5px;
        }}
        QPushButton {{
            background-color: {styles['close_btn_bg']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {styles['edit_btn_bg']};
        }}
    """)
    
    ok = input_dialog.exec()
    text = input_dialog.textValue()
    
    return text, ok == QInputDialog.DialogCode.Accepted


def get_comment_styles(current_theme):
    """Return styles for comment management according to current theme"""
    if current_theme == "dark":
        return {
            'dialog_bg': '#1e1e1e',
            'dialog_text': '#e0e0e0',
            'category_color': '#3b82f6',
            'repo_frame_bg': '#2a2a2a',
            'repo_frame_border': '#444',
            'repo_label_color': '#e0e0e0',
            'comment_text_color': '#a0a0a0',
            'add_btn_bg': '#22c55e',
            'edit_btn_bg': '#f59e0b',
            'delete_btn_bg': '#ef4444',
            'close_btn_bg': '#3b82f6'
        }
    else:
        return {
            'dialog_bg': 'white',
            'dialog_text': 'black',
            'category_color': '#0078d7',
            'repo_frame_bg': '#f9f9f9',
            'repo_frame_border': '#ddd',
            'repo_label_color': '#333',
            'comment_text_color': '#666',
            'add_btn_bg': '#28a745',
            'edit_btn_bg': '#ffc107',
            'delete_btn_bg': '#dc3545',
            'close_btn_bg': '#0078d7'
        }
