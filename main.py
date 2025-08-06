"""
Entry point for the GitHub README Generator application
"""
import sys
from PyQt6.QtWidgets import QApplication
from main_window import GitHubReadMeApp


def main():
    """Main application function"""
    app = QApplication(sys.argv)
    app.setApplicationName("GitHub Contributions README Generator")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("EliD-Dev")
    app.setOrganizationDomain("github.com/EliD-Dev")
    
    window = GitHubReadMeApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()