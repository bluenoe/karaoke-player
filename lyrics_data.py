"""Lyrics data loader module for karaoke player.

This module handles loading and parsing lyrics from JSON files,
and provides data models for structured lyrics representation.
"""

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class Word:
    """Represents a single word with timing information."""
    time: int  # Time in milliseconds
    text: str  # The word text


@dataclass
class Sentence:
    """Represents a sentence containing multiple words."""
    words: List[Word]
    
    @property
    def start_time(self) -> int:
        """Get the start time of the sentence."""
        return self.words[0].time if self.words else 0
    
    @property
    def end_time(self) -> int:
        """Get the end time of the sentence with buffer."""
        return self.words[-1].time + 1000 if self.words else 0


@dataclass
class Song:
    """Represents a complete song with metadata and lyrics."""
    title: str
    artist: str
    sentences: Dict[str, Sentence]
    
    @property
    def total_duration(self) -> int:
        """Get the total duration of the song in milliseconds."""
        if not self.sentences:
            return 0
        last_sentence = list(self.sentences.values())[-1]
        return last_sentence.end_time


class LyricsLoader:
    """Handles loading lyrics from JSON files."""
    
    def __init__(self, lyrics_dir: str = "lyrics"):
        """Initialize the lyrics loader.
        
        Args:
            lyrics_dir: Directory containing lyrics JSON files
        """
        self.lyrics_dir = Path(lyrics_dir)
    
    def load_song(self, filename: str) -> Song:
        """Load a song from a JSON file.
        
        Args:
            filename: Name of the JSON file (with or without .json extension)
            
        Returns:
            Song object with loaded lyrics
            
        Raises:
            FileNotFoundError: If the lyrics file doesn't exist
            json.JSONDecodeError: If the JSON file is malformed
        """
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = self.lyrics_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Lyrics file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self._parse_song_data(data)
    
    def _parse_song_data(self, data: dict) -> Song:
        """Parse JSON data into Song object.
        
        Args:
            data: Dictionary containing song data
            
        Returns:
            Song object
        """
        sentences = {}
        
        for sentence_key, words_data in data['sentences'].items():
            words = [Word(time=word['time'], text=word['text']) for word in words_data]
            sentences[sentence_key] = Sentence(words=words)
        
        return Song(
            title=data['title'],
            artist=data['artist'],
            sentences=sentences
        )
    
    def list_available_songs(self) -> List[str]:
        """List all available song files in the lyrics directory.
        
        Returns:
            List of song filenames (without .json extension)
        """
        if not self.lyrics_dir.exists():
            return []
        
        songs = []
        for file_path in self.lyrics_dir.glob('*.json'):
            songs.append(file_path.stem)
        
        return sorted(songs)
    
    def get_song_info(self, filename: str) -> Optional[Dict[str, str]]:
        """Get basic information about a song without loading full lyrics.
        
        Args:
            filename: Name of the JSON file
            
        Returns:
            Dictionary with title and artist, or None if file doesn't exist
        """
        try:
            if not filename.endswith('.json'):
                filename += '.json'
            
            file_path = self.lyrics_dir / filename
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'title': data.get('title', 'Unknown'),
                'artist': data.get('artist', 'Unknown')
            }
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None