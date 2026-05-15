"""Utilities for interest radar."""

import time
from typing import Any, Dict, List


def log(msg: str, **kwargs):
    """Simple logger that integrates with Hermes logging."""
    # In a real implementation, use Hermes logging facilities
    print(f"[interest_radar] {msg}")


def with_hindsight_client():
    """Return a hindsight client wrapper.

    For now, we'll use the hindsight_recall/reflect tools via hermes_tools.
    In production, this would be a proper client.
    """
    try:
        from hermes_tools import hindsight_recall, hindsight_reflect
        return {"recall": hindsight_recall, "reflect": hindsight_reflect}
    except ImportError:
        return None


def with_hermes_memory():
    """Return Hermes memory client if available."""
    try:
        from hermes_tools import memory
        return memory
    except ImportError:
        return None
