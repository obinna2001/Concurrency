"""Command-line entry point for database exports."""

import argparse
import logging


def main() -> None:
    """Parse the export mode and run the selected exporter."""
    parser = argparse.ArgumentParser(
        prog="concurrency",
        description="Export database rows to CSV files.",
    )
    parser.add_argument(
        "process",
        nargs="?",
        choices=("concurrent", "sequential"),
        default="concurrent",
        help="Export mode (default: concurrent)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        style="{",
        format="{asctime}: [{levelname}] {name} - {message}",
    )

    if args.process == "concurrent":
        from .script.concurrent import multi_threaded_download_process

        multi_threaded_download_process()
    else:
        from .script.single import single_threaded_download_process

        single_threaded_download_process()
