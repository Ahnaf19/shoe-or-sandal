"""
Main entry point for the shoe-or-sandal weather reminder bot.

This is a simple wrapper that delegates to the CLI implementation.
The actual application logic is in src/presentation/cli.py
"""

from src.presentation.cli import main

if __name__ == "__main__":
    main()
