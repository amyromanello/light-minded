"""Console script for light_minded."""
import light_minded

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def main():
    """Console script for light_minded."""
    console.print("Replace this message by putting your code into "
               "light_minded.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    


if __name__ == "__main__":
    app()
