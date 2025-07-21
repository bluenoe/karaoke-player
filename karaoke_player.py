"""Core karaoke player module.

This module contains the main logic for playing karaoke with synchronized
lyrics display and timing management.
"""

import time
from typing import Optional
from rich.console import Console
from rich.live import Live

from lyrics_data import Song
from layout_builder import KaraokeLayoutBuilder
from utils import get_current_sentence, get_next_sentence, is_song_finished


class KaraokePlayer:
    """Main karaoke player class that handles playback and display."""
    
    def __init__(self, console: Console):
        """Initialize the karaoke player.
        
        Args:
            console: Rich console instance
        """
        self.console = console
        self.layout_builder = KaraokeLayoutBuilder(console)
        self.is_playing = False
        self.start_time = 0
    
    def play_song(self, song: Song, refresh_rate: int = 10) -> None:
        """Play a karaoke song with synchronized lyrics.
        
        Args:
            song: Song object to play
            refresh_rate: Screen refresh rate per second
        """
        self.console.print("[bold green]🎵 Bắt đầu phát karaoke với Rich...[/bold green]")
        self.console.print("[yellow]Nhấn Ctrl+C để dừng[/yellow]")
        time.sleep(2)
        
        self.start_time = time.time() * 1000  # Convert to milliseconds
        self.is_playing = True
        
        try:
            with Live(
                self._create_initial_layout(song), 
                refresh_per_second=refresh_rate, 
                screen=True
            ) as live:
                while self.is_playing:
                    current_time = self._get_current_time()
                    
                    # Update the display
                    layout = self._create_current_layout(song, current_time)
                    live.update(layout)
                    
                    # Check if song has finished
                    if is_song_finished(song, current_time):
                        self.console.print("[bold green]🎉 Bài hát đã kết thúc![/bold green]")
                        break
                    
                    # Small delay to control update frequency
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            self.console.print("[bold red]⏹️ Đã dừng karaoke[/bold red]")
        finally:
            self.is_playing = False
    
    def stop(self) -> None:
        """Stop the karaoke playback."""
        self.is_playing = False
    
    def pause(self) -> None:
        """Pause the karaoke playback (placeholder for future implementation)."""
        # TODO: Implement pause functionality
        pass
    
    def resume(self) -> None:
        """Resume the karaoke playback (placeholder for future implementation)."""
        # TODO: Implement resume functionality
        pass
    
    def seek(self, time_ms: int) -> None:
        """Seek to a specific time in the song (placeholder for future implementation).
        
        Args:
            time_ms: Time to seek to in milliseconds
        """
        # TODO: Implement seek functionality
        pass
    
    def _get_current_time(self) -> int:
        """Get the current playback time in milliseconds.
        
        Returns:
            Current time since playback started
        """
        return int((time.time() * 1000) - self.start_time)
    
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
        
        # Create and return the layout
        return self.layout_builder.create_karaoke_layout(
            song, current_time, current_sentence, next_sentence
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