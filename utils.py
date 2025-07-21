"""Utility functions for the karaoke player.

This module contains helper functions for time formatting,
sentence navigation, and other common operations.
"""

from typing import Optional, Tuple
from lyrics_data import Song, Sentence


def format_time(ms: int) -> str:
    """Convert milliseconds to mm:ss format.
    
    Args:
        ms: Time in milliseconds
        
    Returns:
        Formatted time string in mm:ss format
    """
    seconds = int(ms // 1000)
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def get_current_sentence(song: Song, current_time: int) -> Tuple[Optional[str], Optional[Sentence]]:
    """Find the sentence currently being sung.
    
    Args:
        song: Song object containing all lyrics
        current_time: Current playback time in milliseconds
        
    Returns:
        Tuple of (sentence_key, sentence) or (None, None) if no match
    """
    for sentence_key, sentence in song.sentences.items():
        if sentence.start_time <= current_time <= sentence.end_time:
            return sentence_key, sentence
    return None, None


def get_next_sentence(song: Song, current_time: int) -> Tuple[Optional[str], Optional[Sentence]]:
    """Find the next sentence to be sung.
    
    Args:
        song: Song object containing all lyrics
        current_time: Current playback time in milliseconds
        
    Returns:
        Tuple of (sentence_key, sentence) or (None, None) if no next sentence
    """
    for sentence_key, sentence in song.sentences.items():
        if sentence.start_time > current_time:
            return sentence_key, sentence
    return None, None


def get_previous_sentence(song: Song, current_time: int) -> Tuple[Optional[str], Optional[Sentence]]:
    """Find the previous sentence that was sung.
    
    Args:
        song: Song object containing all lyrics
        current_time: Current playback time in milliseconds
        
    Returns:
        Tuple of (sentence_key, sentence) or (None, None) if no previous sentence
    """
    previous_sentence = None
    previous_key = None
    
    for sentence_key, sentence in song.sentences.items():
        if sentence.end_time < current_time:
            previous_sentence = sentence
            previous_key = sentence_key
        else:
            break
    
    return previous_key, previous_sentence


def calculate_progress_percentage(current_time: int, total_duration: int) -> float:
    """Calculate the progress percentage of the song.
    
    Args:
        current_time: Current playback time in milliseconds
        total_duration: Total song duration in milliseconds
        
    Returns:
        Progress percentage (0.0 to 100.0)
    """
    if total_duration <= 0:
        return 0.0
    
    percentage = (current_time / total_duration) * 100
    return min(100.0, max(0.0, percentage))


def is_word_active(word_time: int, current_time: int, highlight_duration: int = 800) -> bool:
    """Check if a word should be highlighted as currently active.
    
    Args:
        word_time: Time when the word should be sung (milliseconds)
        current_time: Current playback time (milliseconds)
        highlight_duration: How long to highlight the word (milliseconds)
        
    Returns:
        True if the word should be highlighted
    """
    return word_time <= current_time <= word_time + highlight_duration


def is_song_finished(song: Song, current_time: int, buffer_time: int = 3000) -> bool:
    """Check if the song has finished playing.
    
    Args:
        song: Song object
        current_time: Current playback time in milliseconds
        buffer_time: Additional time to wait after last word (milliseconds)
        
    Returns:
        True if the song has finished
    """
    return current_time > song.total_duration + buffer_time


def get_sentence_count(song: Song) -> int:
    """Get the total number of sentences in the song.
    
    Args:
        song: Song object
        
    Returns:
        Number of sentences
    """
    return len(song.sentences)


def get_word_count(song: Song) -> int:
    """Get the total number of words in the song.
    
    Args:
        song: Song object
        
    Returns:
        Total number of words
    """
    total_words = 0
    for sentence in song.sentences.values():
        total_words += len(sentence.words)
    return total_words