# Sequel Ace Backup Tool

A command-line tool to backup and restore Sequel Ace favorites including passwords from the macOS Keychain.

## Features

- Backup all Sequel Ace connection favorites
- Extract and backup passwords from macOS Keychain
- Support for SSH tunnel connections (both MySQL and SSH passwords)
- Restore favorites and passwords to a new machine or after reinstall
- List all favorites in a backup file
- Automatic backup of existing favorites before restore

## Requirements

- macOS (uses macOS Keychain for password storage)
- Python 3.6 or higher
- Sequel Ace installed

## Installation

1. Clone or download this repository
2. Make the script executable:

```bash
chmod +x sequel_ace_backup.py
```

## Usage

### Create a Backup

Create a backup with an automatically generated filename:

```bash
./sequel_ace_backup.py backup
```

This will create a file named `sequel_ace_backup_YYYYMMDD_HHMMSS.json` containing all your favorites and passwords.

Create a backup with a custom filename:

```bash
./sequel_ace_backup.py backup -o my_backup.json
```

### List Favorites in a Backup

View all favorites stored in a backup file:

```bash
./sequel_ace_backup.py list -f sequel_ace_backup_20241014_120000.json
```

This will display:
- Connection name
- Connection type (Standard or SSH Tunnel)
- Host, user, and database information
- Whether passwords were backed up (✓ or ✗)
- SSH connection details for tunnel connections

### Restore from a Backup

Restore favorites and passwords from a backup file:

```bash
./sequel_ace_backup.py restore -f sequel_ace_backup_20241014_120000.json
```

This will:
1. Create a backup of your existing favorites (`.backup` file)
2. Restore all favorites from the backup file
3. Restore all passwords to the macOS Keychain

**Note:** You may be prompted by macOS to authorize keychain access when restoring passwords.

## How It Works

### Backup Process

1. Reads the Sequel Ace favorites from:
   ```
   ~/Library/Containers/com.sequel-ace.sequel-ace/Data/Library/Application Support/Sequel Ace/Data/Favorites.plist
   ```

2. For each favorite, extracts the password from the macOS Keychain using the `security` command

3. Saves everything to a JSON file containing:
   - All favorite configurations
   - Passwords (stored securely in the backup file)
   - Timestamp of backup creation

### Restore Process

1. Reads the backup JSON file
2. Creates a backup of existing favorites (`.plist.backup`)
3. Writes the favorites back to the Sequel Ace data directory
4. Restores all passwords to the macOS Keychain

### Keychain Password Format

Sequel Ace stores passwords in the macOS Keychain with:
- Service: `Sequel Ace`
- Account format: `user@host/database` or `user@host`
- SSH passwords use: `SSH:user@host`

## Security Considerations

1. **Backup File Security**: The backup JSON file contains passwords in plain text. Keep it secure:
   - Store in an encrypted location
   - Use encrypted backups (Time Machine with encryption, encrypted disk images, etc.)
   - Delete backups after use if not needed
   - Never commit backup files to version control

2. **Keychain Access**: The tool uses the `security` command to access the Keychain. You may be prompted to authorize access.

3. **File Permissions**: Consider setting restrictive permissions on backup files:
   ```bash
   chmod 600 my_backup.json
   ```

## Troubleshooting

### No passwords found during backup

If the tool shows "No password found" for your favorites:
- The passwords might be stored with a different account name format
- You may need to authorize keychain access
- Passwords might not be saved in Sequel Ace (using SSH keys instead)

### Restore fails

If restore fails:
- Ensure Sequel Ace is not running during restore
- Check that you have write permissions to the Sequel Ace data directory
- Verify the backup file is not corrupted (valid JSON)

### Keychain authorization prompts

When restoring passwords, macOS may prompt you multiple times to authorize keychain access. You can click "Always Allow" to avoid repeated prompts.

## Example Workflow

### Moving to a new Mac

1. On old Mac, create a backup:
   ```bash
   ./sequel_ace_backup.py backup -o sequel_ace_backup.json
   ```

2. Copy `sequel_ace_backup.json` to your new Mac (via USB drive, cloud storage, etc.)

3. On new Mac, install Sequel Ace

4. Restore the backup:
   ```bash
   ./sequel_ace_backup.py restore -f sequel_ace_backup.json
   ```

5. Launch Sequel Ace - all your favorites with passwords should be available

### Regular backups

Create a backup script that runs periodically:

```bash
#!/bin/bash
BACKUP_DIR="$HOME/Documents/SequelAceBackups"
mkdir -p "$BACKUP_DIR"
cd "$BACKUP_DIR"
/path/to/sequel_ace_backup.py backup
# Keep only last 5 backups
ls -t sequel_ace_backup_*.json | tail -n +6 | xargs -r rm
```

## License

This tool is provided as-is for personal use. Feel free to modify and distribute.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
