"""Centralised logging configuration."""

import logging

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    """Return a logger with a consistent format.  Safe to call multiple times."""
    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        _CONFIGURED = True
    return logging.getLogger(name)
