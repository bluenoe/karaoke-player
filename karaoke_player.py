"""Karaoke player module for handling song playback and display.

This module contains the main KaraokePlayer class that manages
song playback, timing, user interactions, and audio synchronization.
"""

import time
import threading
from typing import Optional, Tuple, Callable
from rich.console import Console
from rich.live import Live

from lyrics_data import Song, Sentence, LyricsLoader
from layout_builder import KaraokeLayoutBuilder
from utils import get_current_sentence, get_next_sentence, get_previous_sentence, is_song_finished
from config import ConfigManager
from audio_player import create_audio_player, AudioPlayer


class KaraokePlayer:
    """Handles karaoke song playback and display with audio support."""
    
    def __init__(self, console: Console, config_manager: Optional[ConfigManager] = None):
        """Initialize the karaoke player.
        
        Args:
            console: Rich console instance
            config_manager: Configuration manager for settings and themes
        """
        self.console = console
        self.config_manager = config_manager or ConfigManager()
        self.layout_builder = KaraokeLayoutBuilder(console, self.config_manager)
        
        # Playback state
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0
        self.pause_time = 0
        self.current_song: Optional[Song] = None
        
        # Audio support
        self.audio_player = create_audio_player(self.config_manager.config.audio.audio_directory)
        self.audio_enabled = self.config_manager.config.audio.enable_audio and self.audio_player.is_audio_available()
        
        # Callbacks
        self.on_song_end: Optional[Callable] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Threading
        self._stop_event = threading.Event()
        self._playback_thread: Optional[threading.Thread] = None
    
    def play_song(self, song: Song, refresh_rate: int = 10, audio_file: Optional[str] = None) -> None:
        """Play a karaoke song with synchronized lyrics display and optional audio.
        
        Args:
            song: Song object to play
            refresh_rate: Display refresh rate in Hz
            audio_file: Optional audio file to play alongside lyrics
        """
        self.current_song = song
        self.is_playing = True
        self.is_paused = False
        self.start_time = time.time()
        self._stop_event.clear()
        
        # Load and start audio if enabled
        if self.audio_enabled and audio_file:
            if self.audio_player.load_audio(audio_file):
                self.audio_player.set_volume(self.config_manager.config.audio.volume)
                self.audio_player.play()
            else:
                if self.on_error:
                    self.on_error(f"Failed to load audio file: {audio_file}")
        
        self.console.print("[bold green]🎵 Bắt đầu phát karaoke với Rich...[/bold green]")
        self.console.print("[yellow]Nhấn Ctrl+C để dừng[/yellow]")
        time.sleep(2)
        
        try:
            with Live(
                self._create_initial_layout(song), 
                refresh_per_second=refresh_rate, 
                screen=True
            ) as live:
                while self.is_playing and not self._stop_event.is_set():
                    current_time = self._get_current_time()
                    
                    # Update the display
                    layout = self._create_current_layout(song, current_time)
                    live.update(layout)
                    
                    # Check if song has finished
                    if is_song_finished(song, current_time):
                        self.console.print("[bold green]🎉 Bài hát đã kết thúc![/bold green]")
                        if self.on_song_end:
                            self.on_song_end()
                        break
                    
                    # Small delay to control update frequency
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            self.console.print("[bold red]⏹️ Đã dừng karaoke[/bold red]")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the karaoke playback and audio."""
        self.is_playing = False
        self.is_paused = False
        self._stop_event.set()
        
        if self.audio_enabled:
            self.audio_player.stop()
        
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)
    
    def pause(self) -> None:
        """Pause the karaoke playback and audio."""
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            self.pause_time = time.time()
            
            if self.audio_enabled:
                self.audio_player.pause()
    
    def resume(self) -> None:
        """Resume the karaoke playback and audio."""
        if self.is_paused:
            # Adjust start time to account for pause duration
            pause_duration = time.time() - self.pause_time
            self.start_time += pause_duration
            self.is_paused = False
            
            if self.audio_enabled:
                self.audio_player.resume()
    
    def seek(self, time_ms: int) -> None:
        """Seek to a specific time in the song.
        
        Args:
            time_ms: Time to seek to in milliseconds
        """
        if self.is_playing:
            self.start_time = time.time() - (time_ms / 1000)
            
            if self.audio_enabled:
                self.audio_player.seek(time_ms / 1000)
    
    def _get_current_time(self) -> int:
        """Get current playback time in milliseconds.
        
        Returns:
            Current time in milliseconds
        """
        if self.is_paused:
            return int((self.pause_time - self.start_time) * 1000)
        return int((time.time() - self.start_time) * 1000)
    
    def _get_current_time_ms(self) -> int:
        """Get current playback time in milliseconds (alias for consistency)."""
        return self._get_current_time()
    
    def set_volume(self, volume: float) -> None:
        """Set audio volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        if self.audio_enabled:
            self.audio_player.set_volume(volume)
        
        if self.config_manager:
            self.config_manager.config.audio.volume = volume
    
    def get_volume(self) -> float:
        """Get current audio volume.
        
        Returns:
            Current volume level (0.0 to 1.0)
        """
        if self.config_manager:
            return self.config_manager.config.audio.volume
        return 0.7
    
    def get_current_position(self) -> int:
        """Get current playback position in milliseconds.
        
        Returns:
            Current position in milliseconds
        """
        return self._get_current_time_ms()
    
    def get_song_duration(self) -> int:
        """Get total song duration in milliseconds.
        
        Returns:
            Song duration in milliseconds, or 0 if no song loaded
        """
        if not self.current_song or not self.current_song.sentences:
            return 0
        
        # Find the last word's end time
        last_sentence = list(self.current_song.sentences.values())[-1]
        if last_sentence.words:
            last_word = last_sentence.words[-1]
            return last_word.end_time
        return 0
    
    def is_audio_enabled(self) -> bool:
        """Check if audio is enabled.
        
        Returns:
            True if audio is enabled, False otherwise
        """
        return self.audio_enabled
    
    def toggle_audio(self) -> bool:
        """Toggle audio on/off.
        
        Returns:
            New audio state (True if enabled, False if disabled)
        """
        if self.audio_enabled:
            self.audio_player.stop()
            self.audio_enabled = False
        else:
            self.audio_enabled = True
        
        return self.audio_enabled
    
    def _create_current_layout(self, current_time_ms: int):
        """Create the current karaoke layout.
        
        Args:
            current_time_ms: Current time in milliseconds
            
        Returns:
            Rich layout for the current state
        """
        if not self.current_song:
            return self.layout_builder.create_error_panel("No song loaded")
        
        # Get current and next sentences
        current_key, current_sentence = get_current_sentence(self.current_song, current_time_ms)
        next_key, next_sentence = get_next_sentence(self.current_song, current_time_ms)
        previous_key, previous_sentence = get_previous_sentence(self.current_song, current_time_ms)
        
        # Get audio info if available
        audio_enabled = self.audio_enabled
        volume = self.config_manager.config.audio.volume if self.config_manager else 0.7
        
        # Additional info for footer
        additional_info = []
        if self.is_paused:
            additional_info.append("⏸️ PAUSED")
        if audio_enabled:
            additional_info.append(f"🔊 Audio: ON")
        else:
            additional_info.append(f"🔇 Audio: OFF")
        
        return self.layout_builder.create_karaoke_layout(
            song=self.current_song,
            current_time_ms=current_time_ms,
            current_sentence=current_sentence,
            next_sentence=next_sentence,
            previous_sentence=previous_sentence,
            audio_enabled=audio_enabled,
            volume=volume,
            additional_info=additional_info
        )
    
    def _create_initial_layout(self, song: Song):
        """Create the initial layout for the song.
        
        Args:
            song: Song object
            
        Returns:
            Initial Rich layout
        """
        return self._create_current_layout(song, 0)
    
    def _create_current_layout(self, song: Song, current_time: int):
        """Create the current layout based on playback time.
        
        Args:
            song: Song object
            current_time: Current playback time in milliseconds
            
        Returns:
            Rich layout for current state
        """
        # Get current and next sentences
        _, current_sentence = get_current_sentence(song, current_time)
        _, next_sentence = get_next_sentence(song, current_time)
        _, previous_sentence = get_previous_sentence(song, current_time)
        
        # Get audio info if available
        audio_enabled = self.audio_enabled
        volume = self.config_manager.config.audio.volume if self.config_manager else 0.7
        
        # Additional info for footer
        additional_info = []
        if self.is_paused:
            additional_info.append("⏸️ PAUSED")
        if audio_enabled:
            additional_info.append(f"🔊 Audio: ON")
        else:
            additional_info.append(f"🔇 Audio: OFF")
        
        # Create and return the layout
        return self.layout_builder.create_karaoke_layout(
            song=song,
            current_time_ms=current_time,
            current_sentence=current_sentence,
            next_sentence=next_sentence,
            previous_sentence=previous_sentence,
            audio_enabled=audio_enabled,
            volume=volume,
            additional_info=additional_info
        )
    
    def get_playback_info(self, song: Song) -> dict:
        """Get current playback information.
        
        Args:
            song: Song object
            
        Returns:
            Dictionary with playback information
        """
        if not self.is_playing:
            return {
                'is_playing': False,
                'current_time': 0,
                'progress_percentage': 0.0
            }
        
        current_time = self._get_current_time()
        progress = (current_time / song.total_duration) * 100 if song.total_duration > 0 else 0
        
        return {
            'is_playing': self.is_playing,
            'current_time': current_time,
            'progress_percentage': min(100.0, max(0.0, progress)),
            'current_sentence': get_current_sentence(song, current_time)[0],
            'next_sentence': get_next_sentence(song, current_time)[0]
        }


