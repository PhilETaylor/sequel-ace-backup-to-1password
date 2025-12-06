# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based command-line tool for backing up and restoring Sequel Ace database connection favorites, including passwords. Backups are stored securely in 1Password as Secure Notes, with all passwords extracted from and restored to the macOS Keychain.

## Core Commands

### Running the tool

```bash
./sequel_ace_backup.py backup              # Create backup
./sequel_ace_backup.py restore             # Restore from most recent backup
./sequel_ace_backup.py list                # List all backups
./sequel_ace_backup.py show                # Show favorites in backup
./sequel_ace_backup.py clear               # Clear all favorites
./sequel_ace_backup.py --vault NAME <cmd>  # Use different 1Password vault
```

### Testing

No automated tests exist. Manual testing workflow:

1. Create test favorites in Sequel Ace with saved passwords
2. Run backup command
3. Verify backup appears in 1Password
4. Clear favorites
5. Restore and verify favorites and passwords work

## Architecture

### Main Components

**sequel_ace_backup.py** (805 lines)
- `SequelAceBackup` class handles all operations
- Uses Python stdlib only (plistlib, subprocess, argparse, json)
- Interfaces with: macOS Keychain, 1Password CLI, Sequel Ace plist file

### Key File Paths

```python
SEQUEL_ACE_DATA_PATH = "~/Library/Containers/com.sequel-ace.sequel-ace/Data/Library/Application Support/Sequel Ace/Data"
FAVORITES_FILE = "Favorites.plist"
```

### Keychain Password Naming Conventions

**MySQL passwords:**
- Service: `Sequel Ace : [favorite name] ([ID])`
- Account: `user@host/database` or `user@host/`

**SSH passwords (for SSH tunnel connections):**
- Service: `Sequel Ace SSHTunnel : [favorite name] ([ID])`
- Account: `ssh_user@ssh_host`

### 1Password Integration

Backups stored as Secure Notes with:
- Title format: `Sequel Ace Backup - YYYY-MM-DD HH:MM:SS`
- Tag: `sequel-ace-backup`
- Content: JSON with favorites plist data and extracted passwords

CLI commands used:
```bash
op account list          # Check authentication
op item create          # Create backup
op item get             # Retrieve backup
op item list            # List backups
```

### Backup Data Structure

```json
{
  "timestamp": "ISO 8601 timestamp",
  "favorites": {
    "Favorites Root": {
      "Children": [
        {
          "id": "unique_id",
          "name": "connection_name",
          "host": "hostname",
          "user": "username",
          "database": "dbname",
          "type": 0,  // 0=standard, 2=SSH tunnel
          "sshHost": "ssh_host",
          "sshUser": "ssh_user"
        }
      ]
    }
  },
  "passwords": {
    "unique_id": {
      "service": "keychain_service_name",
      "account": "keychain_account_name",
      "password": "password_value",
      "type": "mysql"
    },
    "unique_id_ssh": {
      "service": "ssh_keychain_service_name",
      "account": "ssh_keychain_account_name",
      "password": "ssh_password_value",
      "type": "ssh"
    }
  }
}
```

## Important Behaviors

### Backup Process

1. Reads Favorites.plist using plistlib
2. For each favorite, extracts password from Keychain using `security find-generic-password -w`
3. Handles both MySQL and SSH tunnel passwords (connection type 2)
4. Creates 1Password Secure Note with JSON backup data

### Restore Process

1. Quits Sequel Ace if running (using osascript)
2. Creates `.plist.backup` of existing favorites
3. Writes favorites data back to plist file
4. Restores passwords to Keychain using `security add-generic-password`
5. Sets access permissions for Sequel Ace binary using `-T` flag

### Keychain Access

- Uses macOS `security` command-line tool
- Grants access to `/Applications/Sequel Ace.app/Contents/MacOS/Sequel Ace` binary
- Users may be prompted for keychain access on first restore

## Error Handling

Custom exceptions:
- `OnePasswordError` - for all 1Password CLI related errors

Error conditions checked:
- 1Password CLI installed and authenticated (checks `op account list`)
- Favorites.plist exists
- Write permissions to Sequel Ace data directory
- Keychain operations may fail silently (returns None)

## Security Considerations

- Passwords stored in 1Password with end-to-end encryption
- No local JSON files with passwords 
- Keychain operations use macOS security APIs
- Tool requires user's normal permissions (not sudo)
- Backup content includes sensitive credentials in JSON format
