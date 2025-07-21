"""Layout builder module for Rich UI components.

This module is responsible for creating and managing all Rich UI components
including layouts, panels, progress bars, and text styling.
"""

from typing import Optional
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.align import Align

from lyrics_data import Song, Sentence
from utils import format_time, is_word_active, calculate_progress_percentage


class KaraokeLayoutBuilder:
    """Builds Rich UI layouts for the karaoke player."""
    
    def __init__(self, console: Console):
        """Initialize the layout builder.
        
        Args:
            console: Rich console instance
        """
        self.console = console
    
    def create_lyrics_text(self, sentence: Sentence, current_time: int, is_current: bool = True) -> Text:
        """Create Rich text for song lyrics with timing-based styling.
        
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
        for word in sentence.words:
            if is_current and is_word_active(word.time, current_time):
                # Currently singing word - highlight in yellow
                text.append(word.text + " ", style="bold yellow on dark_blue")
            elif word.time <= current_time:
                # Already sung word - dim white
                text.append(word.text + " ", style="dim white")
            else:
                # Not yet sung word - normal white
                text.append(word.text + " ", style="white")
        
        return text
    
    def create_progress_bar(self, current_time: int, total_duration: int) -> Progress:
        """Create a progress bar for song playback.
        
        Args:
            current_time: Current playback time in milliseconds
            total_duration: Total song duration in milliseconds
            
        Returns:
            Rich Progress object
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="bright_green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn(f"[yellow]{format_time(current_time)}[/yellow]"),
            console=self.console
        )
        
        task = progress.add_task("🎵 Đang phát...", total=total_duration)
        progress.update(task, completed=current_time)
        
        return progress
    
    def create_header_panel(self, song: Song, current_time: int) -> Panel:
        """Create the header panel with song information.
        
        Args:
            song: Song object
            current_time: Current playback time in milliseconds
            
        Returns:
            Rich Panel object for header
        """
        title_text = Text("🎵 KARAOKE PLAYER", style="bold cyan", justify="center")
        subtitle_text = Text(f"{song.title} - {song.artist}", style="italic cyan", justify="center")
        time_text = Text(
            f"⏰ {format_time(current_time)} / {format_time(song.total_duration)}", 
            style="yellow", 
            justify="center"
        )
        
        header_content = Layout()
        header_content.split_column(
            Layout(title_text),
            Layout(subtitle_text),
            Layout(time_text)
        )
        
        return Panel(header_content, style="cyan", border_style="bright_cyan")
    
    def create_lyrics_panel(self, sentence: Optional[Sentence], current_time: int, 
                           title: str, emoji: str, style: str, is_current: bool = True) -> Panel:
        """Create a panel for displaying lyrics.
        
        Args:
            sentence: Sentence to display (can be None)
            current_time: Current playback time in milliseconds
            title: Panel title
            emoji: Emoji for the title
            style: Panel style
            is_current: Whether this is the current sentence
            
        Returns:
            Rich Panel object
        """
        if sentence:
            lyrics_text = self.create_lyrics_text(sentence, current_time, is_current)
            content = Layout()
            content.split_column(
                Layout(Text(f"{emoji} {title.upper()}", style=f"bold {style}", justify="center")),
                Layout(Align(lyrics_text, align="center"))
            )
        else:
            content = Text("")
        
        return Panel(
            content, 
            title=f"{emoji} {title}", 
            style=style, 
            border_style=f"bright_{style}"
        )
    
    def create_footer_panel(self) -> Panel:
        """Create the footer panel with controls information.
        
        Returns:
            Rich Panel object for footer
        """
        controls_text = Text(
            "🎮 Điều khiển: Ctrl+C để dừng | 🎵 Đang phát...", 
            style="yellow", 
            justify="center"
        )
        return Panel(controls_text, style="yellow", border_style="bright_yellow")
    
    def create_karaoke_layout(self, song: Song, current_time: int, 
                             current_sentence: Optional[Sentence], 
                             next_sentence: Optional[Sentence]) -> Layout:
        """Create the complete karaoke layout.
        
        Args:
            song: Song object
            current_time: Current playback time in milliseconds
            current_sentence: Currently active sentence
            next_sentence: Next sentence to be sung
            
        Returns:
            Rich Layout object
        """
        layout = Layout()
        
        # Split layout into sections
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="progress", size=3),
            Layout(name="main", size=10),
            Layout(name="footer", size=3)
        )
        
        # Header
        layout["header"].update(self.create_header_panel(song, current_time))
        
        # Progress bar
        progress = self.create_progress_bar(current_time, song.total_duration)
        progress_panel = Panel(progress, style="green", border_style="bright_green")
        layout["progress"].update(progress_panel)
        
        # Main content with lyrics
        main_content = Layout()
        main_content.split_column(
            Layout(name="current", size=5),
            Layout(name="next", size=5)
        )
        
        # Current sentence panel
        current_panel = self.create_lyrics_panel(
            current_sentence, current_time, "Câu hiện tại", "🎤", "green", True
        )
        main_content["current"].update(current_panel)
        
        # Next sentence panel
        next_panel = self.create_lyrics_panel(
            next_sentence, current_time, "Câu tiếp theo", "⏭️", "blue", False
        )
        main_content["next"].update(next_panel)
        
        layout["main"].update(main_content)
        
        # Footer
        layout["footer"].update(self.create_footer_panel())
        
        return layout
    
    def create_song_info_table(self, song: Song) -> Table:
        """Create a table with song information.
        
        Args:
            song: Song object
            
        Returns:
            Rich Table object
        """
        from utils import get_sentence_count, get_word_count
        
        info_table = Table(
            title="📊 Thông tin bài hát", 
            show_header=True, 
            header_style="bold magenta"
        )
        info_table.add_column("Mục", style="cyan", justify="center")
        info_table.add_column("Chi tiết", style="green", justify="center")
        
        info_table.add_row("🎵 Tên bài hát", song.title)
        info_table.add_row("🎤 Nghệ sĩ", song.artist)
        info_table.add_row("📝 Số câu", str(get_sentence_count(song)))
        info_table.add_row("📖 Số từ", str(get_word_count(song)))
        info_table.add_row("⏱️ Thời lượng", format_time(song.total_duration))
        
        return info_table
    
    def create_welcome_panel(self, song: Song) -> Panel:
        """Create a welcome panel for the karaoke player.
        
        Args:
            song: Song object
            
        Returns:
            Rich Panel object
        """
        title = f"🎵 KARAOKE PLAYER - {song.title} 🎵"
        return Panel(
            f"[bold cyan]{title}[/bold cyan]",
            style="cyan",
            border_style="bright_cyan"
        )