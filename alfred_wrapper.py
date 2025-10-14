#!/usr/bin/env python3
"""
Alfred Workflow wrapper for Sequel Ace Backup Tool
Provides interactive menu for backup and restore operations
"""

import json
import sys
import os
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
BACKUP_SCRIPT = SCRIPT_DIR / "sequel_ace_backup.py"


def create_item(title, subtitle, arg, icon="icon.png", valid=True):
    """Create an Alfred script filter item."""
    return {
        "title": title,
        "subtitle": subtitle,
        "arg": arg,
        "valid": valid,
        "icon": {"path": icon}
    }


def main():
    """Main entry point for Alfred workflow."""
    query = sys.argv[1] if len(sys.argv) > 1 else ""

    items = []

    # Main menu items
    if not query or query.lower().startswith("b"):
        items.append(create_item(
            "Backup",
            "Create a new backup of Sequel Ace favorites to 1Password",
            "backup",
            "📦"
        ))

    if not query or query.lower().startswith("r"):
        items.append(create_item(
            "Restore",
            "Restore Sequel Ace favorites from the most recent backup",
            "restore",
            "♻️"
        ))

    if not query or query.lower().startswith("l"):
        items.append(create_item(
            "List Backups",
            "Show all available backups in 1Password",
            "list",
            "📋"
        ))

    if not query or query.lower().startswith("s"):
        items.append(create_item(
            "Show Favorites",
            "Display favorites in the most recent backup",
            "show",
            "👁️"
        ))

    if not query or query.lower().startswith("c"):
        items.append(create_item(
            "Clear All",
            "Delete all Sequel Ace favorites (creates backup first)",
            "clear",
            "🗑️"
        ))

    # Output JSON for Alfred
    print(json.dumps({"items": items}, indent=2))


if __name__ == "__main__":
    main()
