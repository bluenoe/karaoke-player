#!/usr/bin/env python3
"""
Karaoke Rich - A terminal-based karaoke application with synchronized lyrics.

This application provides a rich terminal interface for karaoke playback with
real-time lyrics synchronization, audio support, themes, and beautiful visual effects.
"""

import sys
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.align import Align
from rich.layout import Layout
from rich.live import Live
from rich.columns import Columns
from rich import box

from lyrics_data import LyricsLoader, Song
from karaoke_player import KaraokePlayer
from layout_builder import KaraokeLayoutBuilder
from config import ConfigManager
from audio_player import create_audio_player


class KaraokeApp:
    """Main application class for the Karaoke Rich terminal application.
    
    This class manages the overall application flow, user interface,
    audio integration, configuration, and coordinates between different components.
    """
    
    def __init__(self):
        """Initialize the Karaoke application."""
        self.console = Console()
        self.config_manager = ConfigManager()
        self.lyrics_loader = LyricsLoader()
        self.player = KaraokePlayer(
            console=self.console,
            config_manager=self.config_manager
        )
        self.layout_builder = self.player.layout_builder
        self.current_song: Optional[Song] = None
        self.audio_files: Dict[str, str] = {}  # Map song names to audio file paths
        
        # Set up callbacks
        self.player.on_song_end = self._on_song_end
        self.player.on_error = self._on_error
    
    def run(self) -> None:
        """Run the main application loop."""
        try:
            self._show_welcome()
            self._scan_audio_files()
            self._main_menu()
        except KeyboardInterrupt:
            self.console.print("\n[bold red]👋 Goodbye![/bold red]")
        except Exception as e:
            self.console.print(f"[bold red]❌ Error: {e}[/bold red]")
        finally:
            self._cleanup()
            self.console.print("[dim]Thank you for using Karaoke Rich![/dim]")
    
    def _show_welcome(self) -> None:
        """Display the welcome screen with theme support."""
        welcome_layout = self.layout_builder.create_welcome_panel()
        self.console.print(welcome_layout)
        time.sleep(2)
    
    def _main_menu(self) -> None:
        """Display and handle the main menu with enhanced options."""
        while True:
            self.console.clear()
            self._show_welcome()
            
            # Get available songs
            song_files = self.lyrics_loader.list_available_songs()
            
            if not song_files:
                self.console.print("[bold red]❌ No songs found![/bold red]")
                return
            
            # Convert to song info format
            songs = []
            for filename in song_files:
                song_info = self.lyrics_loader.get_song_info(filename)
                if song_info:
                    song_info['filename'] = filename
                    songs.append(song_info)
                else:
                    songs.append({
                        'title': 'Unknown',
                        'artist': 'Unknown',
                        'filename': filename
                    })
            
            # Display main menu options
            self._display_main_menu(songs)
            
            # Get user choice
            choice = self._get_main_menu_choice()
            
            if choice == "exit":
                break
            elif choice == "play":
                self._song_selection_menu(songs)
            elif choice == "settings":
                self._settings_menu()
            elif choice == "themes":
                self._theme_menu()
            elif choice == "audio":
                self._audio_menu()
            else:
                self.console.print("[bold red]❌ Invalid choice![/bold red]")
                time.sleep(1)
    
    def _display_main_menu(self, songs: list) -> None:
        """Display the main menu options.
        
        Args:
            songs: List of available songs
        """
        # Display song list
        song_table = self.layout_builder.create_song_list_table(songs)
        self.console.print(song_table)
        
        # Display menu options
        menu_options = Table(title="🎮 Main Menu", box=box.ROUNDED)
        menu_options.add_column("Option", style="cyan", width=10)
        menu_options.add_column("Description", style="white")
        
        menu_options.add_row("[bold green]play[/bold green]", "🎵 Select and play a song")
        menu_options.add_row("[bold blue]settings[/bold blue]", "⚙️ Application settings")
        menu_options.add_row("[bold magenta]themes[/bold magenta]", "🎨 Change theme")
        menu_options.add_row("[bold yellow]audio[/bold yellow]", "🔊 Audio settings")
        menu_options.add_row("[bold red]exit[/bold red]", "👋 Exit application")
        
        self.console.print(menu_options)
    
    def _get_main_menu_choice(self) -> str:
        """Get and validate main menu choice.
        
        Returns:
            User's choice as string
        """
        choice = Prompt.ask(
            "\n🎯 Choose an option",
            choices=["play", "settings", "themes", "audio", "exit"],
            default="play"
        )
        return choice
    
    def _scan_audio_files(self) -> None:
        """Scan for audio files and map them to songs."""
        audio_dir = Path("audio")
        if audio_dir.exists():
            for audio_file in audio_dir.glob("*"):
                if audio_file.suffix.lower() in ['.mp3', '.wav', '.ogg', '.m4a']:
                    song_name = audio_file.stem
                    self.audio_files[song_name] = str(audio_file)
    
    def _song_selection_menu(self, songs: list) -> None:
        """Handle song selection and playback."""
        song_table = self.layout_builder.create_song_list_table(songs)
        self.console.print(song_table)
        
        choice = Prompt.ask(
            "\n🎵 Select a song (number) or 'back' to return",
            choices=[str(i) for i in range(1, len(songs) + 1)] + ['back']
        )
        
        if choice != 'back':
            song_index = int(choice) - 1
            song_info = songs[song_index]
            self._play_selected_song(song_info)
    
    def _play_selected_song(self, song_info: dict) -> None:
        """Play the selected song."""
        filename = song_info['filename']
        song = self.lyrics_loader.load_song(filename)
        
        if song:
            # Check for audio file
            audio_file = self.audio_files.get(filename)
            self.player.play_song(song, audio_file)
    
    def _settings_menu(self) -> None:
        """Display and handle settings menu."""
        while True:
            self.console.clear()
            
            settings_table = Table(title="⚙️ Settings", box=box.ROUNDED)
            settings_table.add_column("Setting", style="cyan")
            settings_table.add_column("Current Value", style="green")
            settings_table.add_column("Description", style="white")
            
            config = self.config_manager.config
            settings_table.add_row(
                "Refresh Rate", 
                f"{config.display.refresh_rate} Hz", 
                "Display refresh rate"
            )
            settings_table.add_row(
                "Show Progress Bar", 
                "Yes" if config.display.show_progress_bar else "No", 
                "Show progress bar during playback"
            )
            settings_table.add_row(
                "Show Time Info", 
                "Yes" if config.display.show_time_info else "No", 
                "Show time information"
            )
            settings_table.add_row(
                "Max Visible Sentences", 
                str(config.display.max_visible_sentences), 
                "Maximum sentences to display"
            )
            
            self.console.print(settings_table)
            
            choice = Prompt.ask(
                "\n🔧 What would you like to change?",
                choices=["refresh", "progress", "time", "sentences", "back"],
                default="back"
            )
            
            if choice == "back":
                break
            elif choice == "refresh":
                self._change_refresh_rate()
            elif choice == "progress":
                self._toggle_progress_bar()
            elif choice == "time":
                self._toggle_time_info()
            elif choice == "sentences":
                self._change_max_sentences()
    
    def _theme_menu(self) -> None:
        """Display and handle theme selection."""
        while True:
            self.console.clear()
            
            # Display current theme
            current_theme = self.layout_builder.get_current_theme_name()
            self.console.print(f"[bold cyan]🎨 Current Theme: {current_theme}[/bold cyan]\n")
            
            # Display available themes
            themes = self.layout_builder.get_available_themes()
            theme_table = Table(title="Available Themes", box=box.ROUNDED)
            theme_table.add_column("#", style="cyan", width=3)
            theme_table.add_column("Theme Name", style="magenta")
            theme_table.add_column("Description", style="white")
            
            for i, theme_name in enumerate(themes, 1):
                theme_table.add_row(
                    str(i), 
                    theme_name.title(), 
                    f"Switch to {theme_name} theme"
                )
            
            self.console.print(theme_table)
            
            choices = [str(i) for i in range(1, len(themes) + 1)] + ["back"]
            choice = Prompt.ask(
                "\n🎨 Select a theme or 'back' to return",
                choices=choices,
                default="back"
            )
            
            if choice == "back":
                break
            else:
                theme_index = int(choice) - 1
                theme_name = themes[theme_index]
                self.layout_builder.update_theme(theme_name)
                self.console.print(f"[bold green]✅ Theme changed to {theme_name}![/bold green]")
                time.sleep(1)
    
    def _audio_menu(self) -> None:
        """Display and handle audio settings."""
        while True:
            self.console.clear()
            
            audio_table = Table(title="🔊 Audio Settings", box=box.ROUNDED)
            audio_table.add_column("Setting", style="cyan")
            audio_table.add_column("Current Value", style="green")
            audio_table.add_column("Description", style="white")
            
            config = self.config_manager.config
            audio_table.add_row(
                "Audio Enabled", 
                "Yes" if self.player.is_audio_enabled() else "No", 
                "Enable/disable audio playback"
            )
            audio_table.add_row(
                "Volume", 
                f"{int(config.audio.volume * 100)}%", 
                "Audio volume level"
            )
            audio_table.add_row(
                "Audio Files Found", 
                str(len(self.audio_files)), 
                "Number of audio files detected"
            )
            
            self.console.print(audio_table)
            
            if self.audio_files:
                audio_files_table = Table(title="📁 Available Audio Files", box=box.SIMPLE)
                audio_files_table.add_column("Song", style="magenta")
                audio_files_table.add_column("File Path", style="blue")
                
                for song, path in self.audio_files.items():
                    audio_files_table.add_row(song, path)
                
                self.console.print(audio_files_table)
            
            choice = Prompt.ask(
                "\n🔊 What would you like to change?",
                choices=["toggle", "volume", "back"],
                default="back"
            )
            
            if choice == "back":
                break
            elif choice == "toggle":
                self._toggle_audio()
            elif choice == "volume":
                self._change_volume()
    
    def _on_song_end(self) -> None:
        """Callback when song ends."""
        pass
    
    def _on_error(self, error: str) -> None:
        """Callback when error occurs."""
        self.console.print(f"[bold red]Error: {error}[/bold red]")
    
    def _change_refresh_rate(self) -> None:
        """Change display refresh rate."""
        try:
            rate = int(Prompt.ask("Enter new refresh rate (1-60 Hz)", default="10"))
            if 1 <= rate <= 60:
                self.config_manager.config.display.refresh_rate = rate
                self.config_manager.save_config()
                self.console.print(f"[bold green]✅ Refresh rate set to {rate} Hz![/bold green]")
            else:
                self.console.print("[bold red]❌ Rate must be between 1 and 60![/bold red]")
        except ValueError:
            self.console.print("[bold red]❌ Invalid number![/bold red]")
        time.sleep(1)
    
    def _toggle_progress_bar(self) -> None:
        """Toggle progress bar display."""
        config = self.config_manager.config
        config.display.show_progress_bar = not config.display.show_progress_bar
        self.config_manager.save_config()
        status = "enabled" if config.display.show_progress_bar else "disabled"
        self.console.print(f"[bold green]✅ Progress bar {status}![/bold green]")
        time.sleep(1)
    
    def _toggle_time_info(self) -> None:
        """Toggle time info display."""
        config = self.config_manager.config
        config.display.show_time_info = not config.display.show_time_info
        self.config_manager.save_config()
        status = "enabled" if config.display.show_time_info else "disabled"
        self.console.print(f"[bold green]✅ Time info {status}![/bold green]")
        time.sleep(1)
    
    def _change_max_sentences(self) -> None:
        """Change maximum visible sentences."""
        try:
            count = int(Prompt.ask("Enter max visible sentences (1-10)", default="3"))
            if 1 <= count <= 10:
                self.config_manager.config.display.max_visible_sentences = count
                self.config_manager.save_config()
                self.console.print(f"[bold green]✅ Max sentences set to {count}![/bold green]")
            else:
                self.console.print("[bold red]❌ Count must be between 1 and 10![/bold red]")
        except ValueError:
            self.console.print("[bold red]❌ Invalid number![/bold red]")
        time.sleep(1)
    
    def _toggle_audio(self) -> None:
        """Toggle audio on/off."""
        new_state = self.player.toggle_audio()
        status = "enabled" if new_state else "disabled"
        self.console.print(f"[bold green]✅ Audio {status}![/bold green]")
        time.sleep(1)
    
    def _change_volume(self) -> None:
        """Change audio volume."""
        try:
            volume = int(Prompt.ask("Enter volume (0-100%)", default="70"))
            if 0 <= volume <= 100:
                volume_float = volume / 100.0
                self.player.set_volume(volume_float)
                self.config_manager.save_config()
                self.console.print(f"[bold green]✅ Volume set to {volume}%![/bold green]")
            else:
                self.console.print("[bold red]❌ Volume must be between 0 and 100![/bold red]")
        except ValueError:
            self.console.print("[bold red]❌ Invalid number![/bold red]")
        time.sleep(1)
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        if hasattr(self.player, 'stop'):
            self.player.stop()
        if hasattr(self.config_manager, 'save_config'):
            self.config_manager.save_config()
    
    def _check_dependencies(self) -> bool:
        """Check if all required dependencies are available.
        
        Returns:
            True if all dependencies are available
        """
        try:
            import rich
            return True
        except ImportError:
            self.console.print("[bold red]❌ Rich library không được tìm thấy![/bold red]")
            self.console.print("[yellow]💡 Cài đặt bằng: pip install rich[/yellow]")
            return False
    
    def _ensure_lyrics_directory(self) -> None:
        """Ensure the lyrics directory exists."""
        lyrics_dir = Path("lyrics")
        if not lyrics_dir.exists():
            lyrics_dir.mkdir(exist_ok=True)
            self.console.print(f"[yellow]📁 Đã tạo thư mục {lyrics_dir}[/yellow]")


def main() -> None:
    """Main function to run the karaoke application."""
    app = KaraokeApp()
    
    # Check dependencies
    if not app._check_dependencies():
        sys.exit(1)
    
    # Ensure lyrics directory exists
    app._ensure_lyrics_directory()
    
    # Run the application
    app.run()


if __name__ == "__main__":
    main()