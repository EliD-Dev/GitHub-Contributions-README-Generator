"""
Multilingual translation manager
"""
import os
import json


class TranslationManager:
    """Multilingual translation manager"""
    def __init__(self):
        self.current_language = "en"  # Default language: English
        self.translations = {}
        self.available_languages = {
            "en": "English",
            "fr": "Français", 
            "es": "Español"
        }
        self.load_translations()
    
    def load_translations(self):
        """Load all available translations"""
        translations_dir = "translations"
        if not os.path.exists(translations_dir):
            os.makedirs(translations_dir)
        
        for lang_code in self.available_languages.keys():
            translation_file = os.path.join(translations_dir, f"{lang_code}.json")
            try:
                if os.path.exists(translation_file):
                    with open(translation_file, "r", encoding="utf-8") as f:
                        self.translations[lang_code] = json.load(f)
                else:
                    # Fallback to English if file doesn't exist
                    self.translations[lang_code] = {}
            except Exception:
                self.translations[lang_code] = {}
    
    def set_language(self, language_code):
        """Change current language"""
        if language_code in self.available_languages:
            self.current_language = language_code
    
    def _navigate_translation_keys(self, translation_dict, keys):
        """Navigate through nested translation structure"""
        current = translation_dict
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _get_fallback_translation(self, keys):
        """Get fallback translation in English"""
        fallback_dict = self.translations.get("en", {})
        return self._navigate_translation_keys(fallback_dict, keys)
    
    def _format_translation(self, translation, **kwargs):
        """Format translation with provided parameters"""
        if not isinstance(translation, str) or not kwargs:
            return translation
        
        try:
            return translation.format(**kwargs)
        except KeyError:
            return translation
    
    def get_text(self, key, **kwargs):
        """Get translated text with support for nested keys and formatting"""
        keys = key.split('.')
        
        # Try current language
        current_lang_dict = self.translations.get(self.current_language, {})
        translation = self._navigate_translation_keys(current_lang_dict, keys)
        
        # Fallback to English if needed
        if translation is None:
            translation = self._get_fallback_translation(keys)
        
        # If no translation found, return the key
        if translation is None:
            return key
        
        # Format and return
        formatted = self._format_translation(translation, **kwargs)
        return formatted if isinstance(formatted, str) else key


# Global instance of translation manager
translator = TranslationManager()
