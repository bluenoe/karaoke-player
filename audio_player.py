"""Audio player module for karaoke background music.

This module handles audio playback functionality including
MP3 support, volume control, and synchronization with lyrics.
"""

import os
import threading
import time
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


@dataclass
class AudioInfo:
    """Information about an audio file."""
    filename: str
    duration: float
    format: str
    size: int


class AudioPlayer:
    """Handles audio playback for karaoke songs."""
    
    def __init__(self, audio_directory: str = "audio"):
        """Initialize the audio player.
        
        Args:
            audio_directory: Directory containing audio files
        """
        self.audio_directory = Path(audio_directory)
        self.is_initialized = False
        self.is_playing = False
        self.is_paused = False
        self.current_file = None
        self.start_time = 0
        self.pause_time = 0
        self.volume = 0.7
        self.position_callback: Optional[Callable[[float], None]] = None
        self._position_thread = None
        self._stop_position_thread = False
        
        if PYGAME_AVAILABLE:
            self._initialize_pygame()
    
    def _initialize_pygame(self) -> bool:
        """Initialize pygame mixer.
        
        Returns:
            True if initialization successful
        """
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            self.is_initialized = True
            return True
        except pygame.error:
            self.is_initialized = False
            return False
    
    def is_audio_available(self) -> bool:
        """Check if audio functionality is available.
        
        Returns:
            True if audio can be played
        """
        return PYGAME_AVAILABLE and self.is_initialized
    
    def load_audio(self, filename: str) -> bool:
        """Load an audio file.
        
        Args:
            filename: Name of the audio file (with or without extension)
            
        Returns:
            True if file loaded successfully
        """
        if not self.is_audio_available():
            return False
        
        # Try different extensions if not provided
        if not filename.endswith(('.mp3', '.wav', '.ogg')):
            for ext in ['.mp3', '.wav', '.ogg']:
                test_path = self.audio_directory / (filename + ext)
                if test_path.exists():
                    filename = filename + ext
                    break
        
        file_path = self.audio_directory / filename
        
        if not file_path.exists():
            return False
        
        try:
            pygame.mixer.music.load(str(file_path))
            self.current_file = filename
            return True
        except pygame.error:
            return False
    
    def play(self, start_position: float = 0.0) -> bool:
        """Start playing the loaded audio.
        
        Args:
            start_position: Position to start playing from (in seconds)
            
        Returns:
            True if playback started successfully
        """
        if not self.is_audio_available() or not self.current_file:
            return False
        
        try:
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(start=start_position)
            self.is_playing = True
            self.is_paused = False
            self.start_time = time.time() - start_position
            self._start_position_tracking()
            return True
        except pygame.error:
            return False
    
    def pause(self) -> bool:
        """Pause audio playback.
        
        Returns:
            True if paused successfully
        """
        if not self.is_audio_available() or not self.is_playing:
            return False
        
        try:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.pause_time = time.time()
            self._stop_position_tracking()
            return True
        except pygame.error:
            return False
    
    def resume(self) -> bool:
        """Resume audio playback.
        
        Returns:
            True if resumed successfully
        """
        if not self.is_audio_available() or not self.is_paused:
            return False
        
        try:
            pygame.mixer.music.unpause()
            self.is_paused = False
            # Adjust start time to account for pause duration
            pause_duration = time.time() - self.pause_time
            self.start_time += pause_duration
            self._start_position_tracking()
            return True
        except pygame.error:
            return False
    
    def stop(self) -> bool:
        """Stop audio playback.
        
        Returns:
            True if stopped successfully
        """
        if not self.is_audio_available():
            return False
        
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self._stop_position_tracking()
            return True
        except pygame.error:
            return False
    
    def set_volume(self, volume: float) -> bool:
        """Set playback volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            True if volume set successfully
        """
        if not self.is_audio_available():
            return False
        
        self.volume = max(0.0, min(1.0, volume))
        
        try:
            pygame.mixer.music.set_volume(self.volume)
            return True
        except pygame.error:
            return False
    
    def get_volume(self) -> float:
        """Get current volume level.
        
        Returns:
            Current volume (0.0 to 1.0)
        """
        return self.volume
    
    def get_position(self) -> float:
        """Get current playback position in seconds.
        
        Returns:
            Current position in seconds
        """
        if not self.is_playing or self.is_paused:
            return 0.0
        
        return time.time() - self.start_time
    
    def seek(self, position: float) -> bool:
        """Seek to a specific position.
        
        Args:
            position: Position to seek to (in seconds)
            
        Returns:
            True if seek successful
        """
        if not self.is_audio_available() or not self.current_file:
            return False
        
        # Stop current playback
        was_playing = self.is_playing and not self.is_paused
        self.stop()
        
        # Restart from new position
        if was_playing:
            return self.play(position)
        
        return True
    
    def set_position_callback(self, callback: Optional[Callable[[float], None]]) -> None:
        """Set callback function for position updates.
        
        Args:
            callback: Function to call with current position (in seconds)
        """
        self.position_callback = callback
    
    def _start_position_tracking(self) -> None:
        """Start position tracking thread."""
        if self._position_thread and self._position_thread.is_alive():
            return
        
        self._stop_position_thread = False
        self._position_thread = threading.Thread(target=self._position_tracker, daemon=True)
        self._position_thread.start()
    
    def _stop_position_tracking(self) -> None:
        """Stop position tracking thread."""
        self._stop_position_thread = True
        if self._position_thread:
            self._position_thread.join(timeout=1.0)
    
    def _position_tracker(self) -> None:
        """Track playback position and call callback."""
        while not self._stop_position_thread and self.is_playing:
            if not self.is_paused and self.position_callback:
                position = self.get_position()
                self.position_callback(position)
            time.sleep(0.1)  # Update every 100ms
    
    def list_audio_files(self) -> list[str]:
        """List available audio files.
        
        Returns:
            List of audio filenames
        """
        if not self.audio_directory.exists():
            return []
        
        audio_files = []
        for ext in ['*.mp3', '*.wav', '*.ogg']:
            audio_files.extend([f.name for f in self.audio_directory.glob(ext)])
        
        return sorted(audio_files)
    
    def get_audio_info(self, filename: str) -> Optional[AudioInfo]:
        """Get information about an audio file.
        
        Args:
            filename: Name of the audio file
            
        Returns:
            Audio information or None if file not found
        """
        file_path = self.audio_directory / filename
        
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            return AudioInfo(
                filename=filename,
                duration=0.0,  # Would need additional library to get duration
                format=file_path.suffix.lower(),
                size=stat.st_size
            )
        except OSError:
            return None
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        self.stop()
        self._stop_position_tracking()
        
        if self.is_initialized:
            try:
                pygame.mixer.quit()
            except:
                pass
            self.is_initialized = False


