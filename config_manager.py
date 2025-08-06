"""
Configuration manager - saving and loading user settings
"""
import os
import json
import base64

CONFIG_FILE = "config.json"


def save_config(username, token, theme, user_comments=None, language=None):
    """Save user configuration to JSON file"""
    existing_data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            existing_data = {}
    
    # Manage username history
    username_history = existing_data.get("username_history", [])
    
    if username in username_history:
        username_history.remove(username)
    
    username_history.insert(0, username)
    username_history = username_history[:10]  # Limit to 10 entries
    
    # Manage comments per user
    user_configs = existing_data.get("user_configs", {})
    if user_comments is not None:
        user_configs[username] = user_configs.get(username, {})
        user_configs[username]["comments"] = user_comments
    
    data = {
        "username": username,
        "username_history": username_history,
        "token": base64.b64encode(token.encode()).decode(),
        "theme": theme,
        "language": language if language is not None else existing_data.get("language", "en"),
        "user_configs": user_configs
    }
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_config():
    """Load configuration from JSON file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            username = data.get("username", "")
            username_history = data.get("username_history", [])
            token_enc = data.get("token", "")
            theme = data.get("theme", "light")
            language = data.get("language", "en")  # Default English
            user_configs = data.get("user_configs", {})
            token = base64.b64decode(token_enc.encode()).decode() if token_enc else ""
            return username, username_history, token, theme, language, user_configs
        except (json.JSONDecodeError, OSError):
            return "", [], "", "light", "en", {}
    return "", [], "", "light", "en", {}


def get_user_comments(username, user_configs):
    """Get user-specific comments"""
    return user_configs.get(username, {}).get("comments", {})
