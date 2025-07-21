"""Main entry point for the Karaoke Rich application.

This module handles application startup, song selection,
and coordinates the overall user experience.
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text

from lyrics_data import LyricsLoader, Song
from karaoke_player import KaraokeSession


class KaraokeApp:
    """Main application class for the Karaoke Rich player."""
    
    def __init__(self):
        """Initialize the karaoke application."""
        self.console = Console()
        self.lyrics_loader = LyricsLoader()
        self.session = KaraokeSession(self.console)
    
    def run(self) -> None:
        """Run the main application loop."""
        try:
            self._show_welcome()
            
            while True:
                song = self._select_song()
                if song is None:
                    break
                
                self.session.start_session(song)
                
                # Ask if user wants to play another song
                if not Confirm.ask("\n🎵 Bạn có muốn hát thêm bài khác không?"):
                    break
            
            self.session.end_session()
            
        except KeyboardInterrupt:
            self.console.print("\n[bold red]👋 Tạm biệt![/bold red]")
        except Exception as e:
            self.console.print(f"[bold red]❌ Lỗi: {e}[/bold red]")
            sys.exit(1)
    
    def _show_welcome(self) -> None:
        """Display the welcome screen."""
        self.console.clear()
        
        # Main title
        title_panel = Panel(
            "[bold cyan]🎵 CHÀO MỪNG ĐẾN VỚI KARAOKE RICH 🎵[/bold cyan]\n"
            "[yellow]Ứng dụng karaoke terminal với Rich library[/yellow]",
            style="cyan",
            border_style="bright_cyan"
        )
        self.console.print(title_panel)
        
        # Features table
        features_table = Table(
            title="✨ Tính năng", 
            show_header=False, 
            box=None,
            show_edge=False
        )
        features_table.add_column("Feature", style="green")
        
        features = [
            "🎤 Hiển thị lời bài hát theo thời gian thực",
            "🌈 Giao diện màu sắc đẹp mắt với Rich",
            "⏱️ Đồng bộ từng từ với timing chính xác",
            "📊 Thanh tiến trình và thông tin bài hát",
            "🎵 Hỗ trợ nhiều bài hát từ file JSON",
            "⌨️ Điều khiển đơn giản với bàn phím"
        ]
        
        for feature in features:
            features_table.add_row(feature)
        
        self.console.print(features_table)
        self.console.print()
    
    def _select_song(self) -> Song | None:
        """Allow user to select a song to play.
        
        Returns:
            Selected Song object or None if user wants to quit
        """
        available_songs = self._get_available_songs()
        
        if not available_songs:
            self.console.print("[bold red]❌ Không tìm thấy bài hát nào trong thư mục lyrics/[/bold red]")
            self.console.print("[yellow]💡 Hãy thêm file JSON vào thư mục lyrics/ để bắt đầu![/yellow]")
            return None
        
        # Display available songs
        self._display_song_list(available_songs)
        
        # Get user selection
        while True:
            try:
                choice = Prompt.ask(
                    "\n🎵 Chọn bài hát (nhập số) hoặc 'q' để thoát",
                    choices=[str(i) for i in range(1, len(available_songs) + 1)] + ['q', 'Q']
                )
                
                if choice.lower() == 'q':
                    return None
                
                song_index = int(choice) - 1
                song_filename = available_songs[song_index]['filename']
                
                # Load and return the selected song
                return self.lyrics_loader.load_song(song_filename)
                
            except (ValueError, IndexError):
                self.console.print("[bold red]❌ Lựa chọn không hợp lệ![/bold red]")
            except Exception as e:
                self.console.print(f"[bold red]❌ Lỗi khi tải bài hát: {e}[/bold red]")
    
    def _get_available_songs(self) -> list[dict]:
        """Get list of available songs with their information.
        
        Returns:
            List of dictionaries containing song information
        """
        song_files = self.lyrics_loader.list_available_songs()
        songs_info = []
        
        for filename in song_files:
            info = self.lyrics_loader.get_song_info(filename)
            if info:
                songs_info.append({
                    'filename': filename,
                    'title': info['title'],
                    'artist': info['artist']
                })
        
        return songs_info
    
    def _display_song_list(self, songs: list[dict]) -> None:
        """Display the list of available songs.
        
        Args:
            songs: List of song information dictionaries
        """
        songs_table = Table(
            title="🎵 Danh sách bài hát có sẵn",
            show_header=True,
            header_style="bold magenta"
        )
        songs_table.add_column("#", style="cyan", justify="center", width=3)
        songs_table.add_column("Tên bài hát", style="green")
        songs_table.add_column("Nghệ sĩ", style="yellow")
        songs_table.add_column("File", style="dim white")
        
        for i, song in enumerate(songs, 1):
            songs_table.add_row(
                str(i),
                song['title'],
                song['artist'],
                f"{song['filename']}.json"
            )
        
        self.console.print(songs_table)
    
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