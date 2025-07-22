"""Layout builder module for karaoke player UI.

This module handles all Rich UI components and rendering logic,
including styled text, progress bars, and panel layouts with theme support.
"""

from typing import List, Optional, Tuple, Dict, Any
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.align import Align
from rich.console import Group
from rich.rule import Rule
from rich.columns import Columns
from rich.box import ROUNDED, DOUBLE, HEAVY, MINIMAL
from rich.style import Style
from rich.padding import Padding
from rich.emoji import Emoji

from lyrics_data import Song, Sentence, Word
from utils import format_time, is_word_active, calculate_progress_percentage
from config import ConfigManager, ThemeConfig


class KaraokeLayoutBuilder:
    """Builds Rich UI layouts for the karaoke player with theme support."""
    
    def __init__(self, console: Console, config_manager: Optional[ConfigManager] = None):
        """Initialize the layout builder.
        
        Args:
            console: Rich console instance
            config_manager: Configuration manager for themes and settings
        """
        self.console = console
        self.config_manager = config_manager or ConfigManager()
        self.theme = self.config_manager.get_theme()
        self.display_config = self.config_manager.config.display
        
        # Animation states
        self._animation_frame = 0
        self._pulse_direction = 1
    
    def _get_animated_style(self, base_color: str) -> str:
        """Get animated style for active text.
        
        Args:
            base_color: Base color for animation
            
        Returns:
            Animated style string
        """
        if not self.display_config.enable_animations:
            return base_color
        
        # Simple pulse animation
        self._animation_frame += self._pulse_direction
        if self._animation_frame >= 10:
            self._pulse_direction = -1
        elif self._animation_frame <= 0:
            self._pulse_direction = 1
        
        # Create pulsing effect
        if self._animation_frame > 5:
            return f"bright_{base_color}"
        else:
            return base_color
    
    def create_lyrics_text(self, sentence: Sentence, current_time: int, is_current: bool = True) -> Text:
        """Create styled text for a sentence with word-by-word highlighting.
        
        Args:
            sentence: Sentence object containing words
            current_time: Current playback time in milliseconds
            is_current: Whether this is the currently active sentence
            
        Returns:
            Rich Text object with styled lyrics
        """
        if not sentence or not sentence.words:
            return Text("")
        
        text = Text()
        
        for i, word in enumerate(sentence.words):
            # Add space before word (except first word)
            if i > 0:
                text.append(" ")
            
            # Determine word styling based on timing and theme
            if is_word_active(word.time, current_time, self.display_config.highlight_duration):
                # Currently active word with animation
                style = self._get_animated_style(self.theme.text_active)
                text.append(word.text, style=f"bold {style}")
            elif word.time <= current_time:
                # Already sung word
                text.append(word.text, style=self.theme.text_highlight)
            else:
                # Future word
                if is_current:
                    text.append(word.text, style=self.theme.text_primary)
                else:
                    text.append(word.text, style=self.theme.text_secondary)
        
        return text
    
    def create_progress_bar(self, current_time: int, total_duration: int) -> Panel:
        """Create a themed progress bar showing song progress.
        
        Args:
            current_time: Current playback time in milliseconds
            total_duration: Total song duration in milliseconds
            
        Returns:
            Rich Panel containing the progress bar
        """
        if not self.display_config.show_progress_bar:
            return Panel("", height=0)
            
        if total_duration <= 0:
            percentage = 0.0
        else:
            percentage = calculate_progress_percentage(current_time, total_duration)
        
        # Create themed progress bar
        progress = Progress(
            SpinnerColumn("dots", style=self.theme.accent),
            TextColumn(f"[{self.theme.primary}]Progress"),
            BarColumn(
                bar_width=40,
                complete_style=self.theme.progress_complete,
                finished_style=self.theme.progress_complete,
                pulse_style=self.theme.accent
            ),
            TextColumn(f"[{self.theme.primary}]{{task.percentage:>3.0f}}%"),
        )
        
        if self.display_config.show_time_info:
            progress.columns.append(
                TextColumn(f"[{self.theme.text_secondary}]{format_time(current_time)} / {format_time(total_duration)}")
            )
        
        task = progress.add_task("progress", total=100, completed=percentage)
        
        return Panel(
            progress,
            title=f"[{self.theme.accent}]⏱️ Progress",
            border_style=self.theme.border,
            box=ROUNDED,
            padding=(0, 1)
        )
    
    def create_header_panel(self, song: Song, audio_enabled: bool = False, volume: float = 0.7) -> Panel:
        """Create themed header panel with song information.
        
        Args:
            song: Song object containing metadata
            audio_enabled: Whether audio is currently enabled
            volume: Current volume level (0.0 to 1.0)
            
        Returns:
            Rich Panel with song information
        """
        # Main title
        header_text = Text()
        header_text.append("🎤 ", style=self.theme.accent)
        header_text.append(song.title, style=f"bold {self.theme.text_primary}")
        header_text.append(" by ", style=self.theme.text_secondary)
        header_text.append(song.artist, style=self.theme.secondary)
        
        # Audio status
        if audio_enabled:
            volume_bars = "█" * int(volume * 10)
            volume_empty = "░" * (10 - int(volume * 10))
            audio_status = Text()
            audio_status.append("🔊 ", style=self.theme.accent)
            audio_status.append(volume_bars, style=self.theme.progress_complete)
            audio_status.append(volume_empty, style=self.theme.text_secondary)
            audio_status.append(f" {int(volume * 100)}%", style=self.theme.text_secondary)
        else:
            audio_status = Text("🔇 Audio Disabled", style=self.theme.text_secondary)
        
        content = Group(
            Align.center(header_text),
            Align.center(audio_status)
        )
        
        return Panel(
            content,
            title=f"[{self.theme.accent}]🎵 Now Playing",
            border_style=self.theme.border,
            box=ROUNDED,
            padding=(1, 2)
        )
    
    def create_lyrics_panel(self, current_sentence: Optional[Sentence], 
                           next_sentence: Optional[Sentence], 
                           previous_sentence: Optional[Sentence],
                           current_time: int) -> Panel:
        """Create themed panel displaying lyrics with context.
        
        Args:
            current_sentence: Currently active sentence
            next_sentence: Next sentence to be sung
            previous_sentence: Previous sentence that was sung
            current_time: Current playback time in milliseconds
            
        Returns:
            Rich Panel with lyrics
        """
        content = []
        
        # Previous sentence (if enabled and available)
        if (self.display_config.show_previous_sentence and 
            previous_sentence and 
            len(content) < self.display_config.max_visible_sentences):
            prev_text = self.create_lyrics_text(previous_sentence, current_time, is_current=False)
            content.append(Panel(
                Align.center(prev_text),
                title=f"[{self.theme.text_secondary}]Previous",
                border_style=self.theme.text_secondary,
                box=MINIMAL,
                padding=(0, 1)
            ))
        
        # Current sentence
        if current_sentence:
            current_text = self.create_lyrics_text(current_sentence, current_time, is_current=True)
            content.append(Panel(
                Align.center(current_text),
                title=f"[{self.theme.accent}]♪ Current",
                border_style=self.theme.accent,
                box=ROUNDED,
                padding=(1, 2)
            ))
        
        # Next sentence (if enabled and available)
        if (self.display_config.show_next_sentence and 
            next_sentence and 
            len(content) < self.display_config.max_visible_sentences):
            next_text = self.create_lyrics_text(next_sentence, current_time, is_current=False)
            content.append(Panel(
                Align.center(next_text),
                title=f"[{self.theme.primary}]Next",
                border_style=self.theme.primary,
                box=MINIMAL,
                padding=(0, 1)
            ))
        
        if not content:
            content.append(Text("🎵 No lyrics available", style=f"dim {self.theme.text_secondary}"))
        
        return Panel(
            Group(*content),
            title=f"[{self.theme.accent}]📝 Lyrics",
            border_style=self.theme.border,
            box=ROUNDED,
            padding=(0, 1)
        )
    
    def create_footer_panel(self, additional_info: Optional[str] = None) -> Panel:
        """Create themed footer panel with controls and additional information.
        
        Args:
            additional_info: Optional additional information to display
            
        Returns:
            Rich Panel with control instructions
        """
        # Controls
        controls = [
            ("[SPACE]", "Pause/Resume", self.theme.accent),
            ("[Q]", "Quit", "bright_red"),
            ("[R]", "Restart", self.theme.primary),
            ("[T]", "Theme", self.theme.secondary),
            ("[+/-]", "Volume", self.theme.text_secondary)
        ]
        
        controls_text = Text()
        controls_text.append("Controls: ", style=f"bold {self.theme.text_primary}")
        
        for i, (key, action, color) in enumerate(controls):
            if i > 0:
                controls_text.append("  ", style="white")
            controls_text.append(key, style=f"bold {color}")
            controls_text.append(f" {action}", style=self.theme.text_secondary)
        
        content = [controls_text]
        
        # Additional info
        if additional_info:
            info_text = Text(additional_info, style=self.theme.text_secondary)
            content.append(info_text)
        
        return Panel(
            Align.center(Group(*content)),
            title=f"[{self.theme.accent}]🎮 Controls",
            border_style=self.theme.border,
            box=ROUNDED,
            padding=(0, 1)
        )
    
    def create_karaoke_layout(self, song: Song, current_sentence: Optional[Sentence],
                             next_sentence: Optional[Sentence], 
                             previous_sentence: Optional[Sentence],
                             current_time: int, total_duration: int,
                             audio_enabled: bool = False, volume: float = 0.7,
                             additional_info: Optional[str] = None) -> Layout:
        """Create the complete themed karaoke layout.
        
        Args:
            song: Song object with metadata
            current_sentence: Currently active sentence
            next_sentence: Next sentence to be sung
            previous_sentence: Previous sentence that was sung
            current_time: Current playback time in milliseconds
            total_duration: Total song duration in milliseconds
            audio_enabled: Whether audio is currently enabled
            volume: Current volume level
            additional_info: Additional information to display
            
        Returns:
            Rich Layout object
        """
        layout = Layout()
        
        # Dynamic layout based on configuration
        sections = [("header", 6)]
        
        if self.display_config.show_progress_bar:
            sections.append(("progress", 5))
        
        sections.extend([
            ("main", 1),  # ratio=1 means it takes remaining space
            ("footer", 4)
        ])
        
        # Create layout sections
        layout_args = []
        for name, size in sections:
            if size == 1:
                layout_args.append(Layout(name=name, ratio=size))
            else:
                layout_args.append(Layout(name=name, size=size))
        
        layout.split_column(*layout_args)
        
        # Populate sections
        layout["header"].update(self.create_header_panel(song, audio_enabled, volume))
        layout["main"].update(self.create_lyrics_panel(
            current_sentence, next_sentence, previous_sentence, current_time
        ))
        
        if self.display_config.show_progress_bar:
            layout["progress"].update(self.create_progress_bar(current_time, total_duration))
        
        layout["footer"].update(self.create_footer_panel(additional_info))
        
        return layout
    
    def create_song_list_table(self, songs_info: List[Dict[str, str]]) -> Table:
        """Create a themed table displaying song information.
        
        Args:
            songs_info: List of dictionaries containing song information
            
        Returns:
            Rich Table with song information
        """
        table = Table(
            title=f"[{self.theme.accent}]🎵 Available Songs",
            box=ROUNDED,
            border_style=self.theme.border,
            header_style=f"bold {self.theme.primary}"
        )
        
        table.add_column("#", style=self.theme.text_secondary, width=4)
        table.add_column("Title", style=f"bold {self.theme.text_primary}")
        table.add_column("Artist", style=self.theme.secondary)
        table.add_column("File", style=self.theme.text_secondary)
        
        for i, song_info in enumerate(songs_info, 1):
            table.add_row(
                str(i),
                song_info.get('title', 'Unknown'),
                song_info.get('artist', 'Unknown'),
                song_info.get('filename', 'Unknown')
            )
        
        return table
    
    def create_welcome_panel(self, app_name: str = "Karaoke Rich") -> Panel:
        """Create a themed welcome panel.
        
        Args:
            app_name: Name of the application
            
        Returns:
            Rich Panel with welcome message
        """
        welcome_text = Text()
        welcome_text.append("🎤 Welcome to ", style=self.theme.text_primary)
        welcome_text.append(app_name, style=f"bold {self.theme.accent}")
        welcome_text.append("! 🎵", style=self.theme.text_primary)
        
        subtitle = Text(
            "Terminal-based Karaoke Player with Rich UI",
            style=self.theme.text_secondary
        )
        
        instructions = Text()
        instructions.append("Select a song by entering its number, or ", style=self.theme.text_secondary)
        instructions.append("'q'", style=f"bold {self.theme.accent}")
        instructions.append(" to quit.", style=self.theme.text_secondary)
        
        content = Group(
            Align.center(welcome_text),
            Align.center(subtitle),
            Text(""),  # Empty line
            Align.center(instructions)
        )
        
        return Panel(
            content,
            title=f"[{self.theme.accent}]🎵 Karaoke Rich",
            border_style=self.theme.border,
            box=DOUBLE,
            padding=(1, 2)
        )
    
    def create_theme_selection_panel(self, available_themes: Dict[str, str], current_theme: str) -> Panel:
        """Create a panel for theme selection.
        
        Args:
            available_themes: Dictionary of theme keys to display names
            current_theme: Currently selected theme key
            
        Returns:
            Rich Panel for theme selection
        """
        content = []
        content.append(Text("Available Themes:", style=f"bold {self.theme.text_primary}"))
        content.append(Text(""))  # Empty line
        
        for i, (key, name) in enumerate(available_themes.items(), 1):
            theme_text = Text()
            if key == current_theme:
                theme_text.append(f"► {i}. {name} (current)", style=f"bold {self.theme.accent}")
            else:
                theme_text.append(f"  {i}. {name}", style=self.theme.text_primary)
            content.append(theme_text)
        
        content.append(Text(""))  # Empty line
        content.append(Text("Enter theme number to switch, or press any other key to continue.", 
                           style=self.theme.text_secondary))
        
        return Panel(
            Group(*content),
            title=f"[{self.theme.accent}]🎨 Theme Selection",
            border_style=self.theme.border,
            box=ROUNDED,
            padding=(1, 2)
        )
    
    def create_error_panel(self, error_message: str, error_type: str = "Error") -> Panel:
        """Create a themed error panel.
        
        Args:
            error_message: Error message to display
            error_type: Type of error (for title)
            
        Returns:
            Rich Panel with error information
        """
        error_text = Text()
        error_text.append("❌ ", style="bright_red")
        error_text.append(error_message, style="bright_red")
        
        return Panel(
            Align.center(error_text),
            title=f"[bright_red]⚠️ {error_type}",
            border_style="bright_red",
            box=HEAVY,
            padding=(1, 2)
        )
    
    def create_loading_panel(self, message: str = "Loading...") -> Panel:
        """Create a themed loading panel.
        
        Args:
            message: Loading message to display
            
        Returns:
            Rich Panel with loading information
        """
        loading_text = Text()
        loading_text.append("⏳ ", style=self.theme.accent)
        loading_text.append(message, style=self.theme.text_primary)
        
        return Panel(
            Align.center(loading_text),
            title=f"[{self.theme.accent}]⏳ Loading",
            border_style=self.theme.border,
            box=ROUNDED,
            padding=(1, 2)
        )
    
    def update_theme(self, theme_name: str) -> bool:
        """Update the current theme.
        
        Args:
            theme_name: Name of the theme to switch to
            
        Returns:
            True if theme was updated successfully
        """
        if self.config_manager.set_theme(theme_name):
            self.theme = self.config_manager.get_theme()
            return True
        return False
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get available themes.
        
        Returns:
            Dictionary mapping theme keys to display names
        """
        return self.config_manager.get_available_themes()
    
    def get_current_theme_name(self) -> str:
        """Get current theme name.
        
        Returns:
            Current theme key
        """
        return self.config_manager.config.theme
    
    def create_song_info_table(self, song: Song) -> Table:
        """Create a table with song information.
        
        Args:
            song: Song object
            
        Returns:
            Rich Table object
        """
        from utils import get_sentence_count, get_word_count
        
        info_table = Table(
            title=f"[{self.theme.accent}]📊 Song Information", 
            show_header=True, 
            header_style=f"bold {self.theme.primary}",
            box=ROUNDED,
            border_style=self.theme.border
        )
        info_table.add_column("Property", style=self.theme.text_primary, justify="center")
        info_table.add_column("Details", style=self.theme.secondary, justify="center")
        
        info_table.add_row("🎵 Title", song.title)
        info_table.add_row("🎤 Artist", song.artist)
        info_table.add_row("📝 Sentences", str(get_sentence_count(song)))
        info_table.add_row("📖 Words", str(get_word_count(song)))
        info_table.add_row("⏱️ Duration", format_time(song.total_duration))
        
        return info_table