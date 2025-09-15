from pathlib import Path
from urllib import parse
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
import qrcode
from numpy import random
import base64
from .models import GAME_PROMPTS

load_dotenv()


def generate_rand_id() -> dict[str, str]:
    """Generate one time links to games"""
    seed = os.getenv("RAND_ID_SEED", "42")
    random.seed(int(seed))
    game_ids = list(GAME_PROMPTS.keys())
    generated: dict[str, str] = {}
    for id in game_ids:
        while (
            rand_id := base64.urlsafe_b64encode(random.bytes(6)).decode()
        ) in generated:
            pass
        generated[rand_id] = id

    return generated


def display_links(links: dict[str, str]):
    """Display one-time links to the games"""
    console = Console()
    base_url = os.getenv("BASE_URL")
    if not base_url:
        console.print("[red]Env BASE_URL not set[/red]")
        exit(1)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("One-time link")
    table.add_column("Game ID")
    for rand_id, game_id in links.items():
        link = parse.urljoin(base_url, f"/{rand_id}/")
        table.add_row(link, game_id)

    console.print(table)


def save_qrcode(links: dict[str, str]):
    """Save the QR codes to the games"""
    console = Console()
    base_url = os.getenv("BASE_URL")
    if not base_url:
        console.print("[red]Env BASE_URL not set[/red]")
        exit(1)

    data_dir = os.getenv("DATA_DIR")
    if not data_dir:
        console.print("[red]Env DATA_DIR not set[/red]")
        exit(1)

    data_dir = Path(data_dir)

    for rand_id, game_id in links.items():
        link = parse.urljoin(base_url, f"/{rand_id}/")
        path = data_dir / f"{game_id}.png"
        img = qrcode.make(link)
        img.save(path)
        console.print(
            f"[green]:white_check_mark: QR Code saved to {path.as_posix()}[/green]"
        )


RAND_ID_MAPPING = generate_rand_id()

display_links(RAND_ID_MAPPING)
save_qrcode(RAND_ID_MAPPING)

__all__ = ["RAND_ID_MAPPING"]
