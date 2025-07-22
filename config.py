"""Configuration management for the karaoke player.

This module handles application settings, themes, and user preferences.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from pathlib import Path
from rich.style import Style
from rich.color import Color


@dataclass
class ThemeConfig:
    """Theme configuration for the karaoke player."""
    name: str
    background: str
    primary: str
    secondary: str
    accent: str
    text_primary: str
    text_secondary: str
    text_highlight: str
    text_active: str
    progress_complete: str
    progress_remaining: str
    border: str
    panel_background: str


@dataclass
class DisplayConfig:
    """Display configuration settings."""
    show_progress_bar: bool = True
    show_time_info: bool = True
    show_next_sentence: bool = True
    show_previous_sentence: bool = False
    highlight_duration: int = 800
    scroll_speed: int = 1
    max_visible_sentences: int = 5
    center_current_sentence: bool = True
    show_word_count: bool = False
    show_sentence_numbers: bool = False


@dataclass
class AudioConfig:
    """Audio configuration settings."""
    enable_audio: bool = False
    volume: float = 0.7
    audio_format: str = "mp3"
    audio_directory: str = "audio"
    auto_play: bool = True
    fade_in_duration: int = 1000
    fade_out_duration: int = 1000


@dataclass
class AppConfig:
    """Main application configuration."""
    theme: str = "default"
    display: DisplayConfig = None
    audio: AudioConfig = None
    lyrics_directory: str = "lyrics"
    auto_save_settings: bool = True
    check_for_updates: bool = True
    language: str = "vi"
    
    def __post_init__(self):
        if self.display is None:
            self.display = DisplayConfig()
        if self.audio is None:
            self.audio = AudioConfig()


class ConfigManager:
    """Manages application configuration and themes."""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = Path(config_file)
        self.themes = self._load_default_themes()
        self.config = self._load_config()
    
    def _load_default_themes(self) -> Dict[str, ThemeConfig]:
        """Load default themes.
        
        Returns:
            Dictionary of theme configurations
        """
        return {
            "default": ThemeConfig(
                name="Default",
                background="black",
                primary="blue",
                secondary="cyan",
                accent="magenta",
                text_primary="white",
                text_secondary="bright_white",
                text_highlight="yellow",
                text_active="bright_yellow",
                progress_complete="green",
                progress_remaining="white",
                border="blue",
                panel_background="grey11"
            ),
            "dark": ThemeConfig(
                name="Dark",
                background="grey3",
                primary="bright_blue",
                secondary="bright_cyan",
                accent="bright_magenta",
                text_primary="bright_white",
                text_secondary="white",
                text_highlight="bright_yellow",
                text_active="gold1",
                progress_complete="bright_green",
                progress_remaining="grey50",
                border="bright_blue",
                panel_background="grey7"
            ),
            "neon": ThemeConfig(
                name="Neon",
                background="black",
                primary="bright_magenta",
                secondary="bright_cyan",
                accent="bright_green",
                text_primary="bright_white",
                text_secondary="bright_cyan",
                text_highlight="bright_yellow",
                text_active="bright_red",
                progress_complete="bright_green",
                progress_remaining="grey30",
                border="bright_magenta",
                panel_background="grey11"
            ),
            "pastel": ThemeConfig(
                name="Pastel",
                background="grey93",
                primary="medium_purple3",
                secondary="light_sky_blue3",
                accent="light_pink3",
                text_primary="grey19",
                text_secondary="grey37",
                text_highlight="dark_orange3",
                text_active="red3",
                progress_complete="medium_spring_green",
                progress_remaining="grey70",
                border="medium_purple3",
                panel_background="grey89"
            )
        }
    
    def _load_config(self) -> AppConfig:
        """Load configuration from file or create default.
        
        Returns:
            Application configuration
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert nested dictionaries back to dataclasses
                display_data = data.get('display', {})
                audio_data = data.get('audio', {})
                
                return AppConfig(
                    theme=data.get('theme', 'default'),
                    display=DisplayConfig(**display_data),
                    audio=AudioConfig(**audio_data),
                    lyrics_directory=data.get('lyrics_directory', 'lyrics'),
                    auto_save_settings=data.get('auto_save_settings', True),
                    check_for_updates=data.get('check_for_updates', True),
                    language=data.get('language', 'vi')
                )
            except (json.JSONDecodeError, TypeError, KeyError):
                # If config is corrupted, create default
                pass
        
        return AppConfig()
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        if not self.config.auto_save_settings:
            return
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
        except IOError:
            pass  # Silently fail if can't save
    
    def get_theme(self, theme_name: Optional[str] = None) -> ThemeConfig:
        """Get theme configuration.
        
        Args:
            theme_name: Name of the theme, or None for current theme
            
        Returns:
            Theme configuration
        """
        if theme_name is None:
            theme_name = self.config.theme
        
        return self.themes.get(theme_name, self.themes['default'])
    
    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme.
        
        Args:
            theme_name: Name of the theme to set
            
        Returns:
            True if theme was set successfully
        """
        if theme_name in self.themes:
            self.config.theme = theme_name
            self.save_config()
            return True
        return False
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get list of available themes.
        
        Returns:
            Dictionary mapping theme keys to display names
        """
        return {key: theme.name for key, theme in self.themes.items()}
    
    def update_display_config(self, **kwargs) -> None:
        """Update display configuration.
        
        Args:
            **kwargs: Display configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config.display, key):
                setattr(self.config.display, key, value)
        self.save_config()
    
    def update_audio_config(self, **kwargs) -> None:
        """Update audio configuration.
        
        Args:
            **kwargs: Audio configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config.audio, key):
                setattr(self.config.audio, key, value)
        self.save_config()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = AppConfig()
        self.save_config()