class DummyAudioPlayer:
    """Dummy audio player for when pygame is not available."""
    
    def __init__(self, *args, **kwargs):
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7
        self.current_file = None
    
    def is_audio_available(self) -> bool:
        return False
    
    def load_audio(self, filename: str) -> bool:
        return False
    
    def play(self, start_position: float = 0.0) -> bool:
        return False
    
    def pause(self) -> bool:
        return False
    
    def resume(self) -> bool:
        return False
    
    def stop(self) -> bool:
        return False
    
    def set_volume(self, volume: float) -> bool:
        self.volume = volume
        return False
    
    def get_volume(self) -> float:
        return self.volume
    
    def get_position(self) -> float:
        return 0.0
    
    def seek(self, position: float) -> bool:
        return False
    
    def set_position_callback(self, callback) -> None:
        pass
    
    def list_audio_files(self) -> list[str]:
        return []
    
    def get_audio_info(self, filename: str) -> Optional[AudioInfo]:
        return None
    
    def cleanup(self) -> None:
        pass


def create_audio_player(audio_directory: str = "audio") -> AudioPlayer:
    """Create an audio player instance.
    
    Args:
        audio_directory: Directory containing audio files
        
    Returns:
        AudioPlayer instance (or DummyAudioPlayer if pygame unavailable)
    """
    if PYGAME_AVAILABLE:
        return AudioPlayer(audio_directory)
    else:
        return DummyAudioPlayer(audio_directory)