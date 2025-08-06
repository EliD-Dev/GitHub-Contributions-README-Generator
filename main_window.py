"""
Main window of the GitHub README Generator application
"""
import re
import os
from markdown import markdown

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QTextEdit, QSplitter, QFrame, QMessageBox, QComboBox, QDialog,
    QScrollArea, QApplication
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QUrl

from PyQt6.QtWebEngineWidgets import QWebEngineView

from translation_manager import translator
from config_manager import save_config, load_config, get_user_comments
from github_api import test_github_auth, generate_readme_content
from ui_components import (
    CustomWebEnginePage, open_link_in_browser, 
    show_themed_input_dialog, get_comment_styles
)


class GitHubReadMeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(translator.get_text("app_title"))
        if os.path.exists("images/logo.png"):
            self.setWindowIcon(QIcon("images/logo.png"))
        self.setMinimumSize(1200, 800)

        # Initialisation des attributs
        self.current_theme = "auto"
        self.current_language = "en"
        self.user_configs = {}
        self.last_repos_data = {}
        self.copy_btn_enabled = False
        self.comments_btn_enabled = False
        
        # Initialisation des widgets
        self._init_widgets()
        self.setup_ui()
        self.load_saved_config()
        self.apply_theme(self.current_theme)
        self.update_copy_btn_cursor()
        self.update_comments_btn_cursor()

    def _init_widgets(self):
        """Initialise tous les widgets de l'interface"""
        self.username_input = QComboBox()
        self.username_input.setEditable(True)
        self.username_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.username_input.setMinimumWidth(200)
        
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Language selector
        self.language_selector = QComboBox()
        for code, name in translator.available_languages.items():
            self.language_selector.addItem(name, code)
        self.language_selector.currentTextChanged.connect(self.change_language)

        self.validate_btn = QPushButton(translator.get_text("validate_button"))
        self.validate_btn.clicked.connect(self.on_validate)
        self.validate_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.theme_toggle_btn = QPushButton()
        self.theme_toggle_btn.setFixedWidth(40)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        self.theme_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        self.status_label.setMaximumHeight(20)

        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setStyleSheet("border-radius: 8px;")

        # Create container frame for preview with border
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                border-radius: 6px;
                background-color: white;
            }
        """)
        
        # Layout pour le frame
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(2, 2, 2, 2)
        preview_layout.setSpacing(0)
        
        self.preview = QWebEngineView()
        self.preview.setStyleSheet("border: none; background: transparent; border-radius: 6px;")
        
        # Use custom page
        custom_page = CustomWebEnginePage(self)
        self.preview.setPage(custom_page)
        self.custom_page = custom_page
        
        preview_layout.addWidget(self.preview)

        self.copy_btn = QPushButton(translator.get_text("copy_readme_button"))
        self.copy_btn.clicked.connect(self.copy_readme)
        self.copy_btn.setCursor(Qt.CursorShape.ForbiddenCursor)

        self.comments_btn = QPushButton(translator.get_text("manage_comments_button"))
        self.comments_btn.clicked.connect(self.open_comments_dialog)
        self.comments_btn.setCursor(Qt.CursorShape.ForbiddenCursor)

    def open_link_in_browser(self, url):
        """Delegate link opening to ui_components module"""
        open_link_in_browser(url)

    def change_language(self):
        """Change la langue de l'interface"""
        selected_language = self.language_selector.currentData()
        if selected_language and selected_language != self.current_language:
            self.current_language = selected_language
            translator.set_language(selected_language)
            self.update_ui_texts()
            save_config(
                self.username_input.currentText(),
                self.token_input.text(),
                self.current_theme,
                language=selected_language
            )

    def update_ui_texts(self):
        """Update all interface texts"""
        self.setWindowTitle(translator.get_text("app_title"))
        self.validate_btn.setText(translator.get_text("validate_button"))
        self.copy_btn.setText(translator.get_text("copy_readme_button"))
        self.comments_btn.setText(translator.get_text("manage_comments_button"))
        
        # Update labels with direct references
        if hasattr(self, 'username_label'):
            self.username_label.setText(translator.get_text("username_label"))
        if hasattr(self, 'token_label'):
            self.token_label.setText(translator.get_text("token_label"))
        if hasattr(self, 'language_label'):
            self.language_label.setText(translator.get_text("language_label"))
        
        # Update credit
        if hasattr(self, 'credit_label'):
            if self.current_theme == "dark":
                credit_text = f'{translator.get_text("created_by")} <a href="https://github.com/EliD-Dev" style="color: #3b82f6; text-decoration: none;">EliD-Dev</a>'
            else:
                credit_text = f'{translator.get_text("created_by")} <a href="https://github.com/EliD-Dev" style="color: #0078d7; text-decoration: none;">EliD-Dev</a>'
            self.credit_label.setText(credit_text)

    def update_copy_btn_cursor(self):
        """Update cursor and appearance of copy button according to its state"""
        if self.copy_btn_enabled:
            self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if self.current_theme == "dark":
                self.copy_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3b82f6;
                        color: white;
                        border-radius: 8px;
                        padding: 8px 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #2563eb;
                    }
                    QPushButton:pressed {
                        background-color: #1d4ed8;
                    }
                """)
            else:
                self.copy_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0078d7;
                        color: white;
                        border-radius: 8px;
                        padding: 8px 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #005a9e;
                    }
                    QPushButton:pressed {
                        background-color: #004880;
                    }
                """)
        else:
            self.copy_btn.setCursor(Qt.CursorShape.ForbiddenCursor)
            self.copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #cccccc;
                    color: #666666;
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-weight: bold;
                }
            """)

    def update_comments_btn_cursor(self):
        """Update cursor and appearance of comments button according to its state"""
        if self.comments_btn_enabled:
            self.comments_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if self.current_theme == "dark":
                self.comments_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3b82f6;
                        color: white;
                        border-radius: 8px;
                        padding: 8px 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #2563eb;
                    }
                    QPushButton:pressed {
                        background-color: #1d4ed8;
                    }
                """)
            else:
                self.comments_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0078d7;
                        color: white;
                        border-radius: 8px;
                        padding: 8px 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #005a9e;
                    }
                    QPushButton:pressed {
                        background-color: #004880;
                    }
                """)
        else:
            self.comments_btn.setCursor(Qt.CursorShape.ForbiddenCursor)
            self.comments_btn.setStyleSheet("""
                QPushButton {
                    background-color: #cccccc;
                    color: #666666;
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-weight: bold;
                }
            """)

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QVBoxLayout(self)

        form_layout = QHBoxLayout()
        
        # Create and store label references
        self.username_label = QLabel(translator.get_text("username_label"))
        self.token_label = QLabel(translator.get_text("token_label"))
        self.language_label = QLabel(translator.get_text("language_label"))
        
        form_layout.addWidget(self.username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.token_label)
        form_layout.addWidget(self.token_input)
        form_layout.addWidget(self.language_label)
        form_layout.addWidget(self.language_selector)
        form_layout.addWidget(self.validate_btn)
        form_layout.addWidget(self.theme_toggle_btn)
        layout.addLayout(form_layout)

        layout.addWidget(self.status_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.raw_text)
        splitter.addWidget(self.preview_frame)
        splitter.setSizes([500, 500])
        layout.addWidget(splitter)

        btn_layout = QHBoxLayout() 
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addStretch(2)
        btn_layout.addWidget(self.comments_btn)
        btn_layout.addStretch(1)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        layout.addLayout(btn_layout)

        # Credit at bottom right
        credit_layout = QHBoxLayout()
        credit_layout.addStretch()
        
        credit_text = f'{translator.get_text("created_by")} <a href="https://github.com/EliD-Dev" style="color: #0078d7; text-decoration: none;">EliD-Dev</a>'
        self.credit_label = QLabel(credit_text)
        self.credit_label.setOpenExternalLinks(True)
        self.credit_label.setStyleSheet("color: black; font-size: 11px; margin: 5px 0;")
        self.credit_label.setMaximumHeight(35)
        credit_layout.addWidget(self.credit_label)
        
        layout.addLayout(credit_layout)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        self._apply_base_styles()

    def _apply_base_styles(self):
        """Applique les styles de base"""
        self.setStyleSheet("""
            QWidget {
                font-family: Segoe UI, sans-serif;
                font-size: 13px;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 5px;
            }
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 5px;
                padding-right: 25px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #ccc;
                background-color: #f8f8f8;
            }
            QComboBox::drop-down:hover {
                background-color: #e8e8e8;
            }
            QComboBox::down-arrow {
                image: url(images/arrow-down.svg);
                width: 25px;
                height: 25px;
            }
            QComboBox::down-arrow:disabled {
                background-color: #CCC;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004880;
            }
        """)

    def load_saved_config(self):
        """Load saved configuration"""
        username, username_history, token, theme, language, user_configs = load_config()
        
        # Configure language
        self.current_language = language
        translator.set_language(language)
        
        # Set language selector selection
        for i in range(self.language_selector.count()):
            if self.language_selector.itemData(i) == language:
                self.language_selector.setCurrentIndex(i)
                break
        
        # Remplir le combobox avec l'historique
        self.username_input.clear()
        if username_history:
            self.username_input.addItems(username_history)
        
        # Set current username (most recent)
        if username:
            self.username_input.setCurrentText(username)
        
        self.token_input.setText(token)
        self.current_theme = theme
        self.user_configs = user_configs
        
        # Update texts after loading language
        self.update_ui_texts()

    def refresh_username_combobox(self):
        """Update QComboBox with username history"""
        current_text = self.username_input.currentText()
        username, username_history, _, _, _, user_configs = load_config()
        self.user_configs = user_configs
        
        self.username_input.clear()
        if username_history:
            self.username_input.addItems(username_history)
        
        if current_text:
            self.username_input.setCurrentText(current_text)
        elif username:
            self.username_input.setCurrentText(username)

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.current_theme == "light":
            self.current_theme = "dark"
        else:
            self.current_theme = "light"

        self.apply_theme(self.current_theme)
        # Translate theme name for display
        theme_name = translator.get_text(f"themes.{self.current_theme}")
        self.status_label.setText(translator.get_text("status_messages.theme_changed", theme=theme_name))

    def apply_theme(self, theme):
        """Apply specified theme"""
        base_style = self.styleSheet()

        def inject_preview_css(css_file, bg_color, text_color):
            # Read GitHub CSS for the theme
            with open(css_file, "r", encoding="utf-8") as f:
                github_css = f.read()
            
            # S'assurer qu'il y a du contenu dans le preview avant d'injecter le CSS
            current_content = self.raw_text.toPlainText().strip()
            if not current_content:
                minimal_html = f"""
                <html>
                <head><meta charset='utf-8'></head>
                <body style="background-color: {bg_color}; margin: 8px; padding: 8px; border-radius: 6px;">
                    <div class="markdown-body"></div>
                </body>
                </html>
                """
                self.preview.setHtml(minimal_html, baseUrl=QUrl("https://github.com/"))
            
            # JavaScript to update/inject style
            js = f"""
            (function() {{
                var styleTag = document.getElementById('theme-style');
                if (!styleTag) {{
                    styleTag = document.createElement('style');
                    styleTag.id = 'theme-style';
                    document.head.appendChild(styleTag);
                }}
                styleTag.innerHTML = `{github_css}
                body, .markdown-body {{
                    background-color: {bg_color} !important;
                    color: {text_color} !important;
                }}`;
            }})();
            """
            self.preview.page().runJavaScript(js)

        if theme == "dark":
            css_file = "styles/github-markdown-dark.css"
            self.theme_css_file = css_file
            inject_preview_css(css_file, "#1e1e1e", "#e0e0e0")
            self.theme_toggle_btn.setText("☀️")
            self.setStyleSheet(base_style + """
                QWidget { background-color: #121212; color: #e0e0e0; }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: #1e1e1e;
                    color: white;
                    border: 1px solid #444;
                }
                QComboBox::drop-down {
                    border-left-color: #444;
                    background-color: #2a2a2a;
                }
                QComboBox::drop-down:hover {
                    background-color: #3a3a3a;
                }
                QComboBox::down-arrow {
                    image: url(images/arrow-down-dark.svg);
                }
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
                QPushButton:pressed {
                    background-color: #1d4ed8;
                }
            """)
            self.preview_frame.setStyleSheet("""
                QFrame {
                    border: 1px solid #444;
                    border-radius: 6px;
                    background-color: #1e1e1e;
                }
            """)
            self.credit_label.setStyleSheet("color: #a0a0a0; font-size: 11px; margin: 5px 0;")
        else:
            css_file = "styles/github-markdown-light.css"
            self.theme_css_file = css_file
            inject_preview_css(css_file, "white", "black")
            self.theme_toggle_btn.setText("🌙")
            self.setStyleSheet(base_style + """
                QWidget { background-color: #f0f2f5; color: black; }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: white;
                    color: black;
                    border: 1px solid #ccc;
                }
                QComboBox::drop-down {
                    border-left-color: #ccc;
                    background-color: #f8f8f8;
                }
                QComboBox::drop-down:hover {
                    background-color: #e8e8e8;
                }
                QComboBox::down-arrow {
                    image: url(images/arrow-down.svg);
                }
                QPushButton {
                    background-color: #0078d7;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #005a9e;
                }
                QPushButton:pressed {
                    background-color: #004880;
                }
            """)
            self.preview_frame.setStyleSheet("""
                QFrame {
                    border: 1px solid #ccc;
                    border-radius: 6px;
                    background-color: white;
                }
            """)
            self.credit_label.setStyleSheet("color: black; font-size: 11px; margin: 5px 0;")

        # Update texts and save
        self.update_ui_texts()
        save_config(self.username_input.currentText(), self.token_input.text(), self.current_theme, language=self.current_language)
        self.refresh_username_combobox()
        self.update_copy_btn_cursor()
        self.update_comments_btn_cursor()

    def on_validate(self):
        """Validate credentials and generate README"""
        username = self.username_input.currentText().strip()
        token = self.token_input.text().strip()
        if not username or not token:
            self.status_label.setText(translator.get_text("status_messages.fill_both_fields"))
            return

        self.status_label.setText(translator.get_text("status_messages.validating"))
        QApplication.processEvents()

        if not test_github_auth(username, token):
            self.status_label.setText(translator.get_text("status_messages.invalid_credentials"))
            self.raw_text.clear()
            self.preview.setHtml("<p style='color: red;'>Aucune donnée disponible.</p>")
            self.copy_btn_enabled = False
            self.comments_btn_enabled = False
            self.update_copy_btn_cursor()
            self.update_comments_btn_cursor()
            QMessageBox.critical(self, translator.get_text("errors.invalid_credentials").split('.')[0], 
                               translator.get_text("errors.invalid_credentials"))
            return

        save_config(username, token, self.current_theme, language=self.current_language)
        self.refresh_username_combobox()
        self.status_label.setText(translator.get_text("status_messages.connection_validated"))

        readme_content, repos_data = self.generate_readme(username, token)
        if readme_content:
            self.last_repos_data = repos_data
            self.raw_text.setPlainText(readme_content)
            html = self.get_html_with_github_style(readme_content)
            self.preview.setHtml(html, baseUrl=QUrl("https://github.com/"))
            self.copy_btn_enabled = True
            self.comments_btn_enabled = True
            self.update_copy_btn_cursor()
            self.update_comments_btn_cursor()

    def generate_readme(self, username, token):
        """Generate README content using GitHub API"""
        user_comments = get_user_comments(username, self.user_configs)
        
        readme_content, repos_data = generate_readme_content(username, token, user_comments, translator)
        
        if not readme_content:
            self.status_label.setText(translator.get_text("errors.github_data_error"))
            return "", {}
        
        return readme_content, repos_data

    def get_html_with_github_style(self, markdown_text):
        """Convertit le markdown en HTML avec le style GitHub"""
        html_body = markdown(markdown_text, extensions=['tables', 'fenced_code'])
        
        # Remplacer tous les liens href par onclick qui ouvre dans le navigateur
        def replace_link(match):
            url = match.group(1)
            text = match.group(2)
            return f'<a href="qt-bridge://openurl?url={url}">{text}</a>'
        
        html_body = re.sub(r'<a href="([^"]*)"[^>]*>([^<]*)</a>', replace_link, html_body)
        
        # Ajouter un style pour que le contenu soit transparent et laisse voir le fond du frame
        if self.current_theme == "dark":
            background_style = """
                body {
                    background-color: #1e1e1e;
                    margin: 8px !important;
                    padding: 8px !important;
                    border-radius: 6px !important;
                }
                .markdown-body {
                    background-color: #1e1e1e;
                }
            """
        else:
            background_style = """
                body {
                    background-color: white;
                    margin: 8px !important;
                    padding: 8px !important;
                    border-radius: 6px !important;
                }
                .markdown-body {
                    background-color: white;
                }
            """
            
        if html_body.strip() != "":
            with open(self.theme_css_file, "r", encoding="utf-8") as f:
                github_css = f.read()
            
            fade_style = """
                .markdown-body {
                    animation: fadeIn 0.4s ease-in-out;
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
            """
        else:
            github_css = ""
            fade_style = ""

        html = f"""
        <html>
        <head>
            <meta charset='utf-8'>
            <style>
                {github_css}
                {background_style}
                {fade_style}
            </style>
        </head>
        <body>
            <div class="markdown-body">
                {html_body}
            </div>
        </body>
        </html>
        """
        return html

    def copy_readme(self):
        """Copie le README dans le presse-papiers"""
        if not self.copy_btn_enabled:
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.raw_text.toPlainText())
        self.status_label.setText(translator.get_text("status_messages.readme_copied"))

    def open_comments_dialog(self):
        """Open dialog to manage comments"""
        if not self.comments_btn_enabled:
            return
        
        current_username = self.username_input.currentText().strip()
        if not current_username:
            QMessageBox.warning(self, translator.get_text("warnings.select_username").split('.')[0], 
                               translator.get_text("warnings.select_username"))
            return
        
        if not hasattr(self, 'last_repos_data') or not self.last_repos_data:
            QMessageBox.information(self, translator.get_text("warnings.generate_readme_first").split('.')[0], 
                                   translator.get_text("warnings.generate_readme_first"))
            return
        
        user_comments = get_user_comments(current_username, self.user_configs)
        
        # Create custom dialog class that captures closing
        class CommentsDialog(QDialog):
            def __init__(self, parent):
                super().__init__(parent)
                self.parent_app = parent
                
            def closeEvent(self, event):
                self.parent_app.on_validate()
                super().closeEvent(event)
        
        dialog = CommentsDialog(self)
        dialog.setWindowTitle(translator.get_text("comments_dialog.title", username=current_username))
        dialog.setMinimumSize(800, 600)
        
        styles = get_comment_styles(self.current_theme)
        
        # Apply style to dialog
        dialog.setStyleSheet(f"""
            QDialog {{
                color: {styles['dialog_text']};
            }}
            QLabel {{
                color: {styles['dialog_text']};
            }}
            QScrollArea {{
                background-color: {styles['dialog_bg']};
                border: 1px solid {styles['repo_frame_border']};
                border-radius: 6px;
            }}
        """)
        
        main_layout = QVBoxLayout(dialog)
        
        # Titre et instructions
        title_label = QLabel(translator.get_text("comments_dialog.subtitle", username=current_username))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        instructions = QLabel(translator.get_text("comments_dialog.instructions"))
        instructions.setStyleSheet("color: gray; margin-bottom: 15px;")
        main_layout.addWidget(instructions)
        
        # Scroll area for repository list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Divide repos by categories
        categories = [
            (translator.get_text("categories.profile_git"), self.last_repos_data.get('repos_profile_git', set())),
            (translator.get_text("categories.commit_only"), self.last_repos_data.get('repos_commit_only', set())),
            (translator.get_text("categories.pull_requests"), self.last_repos_data.get('repos_pr_only', set())),
            (translator.get_text("categories.other_contributions"), self.last_repos_data.get('repos_other', set()))
        ]
        
        for category_name, repos_set in categories:
            if not repos_set:
                continue
                
            # Category title
            category_label = QLabel(category_name)
            category_label.setStyleSheet(f"font-weight: bold; font-size: 14px; margin: 15px 0 10px 0; color: {styles['category_color']};")
            scroll_layout.addWidget(category_label)
            
            # List of repositories in this category
            for repo_name, repo_url in sorted(repos_set):
                repo_frame = QFrame()
                repo_frame.setStyleSheet(f"border: 1px solid {styles['repo_frame_border']}; border-radius: 6px; margin: 5px 0; padding: 10px; background-color: {styles['repo_frame_bg']};")
                repo_layout = QHBoxLayout(repo_frame)
                
                # Nom du repository
                repo_label = QLabel(repo_name)
                repo_label.setStyleSheet(f"font-weight: bold; color: {styles['repo_label_color']};")
                repo_layout.addWidget(repo_label)
                
                repo_layout.addStretch()
                
                # Check if comment exists
                current_comment = user_comments.get(repo_name, "")
                
                if current_comment:
                    # Afficher le commentaire existant
                    comment_label = QLabel(f'"{current_comment}"')
                    comment_label.setStyleSheet(f"color: {styles['comment_text_color']}; font-style: italic; margin: 0 10px;")
                    repo_layout.addWidget(comment_label)
                    
                    # Bouton Modifier
                    edit_btn = QPushButton(translator.get_text("comments_dialog.edit_button"))
                    edit_btn.setStyleSheet(f"padding: 5px 10px; background-color: {styles['edit_btn_bg']}; color: white; border: none; border-radius: 4px;")
                    edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    edit_btn.clicked.connect(lambda checked, name=repo_name, comment=current_comment: self.edit_comment(name, comment, user_comments, current_username, dialog))
                    repo_layout.addWidget(edit_btn)
                    
                    # Bouton Supprimer
                    delete_btn = QPushButton(translator.get_text("comments_dialog.delete_button"))
                    delete_btn.setStyleSheet(f"padding: 5px 10px; background-color: {styles['delete_btn_bg']}; color: white; border: none; border-radius: 4px;")
                    delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    delete_btn.clicked.connect(lambda checked, name=repo_name: self.delete_comment(name, user_comments, current_username, dialog))
                    repo_layout.addWidget(delete_btn)
                else:
                    # Bouton Ajouter
                    add_btn = QPushButton(translator.get_text("comments_dialog.add_comment"))
                    add_btn.setStyleSheet(f"padding: 5px 10px; background-color: {styles['add_btn_bg']}; color: white; border: none; border-radius: 4px;")
                    add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    add_btn.clicked.connect(lambda checked, name=repo_name: self.add_comment(name, user_comments, current_username, dialog))
                    repo_layout.addWidget(add_btn)
                
                scroll_layout.addWidget(repo_frame)
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        close_btn = QPushButton(translator.get_text("comments_dialog.close_button"))
        close_btn.setStyleSheet(f"padding: 8px 16px; background-color: {styles['close_btn_bg']}; color: white; border: none; border-radius: 6px; font-weight: bold;")
        
        def close_and_refresh():
            dialog.accept()
            self.on_validate()
            
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(close_and_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        main_layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def add_comment(self, repo_name, user_comments, username, parent_dialog):
        """Ajoute un commentaire pour un repository"""
        styles = get_comment_styles(self.current_theme)
        comment, ok = show_themed_input_dialog(
            parent_dialog, 
            translator.get_text("comments_dialog.add_comment_title"), 
            translator.get_text("comments_dialog.comment_for_repo", repo=repo_name),
            "",
            styles
        )
        if ok and comment.strip():
            user_comments[repo_name] = comment.strip()
            save_config(username, self.token_input.text(), self.current_theme, user_comments, self.current_language)
            self.refresh_username_combobox()
            parent_dialog.accept()
            self.open_comments_dialog()
    
    def edit_comment(self, repo_name, current_comment, user_comments, username, parent_dialog):
        """Modifie un commentaire existant"""
        styles = get_comment_styles(self.current_theme)
        comment, ok = show_themed_input_dialog(
            parent_dialog, 
            translator.get_text("comments_dialog.edit_comment_title"), 
            translator.get_text("comments_dialog.comment_for_repo", repo=repo_name), 
            current_comment,
            styles
        )
        if ok and comment.strip():
            user_comments[repo_name] = comment.strip()
            save_config(username, self.token_input.text(), self.current_theme, user_comments, self.current_language)
            self.refresh_username_combobox()
            parent_dialog.accept()
            self.open_comments_dialog()
    
    def delete_comment(self, repo_name, user_comments, username, parent_dialog):
        """Supprime un commentaire"""
        msg_box = QMessageBox(parent_dialog)
        msg_box.setWindowTitle(translator.get_text("comments_dialog.delete_confirm_title"))
        msg_box.setText(translator.get_text("comments_dialog.delete_confirm_message", repo=repo_name))
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        yes_btn = msg_box.addButton(translator.get_text("dialog_buttons.yes"), QMessageBox.ButtonRole.YesRole)
        no_btn = msg_box.addButton(translator.get_text("dialog_buttons.no"), QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(no_btn)
        
        msg_box.exec()
        clicked_button = msg_box.clickedButton()
        
        if clicked_button == yes_btn:
            if repo_name in user_comments:
                del user_comments[repo_name]
            save_config(username, self.token_input.text(), self.current_theme, user_comments, self.current_language)
            self.refresh_username_combobox()
            parent_dialog.accept()
            self.open_comments_dialog()
            