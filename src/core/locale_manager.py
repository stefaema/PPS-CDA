# src/core/locale_manager.py
import json
import os
from typing import Dict, Any
import importlib.resources as pkg_resources
from core.log_manager import logger
I18N_PACKAGE_REF = pkg_resources.files('i18n')

DEFAULT_LOCALE = 'es'
FALLBACK_LOCALE = 'en'

class LocaleManager:
    """
    Manages locale settings and provides robust translation services.
    Implements the Configuration File Translation Strategy.
    """
    
    def __init__(self):
        """Initializes the manager, loading the default locale."""
        self._current_locale: str = DEFAULT_LOCALE
        self._translations: Dict[str, str] = {}
        self._fallback_translations: Dict[str, str] = {}
        
        # Load fallback first for robustness
        self._fallback_translations = self._load_translations(FALLBACK_LOCALE)
        
        # Load initial current locale (might be the same as fallback)
        if DEFAULT_LOCALE != FALLBACK_LOCALE:
            self.set_locale(DEFAULT_LOCALE)
        else:
            self._translations = self._fallback_translations


        logger.info(f"LocaleManager initialized. Current: {self._current_locale}. Fallback loaded: {FALLBACK_LOCALE}")

    def _load_translations(self, locale: str) -> Dict[str, str]:
        """
        Loads translations for a specific locale from a JSON file using 
        importlib.resources for robust path handling.
        """
        if I18N_PACKAGE_REF is None:
            logger.error("importlib.resources.files not available. Please use Python 3.9+.")
            return {}
        
        file_name = f'{locale}.json'
        
        try:
            # 1. Access the resource file within the package
            file_path = I18N_PACKAGE_REF / file_name
            
            # 2. Open and read the content stream
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise TypeError("Translation file root must be a dictionary.")
                logger.info(f"Loaded translations for locale '{locale}'.")
                return data
        except FileNotFoundError:
            logger.warning(f"Translation resource not found for locale '{locale}' ({file_name}).")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in file for locale '{locale}': {e}")
            return {}
        except AttributeError:
            # Catch errors if I18N_PACKAGE_REF is somehow invalid (e.g., package not found)
            logger.error(f"Resource reference is invalid or package 'i18n' not found.")
            return {}
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading locale '{locale}': {e}")
            return {}

    def set_locale(self, locale: str) -> None:
        """
        Attempts to change the current locale. Falls back to the previous locale 
        and prints a warning if the new locale file cannot be loaded.
        """
        new_translations = self._load_translations(locale)
        
        if new_translations:
            self._translations = new_translations
            self._current_locale = locale
        else:
            logger.warning(f"Could not load locale '{locale}'. Sticking to '{self._current_locale}'.")

    @property
    def current_locale(self) -> str:
        """Returns the currently active locale identifier."""
        return self._current_locale

    def T(self, key: str, **kwargs: Any) -> str:
        """
        The core translation function.
        
        Retrieves the translated string for a given key. Supports variable interpolation
        using standard Python string formatting (e.g., f-string style keys).
        
        Args:
            key: The identifier key for the string to translate.
            **kwargs: Variables for string interpolation (e.g., T('welcome', name='User')).

        Returns:
            The translated string, or a fallback message if the key is missing.

        Examples:
            >>> # If 'greeting' is 'Hello {name}'
            >>> T('greeting', name='Alice')
            'Hello Alice'
            
            >>> # If 'button_ok' is 'OK'
            >>> T('button_ok')
            'OK'
        """
        
        # 1. Look up in current locale
        translated_string = self._translations.get(key)
        
        # 2. Look up in fallback locale if key is missing
        if translated_string is None:
            translated_string = self._fallback_translations.get(key)
            if translated_string is None:
                # 3. Last resort: Return the key itself as an indication of missing translation
                logger.warning(f"Missing translation key '{key}' in both current and fallback locales.")
                return f"!! {key} !!"

        # 4. Perform string formatting if kwargs are provided
        if kwargs:
            try:
                # Use .format() for interpolation
                return translated_string.format(**kwargs)
            except KeyError as e:
                # Handle case where the translation string has an unexpected placeholder
                logger.error(f"Missing format key {e} for translation key '{key}' in locale '{self._current_locale}'.")
                return translated_string
            except Exception as e:
                # Catch other formatting errors (e.g., incorrect type)
                logger.error(f"Formatting failed for key '{key}' in locale '{self._current_locale}': {e}")
                return translated_string

        # 5. Return the raw string if no formatting is needed
        return translated_string

# Create a globally accessible singleton instance
global_locale_manager = LocaleManager()

# Define the short alias for translation for ease of use in UI files
T = global_locale_manager.T
