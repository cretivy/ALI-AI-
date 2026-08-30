from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

console = Console()

def show_banner():
    banner_text = Text()
    banner_text.append("   🤖 JARVIS - O'ZBEK TILI OVOZLI YORDAMCHISI   \n", style="bold cyan")
    banner_text.append("   Apple Silicon (MacBook Air M5) uchun moslashtirilgan   ", style="dim white")
    
    panel = Panel(
        banner_text,
        title="[bold magenta]JARVIS v1.0[/bold magenta]",
        border_style="cyan",
        expand=False
    )
    console.print(panel)

def show_status(status_msg, style="bold yellow"):
    console.print(f"[{style}]>>> {status_msg}[/{style}]")

def show_transcript(user_text):
    panel = Panel(
        f"[bold white]\"{user_text}\"[/bold white]",
        title="[bold green]🎤 Olingan Ovozli Buyruq (STT)[/bold green]",
        border_style="green"
    )
    console.print(panel)

def show_action_result(intent, response_text, details=""):
    table = Table(title="⚡ Jarvis Bajarilgan Amal", border_style="blue")
    table.add_column("Kategoriya", style="cyan")
    table.add_column("Tafsilotlar", style="white")

    table.add_row("Buyruq Turi (Intent)", str(intent))
    table.add_row("Jarvis Javobi", str(response_text))
    if details:
        table.add_row("Amal Natijasi", str(details))

    console.print(table)
