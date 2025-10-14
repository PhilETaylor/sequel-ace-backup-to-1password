#!/usr/bin/env python3
"""
Sequel Ace Favorites Backup and Restore Tool with 1Password Integration

This tool allows you to backup and restore Sequel Ace favorites including passwords
stored in the macOS Keychain. Backups are stored in 1Password as Secure Notes.
"""

import argparse
import json
import plistlib
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class OnePasswordError(Exception):
    """Exception raised for 1Password CLI errors."""
    pass


class SequelAceBackup:
    """Handles backup and restore operations for Sequel Ace favorites."""

    SEQUEL_ACE_DATA_PATH = Path.home() / "Library/Containers/com.sequel-ace.sequel-ace/Data/Library/Application Support/Sequel Ace/Data"
    FAVORITES_FILE = "Favorites.plist"
    KEYCHAIN_SERVICE = "Sequel Ace"
    KEYCHAIN_SERVICE_PREFIX = "Sequel Ace : "
    ONEPASSWORD_BACKUP_PREFIX = "Sequel Ace Backup"
    ONEPASSWORD_TAG = "sequel-ace-backup"

    def __init__(self, vault: str = "Private"):
        """Initialize the backup handler.

        Args:
            vault: 1Password vault name to use for backups (default: Private)
        """
        self.vault = vault
        self._check_op_cli()

    def _check_op_cli(self) -> None:
        """Check if 1Password CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ['op', 'account', 'list'],
                capture_output=True,
                text=True,
                check=True
            )
            if not result.stdout.strip():
                raise OnePasswordError(
                    "1Password CLI is not signed in. Please run: op signin"
                )
        except FileNotFoundError:
            raise OnePasswordError(
                "1Password CLI is not installed. Please install it from: "
                "https://developer.1password.com/docs/cli/get-started/"
            )
        except subprocess.CalledProcessError as e:
            raise OnePasswordError(
                f"1Password CLI error: {e.stderr}. Please run: op signin"
            )

    def _run_op_command(self, args: List[str]) -> str:
        """Run a 1Password CLI command and return the output.

        Args:
            args: Command arguments to pass to 'op'

        Returns:
            Command output as string

        Raises:
            OnePasswordError: If the command fails
        """
        try:
            result = subprocess.run(
                ['op'] + args,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise OnePasswordError(f"1Password CLI error: {e.stderr}")

    def get_favorites_path(self) -> Path:
        """Get the path to the Favorites.plist file."""
        return self.SEQUEL_ACE_DATA_PATH / self.FAVORITES_FILE

    def read_favorites(self) -> Dict:
        """Read the Favorites.plist file."""
        favorites_path = self.get_favorites_path()

        if not favorites_path.exists():
            raise FileNotFoundError(
                f"Favorites file not found at {favorites_path}. "
                "Is Sequel Ace installed and have you created any favorites?"
            )

        with open(favorites_path, 'rb') as f:
            return plistlib.load(f)

    def write_favorites(self, favorites_data: Dict) -> None:
        """Write data to the Favorites.plist file."""
        favorites_path = self.get_favorites_path()

        # Create backup of existing file
        if favorites_path.exists():
            backup_file = favorites_path.with_suffix('.plist.backup')
            shutil.copy2(favorites_path, backup_file)
            print(f"Created backup of existing favorites at {backup_file}")

        # Ensure directory exists
        favorites_path.parent.mkdir(parents=True, exist_ok=True)

        with open(favorites_path, 'wb') as f:
            plistlib.dump(favorites_data, f)

    def get_keychain_account_name(self, favorite: Dict) -> str:
        """Generate the keychain account name for a favorite.

        Sequel Ace uses: user@host/database or user@host/ (with trailing slash if no database)
        """
        user = favorite.get('user', '')
        host = favorite.get('host', '')
        database = favorite.get('database', '')

        if database:
            return f"{user}@{host}/{database}"
        else:
            return f"{user}@{host}/"

    def get_keychain_service_name(self, favorite: Dict) -> str:
        """Generate the keychain service name for a favorite.

        Sequel Ace uses: "Sequel Ace : [favorite name] ([ID])"
        """
        name = favorite.get('name', 'Unknown')
        fav_id = favorite.get('id', '')
        return f"{self.KEYCHAIN_SERVICE_PREFIX}{name} ({fav_id})"

    def get_ssh_keychain_service_name(self, favorite: Dict) -> Optional[str]:
        """Generate the SSH keychain service name if SSH is used.

        Sequel Ace uses: "Sequel Ace SSHTunnel : [favorite name] ([ID])"
        """
        connection_type = favorite.get('type', 0)
        if connection_type == 2:  # SSH connection
            name = favorite.get('name', 'Unknown')
            fav_id = favorite.get('id', '')
            return f"Sequel Ace SSHTunnel : {name} ({fav_id})"
        return None

    def get_ssh_keychain_account_name(self, favorite: Dict) -> Optional[str]:
        """Generate the SSH keychain account name if SSH is used.

        Sequel Ace uses: ssh_user@ssh_host
        """
        connection_type = favorite.get('type', 0)
        if connection_type == 2:  # SSH connection
            ssh_user = favorite.get('sshUser', '')
            ssh_host = favorite.get('sshHost', '')
            if ssh_user and ssh_host:
                return f"{ssh_user}@{ssh_host}"
        return None

    def get_password_from_keychain(self, service_name: str, account_name: str) -> Optional[str]:
        """Retrieve a password from the macOS Keychain.

        Args:
            service_name: The service name in the keychain
            account_name: The account name in the keychain

        Returns:
            The password if found, None otherwise
        """
        try:
            result = subprocess.run(
                ['security', 'find-generic-password',
                 '-s', service_name,
                 '-a', account_name,
                 '-w'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def quit_sequel_ace(self) -> None:
        """Quit Sequel Ace if it's running."""
        try:
            result = subprocess.run(
                ['osascript', '-e', 'tell application "Sequel Ace" to quit'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                print("Sequel Ace has been quit")
                # Wait a moment for the app to fully close
                time.sleep(1)
        except Exception as e:
            print(f"Note: Could not quit Sequel Ace: {e}", file=sys.stderr)

    def save_password_to_keychain(self, service_name: str, account_name: str, password: str) -> bool:
        """Save a password to the macOS Keychain.

        Args:
            service_name: The service name in the keychain
            account_name: The account name in the keychain
            password: The password to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # First, try to delete existing entry
            subprocess.run(
                ['security', 'delete-generic-password',
                 '-s', service_name,
                 '-a', account_name],
                capture_output=True,
                check=False  # Don't fail if entry doesn't exist
            )

            # Find Sequel Ace executable path (not just the .app bundle)
            sequel_ace_binary = "/Applications/Sequel Ace.app/Contents/MacOS/Sequel Ace"

            # Add the new password with access permissions
            # -T grants access to specific application without prompting
            # Using the actual binary path instead of the .app bundle
            cmd = [
                'security', 'add-generic-password',
                '-s', service_name,
                '-a', account_name,
                '-w', password,
                '-T', sequel_ace_binary,  # Grant access to Sequel Ace binary
                '-T', '/usr/bin/security',  # Allow security command itself
                '-T', '',  # Empty string = this tool itself
                '-U'  # Update if exists
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error saving password for {account_name}: {e.stderr}", file=sys.stderr)
            return False

    def _save_to_1password(self, backup_data: Dict, title: str) -> str:
        """Save backup data to 1Password.

        Args:
            backup_data: The backup data to save
            title: Title for the 1Password item

        Returns:
            The item ID of the created backup

        Raises:
            OnePasswordError: If saving fails
        """
        # Convert backup data to JSON string
        backup_json = json.dumps(backup_data, indent=2)

        # Create a Secure Note in 1Password
        # Using op item create with proper encoding
        try:
            result = self._run_op_command([
                'item', 'create',
                '--category', 'Secure Note',
                '--title', title,
                '--vault', self.vault,
                '--tags', self.ONEPASSWORD_TAG,
                '--format', 'json',
                f'notesPlain={backup_json}'
            ])

            # Parse the result to get the item ID
            item_data = json.loads(result)
            return item_data['id']

        except (json.JSONDecodeError, KeyError) as e:
            raise OnePasswordError(f"Failed to parse 1Password response: {e}")

    def _get_from_1password(self, title: str) -> Dict:
        """Retrieve backup data from 1Password by title.

        Args:
            title: Title of the 1Password item

        Returns:
            The backup data

        Raises:
            OnePasswordError: If retrieval fails
        """
        try:
            # Get the item by title
            result = self._run_op_command([
                'item', 'get', title,
                '--vault', self.vault,
                '--format', 'json'
            ])

            item_data = json.loads(result)

            # Extract the notes field which contains our backup JSON
            notes = None
            for field in item_data.get('fields', []):
                if field.get('id') == 'notesPlain':
                    notes = field.get('value', '')
                    break

            if not notes:
                raise OnePasswordError(f"No backup data found in item: {title}")

            return json.loads(notes)

        except json.JSONDecodeError as e:
            raise OnePasswordError(f"Failed to parse backup data: {e}")

    def _list_1password_backups(self) -> List[Tuple[str, str, str]]:
        """List all Sequel Ace backups in 1Password.

        Returns:
            List of tuples (id, title, created_at)
        """
        try:
            result = self._run_op_command([
                'item', 'list',
                '--vault', self.vault,
                '--tags', self.ONEPASSWORD_TAG,
                '--format', 'json'
            ])

            items = json.loads(result)
            backups = []

            for item in items:
                if item.get('title', '').startswith(self.ONEPASSWORD_BACKUP_PREFIX):
                    backups.append((
                        item['id'],
                        item['title'],
                        item.get('created_at', 'Unknown')
                    ))

            # Sort by title (which includes timestamp) in reverse
            backups.sort(key=lambda x: x[1], reverse=True)
            return backups

        except json.JSONDecodeError as e:
            raise OnePasswordError(f"Failed to parse 1Password items: {e}")

    def backup(self, title: Optional[str] = None) -> None:
        """Create a backup of Sequel Ace favorites and passwords to 1Password.

        Args:
            title: Optional custom title for the backup. If None, generates timestamp-based title.
        """
        print(f"Reading favorites from {self.get_favorites_path()}...")
        favorites_data = self.read_favorites()

        timestamp = datetime.now()
        if not title:
            title = f"{self.ONEPASSWORD_BACKUP_PREFIX} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

        backup_data = {
            'timestamp': timestamp.isoformat(),
            'favorites': favorites_data,
            'passwords': {}
        }

        # Extract passwords from keychain
        favorites_root = favorites_data.get('Favorites Root', {})
        children = favorites_root.get('Children', [])

        print(f"Found {len(children)} favorites")
        print("\nNote: Passwords are only backed up if they were saved to the keychain.")
        print("In Sequel Ace, edit each favorite and check 'Save password in keychain'")
        print("to ensure passwords are included in backups.\n")
        print("Extracting passwords from Keychain...")

        for favorite in children:
            name = favorite.get('name', 'Unknown')
            fav_id = str(favorite.get('id', ''))

            # Get MySQL password
            service_name = self.get_keychain_service_name(favorite)
            account_name = self.get_keychain_account_name(favorite)
            password = self.get_password_from_keychain(service_name, account_name)

            if password:
                backup_data['passwords'][fav_id] = {
                    'service': service_name,
                    'account': account_name,
                    'password': password,
                    'type': 'mysql'
                }
                print(f"  ✓ Extracted password for: {name}")
            else:
                print(f"  ⚠ No password found for: {name}")

            # Get SSH password if applicable
            ssh_service_name = self.get_ssh_keychain_service_name(favorite)
            ssh_account_name = self.get_ssh_keychain_account_name(favorite)
            if ssh_service_name and ssh_account_name:
                ssh_password = self.get_password_from_keychain(ssh_service_name, ssh_account_name)
                if ssh_password:
                    ssh_id = f"{fav_id}_ssh"
                    backup_data['passwords'][ssh_id] = {
                        'service': ssh_service_name,
                        'account': ssh_account_name,
                        'password': ssh_password,
                        'type': 'ssh'
                    }
                    print(f"  ✓ Extracted SSH password for: {name}")

        # Save to 1Password
        print(f"\nSaving backup to 1Password (vault: {self.vault})...")
        item_id = self._save_to_1password(backup_data, title)

        print(f"\n✓ Backup saved to 1Password!")
        print(f"  Title: {title}")
        print(f"  Item ID: {item_id}")
        print(f"  Vault: {self.vault}")
        print(f"  Favorites: {len(children)}")
        print(f"  Passwords: {len(backup_data['passwords'])}")

    def restore(self, title: Optional[str] = None) -> None:
        """Restore Sequel Ace favorites and passwords from a 1Password backup.

        Args:
            title: Title of the backup to restore. If None, restores the most recent backup.
        """
        # If no title provided, get the most recent backup
        if not title:
            print("No backup title specified, finding most recent backup...")
            backups = self._list_1password_backups()
            if not backups:
                raise OnePasswordError(
                    f"No Sequel Ace backups found in vault '{self.vault}'. "
                    "Run 'backup' command first."
                )
            title = backups[0][1]  # Get title of most recent backup
            print(f"Found most recent backup: {title}")

        # Quit Sequel Ace if it's running
        print("\nChecking if Sequel Ace is running...")
        self.quit_sequel_ace()

        print(f"Retrieving backup from 1Password...")
        backup_data = self._get_from_1password(title)

        # Restore favorites
        favorites_data = backup_data.get('favorites', {})
        favorites_root = favorites_data.get('Favorites Root', {})
        children = favorites_root.get('Children', [])

        print(f"Restoring {len(children)} favorites...")
        self.write_favorites(favorites_data)
        print("✓ Favorites restored")

        # Restore passwords
        passwords = backup_data.get('passwords', {})
        print(f"\nRestoring {len(passwords)} passwords to Keychain...")

        success_count = 0
        for fav_id, pwd_data in passwords.items():
            service = pwd_data.get('service', self.KEYCHAIN_SERVICE)  # Fallback for old backups
            account = pwd_data['account']
            password = pwd_data['password']
            pwd_type = pwd_data.get('type', 'mysql')

            if self.save_password_to_keychain(service, account, password):
                print(f"  ✓ Restored {pwd_type} password for: {account}")
                success_count += 1
            else:
                print(f"  ✗ Failed to restore password for: {account}")

        print(f"\n✓ Restore complete!")
        print(f"  Favorites: {len(children)}")
        print(f"  Passwords: {success_count}/{len(passwords)}")
        print(f"\nNote: When you first connect to each database in Sequel Ace,")
        print(f"you may be prompted to allow keychain access. Click 'Always Allow'.")

    def list_backups(self) -> None:
        """List all Sequel Ace backups stored in 1Password."""
        print(f"Searching for backups in vault: {self.vault}\n")

        backups = self._list_1password_backups()

        if not backups:
            print(f"No Sequel Ace backups found in vault '{self.vault}'.")
            print("Create a backup with: sequel_ace_backup.py backup")
            return

        print(f"Found {len(backups)} backup(s):\n")

        for i, (item_id, title, created_at) in enumerate(backups, 1):
            print(f"{i}. {title}")
            print(f"   Created: {created_at}")
            print(f"   Item ID: {item_id}")
            print()

    def list_favorites(self, title: Optional[str] = None) -> None:
        """List all favorites in a specific backup.

        Args:
            title: Title of the backup to list. If None, lists the most recent backup.
        """
        # If no title provided, get the most recent backup
        if not title:
            print("No backup title specified, finding most recent backup...")
            backups = self._list_1password_backups()
            if not backups:
                raise OnePasswordError(
                    f"No Sequel Ace backups found in vault '{self.vault}'. "
                    "Run 'backup' command first."
                )
            title = backups[0][1]  # Get title of most recent backup

        print(f"Retrieving backup: {title}\n")
        backup_data = self._get_from_1password(title)

        timestamp = backup_data.get('timestamp', 'Unknown')
        favorites_data = backup_data.get('favorites', {})
        favorites_root = favorites_data.get('Favorites Root', {})
        children = favorites_root.get('Children', [])
        passwords = backup_data.get('passwords', {})

        print(f"Backup created: {timestamp}")
        print(f"\nFavorites ({len(children)}):\n")

        for i, favorite in enumerate(children, 1):
            name = favorite.get('name', 'Unknown')
            host = favorite.get('host', '')
            user = favorite.get('user', '')
            database = favorite.get('database', '')
            fav_id = str(favorite.get('id', ''))
            connection_type = favorite.get('type', 0)

            type_str = "SSH Tunnel" if connection_type == 2 else "Standard"
            has_password = '✓' if fav_id in passwords else '✗'

            print(f"{i}. {name}")
            print(f"   Type: {type_str}")
            print(f"   Connection: {user}@{host}")
            if database:
                print(f"   Database: {database}")
            print(f"   Password: {has_password}")

            if connection_type == 2:
                ssh_host = favorite.get('sshHost', '')
                ssh_user = favorite.get('sshUser', '')
                ssh_id = f"{fav_id}_ssh"
                has_ssh_pwd = '✓' if ssh_id in passwords else '✗'
                print(f"   SSH: {ssh_user}@{ssh_host} (Password: {has_ssh_pwd})")
            print()

    def delete_password_from_keychain(self, service_name: str, account_name: str) -> bool:
        """Delete a password from the macOS Keychain.

        Args:
            service_name: The service name in the keychain
            account_name: The account name in the keychain

        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ['security', 'delete-generic-password',
                 '-s', service_name,
                 '-a', account_name],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def clear_all_favorites(self, skip_backup: bool = False) -> None:
        """Clear all Sequel Ace favorites and passwords.

        Args:
            skip_backup: If True, skip the backup prompt (dangerous!)
        """
        # Check if favorites file exists
        favorites_path = self.get_favorites_path()
        if not favorites_path.exists():
            print("No Sequel Ace favorites file found. Nothing to clear.")
            return

        # Read current favorites to get count
        try:
            favorites_data = self.read_favorites()
            favorites_root = favorites_data.get('Favorites Root', {})
            children = favorites_root.get('Children', [])
            num_favorites = len(children)
        except Exception as e:
            print(f"Error reading favorites: {e}", file=sys.stderr)
            return

        if num_favorites == 0:
            print("No favorites found to clear.")
            return

        print(f"\n⚠️  WARNING: This will delete ALL {num_favorites} Sequel Ace favorites!")
        print("This action cannot be undone.\n")

        # Offer to create backup first
        if not skip_backup:
            while True:
                response = input("Do you want to create a backup first? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    print("\nCreating backup before clearing...")
                    try:
                        timestamp = datetime.now()
                        title = f"{self.ONEPASSWORD_BACKUP_PREFIX} - Pre-Clear - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                        self.backup(title=title)
                        print("\n✓ Backup created successfully!\n")
                    except Exception as e:
                        print(f"\nError creating backup: {e}", file=sys.stderr)
                        print("Aborting clear operation for safety.", file=sys.stderr)
                        return
                    break
                elif response in ['n', 'no']:
                    print("\nSkipping backup...")
                    break
                else:
                    print("Please enter 'y' or 'n'")

        # Final confirmation
        print("\nFinal confirmation required.")
        while True:
            response = input(f"Type 'DELETE' to confirm clearing all {num_favorites} favorites: ").strip()
            if response == 'DELETE':
                break
            elif response.lower() in ['n', 'no', 'cancel', 'quit', 'exit']:
                print("\nOperation cancelled.")
                return
            else:
                print("Please type 'DELETE' to confirm, or 'cancel' to abort.")

        # Quit Sequel Ace if running
        print("\nChecking if Sequel Ace is running...")
        self.quit_sequel_ace()

        # Delete passwords from keychain
        print(f"\nDeleting {num_favorites} passwords from Keychain...")
        deleted_count = 0

        for favorite in children:
            name = favorite.get('name', 'Unknown')

            # Delete MySQL password
            service_name = self.get_keychain_service_name(favorite)
            account_name = self.get_keychain_account_name(favorite)
            if self.delete_password_from_keychain(service_name, account_name):
                deleted_count += 1
                print(f"  ✓ Deleted password for: {name}")

            # Delete SSH password if applicable
            ssh_service_name = self.get_ssh_keychain_service_name(favorite)
            ssh_account_name = self.get_ssh_keychain_account_name(favorite)
            if ssh_service_name and ssh_account_name:
                if self.delete_password_from_keychain(ssh_service_name, ssh_account_name):
                    print(f"  ✓ Deleted SSH password for: {name}")

        # Clear the favorites file by creating an empty structure
        empty_favorites = {
            'Favorites Root': {
                'Children': [],
                'IsExpanded': True,
                'Name': 'Favorites Root'
            }
        }

        print("\nClearing favorites file...")
        self.write_favorites(empty_favorites)

        print(f"\n✓ All favorites have been cleared!")
        print(f"  Favorites deleted: {num_favorites}")
        print(f"  Keychain entries deleted: {deleted_count}")
        print(f"\nYou can restore from a backup using: {sys.argv[0]} restore")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Backup and restore Sequel Ace favorites including passwords to/from 1Password',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a backup (stored in 1Password)
  %(prog)s backup

  # Create a backup with custom title
  %(prog)s backup --title "My Custom Backup Name"

  # Create a backup to a different vault
  %(prog)s backup --vault Shared

  # List all backups
  %(prog)s list

  # Restore from the most recent backup
  %(prog)s restore

  # Restore from a specific backup
  %(prog)s restore --title "Sequel Ace Backup - 2024-10-14 12:00:00"

  # List favorites in the most recent backup
  %(prog)s show

  # List favorites in a specific backup
  %(prog)s show --title "Sequel Ace Backup - 2024-10-14 12:00:00"

  # Clear all Sequel Ace favorites (prompts for backup first)
  %(prog)s clear

  # Clear all favorites without backup prompt (dangerous!)
  %(prog)s clear --skip-backup
        """
    )

    parser.add_argument(
        '--vault',
        default='Private',
        help='1Password vault to use (default: Private)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create a backup of favorites and passwords')
    backup_parser.add_argument('--title', help='Custom title for the backup')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore favorites and passwords from backup')
    restore_parser.add_argument('--title', help='Title of backup to restore (defaults to most recent)')

    # List command
    list_parser = subparsers.add_parser('list', help='List all backups in 1Password')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show favorites in a backup')
    show_parser.add_argument('--title', help='Title of backup to show (defaults to most recent)')

    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all Sequel Ace favorites and passwords')
    clear_parser.add_argument('--skip-backup', action='store_true',
                             help='Skip backup prompt (dangerous!)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        backup_handler = SequelAceBackup(vault=args.vault)

        if args.command == 'backup':
            backup_handler.backup(title=args.title)

        elif args.command == 'restore':
            backup_handler.restore(title=args.title)

        elif args.command == 'list':
            backup_handler.list_backups()

        elif args.command == 'show':
            backup_handler.list_favorites(title=args.title)

        elif args.command == 'clear':
            backup_handler.clear_all_favorites(skip_backup=args.skip_backup)

    except (OnePasswordError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