class KaraokeSession:
    """Manages a complete karaoke session with multiple songs."""
    
    def __init__(self, console: Console):
        """Initialize the karaoke session.
        
        Args:
            console: Rich console instance
        """
        self.console = console
        self.player = KaraokePlayer(console)
        self.layout_builder = KaraokeLayoutBuilder(console)
        self.current_song: Optional[Song] = None
    
    def start_session(self, song: Song) -> None:
        """Start a karaoke session with a song.
        
        Args:
            song: Song to play
        """
        self.current_song = song
        
        # Clear screen and show welcome
        self.console.clear()
        
        # Display welcome panel
        welcome_panel = self.layout_builder.create_welcome_panel(song)
        self.console.print(welcome_panel)
        
        # Display song information
        info_table = self.layout_builder.create_song_info_table(song)
        self.console.print(info_table)
        self.console.print()
        
        # Wait for user to start
        input("Nhấn Enter để bắt đầu karaoke...")
        
        # Start playing
        self.player.play_song(song)
    
    def end_session(self) -> None:
        """End the current karaoke session."""
        if self.player.is_playing:
            self.player.stop()
        
        self.console.print("[bold cyan]🎵 Cảm ơn bạn đã sử dụng Karaoke Player! 🎵[/bold cyan]")
        self.current_song = None
    
    def get_session_info(self) -> dict:
        """Get information about the current session.
        
        Returns:
            Dictionary with session information
        """
        if not self.current_song:
            return {'has_active_song': False}
        
        playback_info = self.player.get_playback_info(self.current_song)
        
        return {
            'has_active_song': True,
            'song_title': self.current_song.title,
            'song_artist': self.current_song.artist,
            'total_duration': self.current_song.total_duration,
            **playback_info
        }