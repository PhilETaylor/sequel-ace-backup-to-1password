# Sequel Ace Favourites Backup Tool

A command-line tool to backup and restore Sequel Ace favorites including passwords, with secure storage in 1Password.

**THIS TOOL WAS 100% CREATED BY CLAUDE.AI - YOU CAN READ THE SOURCE AND MAKE UP YOUR OWN MIND ON ITS QUALITY/SECURITY**

It fits my needs perfectly, and works perfectly.

A previous iteration just dumped favorites to/from a JSON file - you could ask Claude to do it again if you dont want 1Password integration, but just note that is insecure as it stores the passwords in plain text.

## Features

- Backup all Sequel Ace connection favorites to 1Password as Secure Notes
- Extract and backup passwords from macOS Keychain
- Support for SSH tunnel connections (both MySQL and SSH passwords)
- Restore favorites and passwords to a new machine or after reinstall
- List all backups stored in 1Password
- Show favorites in a specific backup
- Clear all Sequel Ace favorites and passwords (with safety prompts)
- Automatic backup of existing favorites before restore
- No local JSON files - everything stored securely in 1Password

## Requirements

- macOS (uses macOS Keychain for password storage)
- Python 3.6 or higher
- Sequel Ace installed
- 1Password account
- 1Password CLI (op) installed and configured

## Installation

1. Clone or download this repository

2. Install 1Password CLI if not already installed:
   ```bash
   brew install --cask 1password-cli
   ```

3. Sign in to 1Password CLI (You first need to enable CLI in 1Password settings if you have not already done so):
   ```bash
   op signin
   ```

4. Make the script executable:
   ```bash
   chmod +x sequel_ace_backup.py
   ```

## Usage

### Create a Backup

Create a backup with an automatically generated title (stored in 1Password):

```bash
./sequel_ace_backup.py backup
```

This creates a Secure Note in 1Password with a title like `Sequel Ace Backup - 2024-10-14 12:00:00`.

Create a backup with a custom title:

```bash
./sequel_ace_backup.py backup --title "Before Database Migration"
```

Create a backup in a different 1Password vault:

```bash
./sequel_ace_backup.py backup --vault Shared
```

### List All Backups

View all Sequel Ace backups stored in 1Password:

```bash
./sequel_ace_backup.py list
```

This displays:
- Backup title and creation timestamp
- 1Password item ID

To list backups in a different vault:

```bash
./sequel_ace_backup.py list --vault Shared
```

### Show Favorites in a Backup

View all favorites in the most recent backup:

```bash
./sequel_ace_backup.py show
```

View favorites in a specific backup:

```bash
./sequel_ace_backup.py show --title "Sequel Ace Backup - 2024-10-14 12:00:00"
```

This displays for each favorite:
- Connection name
- Connection type (Standard or SSH Tunnel)
- Host, user, and database information
- Whether passwords were backed up (✓ or ✗)
- SSH connection details for tunnel connections

### Restore from a Backup

Restore from the most recent backup:

```bash
./sequel_ace_backup.py restore
```

Restore from a specific backup:

```bash
./sequel_ace_backup.py restore --title "Sequel Ace Backup - 2024-10-14 12:00:00"
```

Restore from a different vault:

```bash
./sequel_ace_backup.py restore --vault Shared
```

This will:
1. Quit Sequel Ace if it's running
2. Create a backup of your existing favorites (`.plist.backup` file)
3. Restore all favorites from the backup
4. Restore all passwords to the macOS Keychain

**Note:** You may be prompted by macOS to authorize keychain access when restoring passwords.

### Clear All Favorites

Remove all Sequel Ace favorites and passwords (with safety prompts):

```bash
./sequel_ace_backup.py clear
```

This will:
1. Show a warning and count of favorites to be deleted
2. Prompt you to create a backup first (recommended)
3. Require typing "DELETE" to confirm
4. Delete all favorites and keychain entries

Skip the backup prompt (dangerous):

```bash
./sequel_ace_backup.py clear --skip-backup
```

## How It Works

### Backup Process

1. Reads the Sequel Ace favorites from:
   ```
   ~/Library/Containers/com.sequel-ace.sequel-ace/Data/Library/Application Support/Sequel Ace/Data/Favorites.plist
   ```

2. For each favorite, extracts the password from the macOS Keychain using the `security` command

3. Creates a Secure Note in 1Password containing:
   - All favorite configurations (from the plist)
   - All passwords (MySQL and SSH)
   - Timestamp of backup creation
   - Tagged with `sequel-ace-backup` for easy filtering

### Restore Process

1. Retrieves the backup from 1Password
2. Quits Sequel Ace if it's running
3. Creates a backup of existing favorites (`.plist.backup`)
4. Writes the favorites back to the Sequel Ace data directory
5. Restores all passwords to the macOS Keychain with proper access permissions

### Keychain Password Format

Sequel Ace stores passwords in the macOS Keychain with:
- **MySQL passwords:**
  - Service: `Sequel Ace : [favorite name] ([ID])`
  - Account: `user@host/database` or `user@host/`
- **SSH passwords:**
  - Service: `Sequel Ace SSHTunnel : [favorite name] ([ID])`
  - Account: `ssh_user@ssh_host`

### 1Password Integration

Backups are stored as Secure Notes in 1Password with:
- Title format: `Sequel Ace Backup - YYYY-MM-DD HH:MM:SS`
- Tag: `sequel-ace-backup` (for filtering)
- Default vault: `Private` (configurable)
- Content: JSON structure with favorites and passwords

## Security Considerations

1. **1Password Storage**: Backups are stored as Secure Notes in 1Password, leveraging:
   - End-to-end encryption
   - 1Password's security infrastructure
   - Access control via your 1Password account
   - No local files containing passwords
   - Secure sharing via 1Password vaults

2. **Keychain Access**: The tool uses the `security` command to access the Keychain. You may be prompted to authorize access when:
   - Reading passwords during backup
   - Writing passwords during restore

3. **1Password CLI Authentication**:
   - The tool checks for `op` CLI authentication on startup
   - Run `op signin` if you see authentication errors
   - Consider using 1Password biometric unlock for convenience

4. **Backup Content**: While stored securely in 1Password, backups contain:
   - Database connection details
   - Usernames and passwords in JSON format
   - Only share backups with trusted individuals via appropriate 1Password vaults

## Troubleshooting

### 1Password CLI errors

If you see "1Password CLI is not installed" or authentication errors:
- Install: `brew install --cask 1password-cli`
- Sign in: `op signin`
- Verify: `op account list`

### No passwords found during backup

If the tool shows "⚠ No password found" for your favorites:
- Passwords might not be saved to the keychain in Sequel Ace
- In Sequel Ace, edit each favorite and check "Save password in keychain"
- Some connections may use SSH keys instead of passwords

### Restore fails

If restore fails:
- Ensure you're signed in to 1Password CLI: `op signin`
- The tool will automatically quit Sequel Ace before restore
- Check that you have write permissions to the Sequel Ace data directory
- Verify the backup exists in 1Password: `./sequel_ace_backup.py list`

### Keychain authorization prompts

When restoring passwords, macOS may prompt you multiple times to authorize keychain access:
- Click "Always Allow" to avoid repeated prompts
- The tool sets access permissions for Sequel Ace automatically
- You may see one prompt per connection on first use

### Backup not found

If `restore` or `show` can't find a backup:
- Run `./sequel_ace_backup.py list` to see available backups
- Specify the exact title: `--title "Sequel Ace Backup - 2024-10-14 12:00:00"`
- Check the vault: `--vault YourVaultName`
- Ensure the backup wasn't deleted from 1Password

## Example Workflows

### Moving to a new Mac

1. On old Mac, create a backup:
   ```bash
   ./sequel_ace_backup.py backup --title "Mac Migration Backup"
   ```

2. On new Mac:
   - Install Sequel Ace
   - Install 1Password and 1Password CLI
   - Sign in to 1Password: `op signin`

3. Restore the backup:
   ```bash
   ./sequel_ace_backup.py restore
   ```

4. Launch Sequel Ace - all your favorites with passwords should be available

### Regular backups

Create a backup script that runs periodically via cron or launchd:

```bash
#!/bin/bash
# ~/bin/backup-sequel-ace.sh

# Ensure 1Password CLI is authenticated
if ! op account list &>/dev/null; then
    echo "Error: 1Password CLI not authenticated" >&2
    exit 1
fi

# Create backup
/path/to/sequel_ace_backup.py backup --title "Automated Backup - $(date +%Y-%m-%d)"

# Optional: Cleanup old backups (keep last 10)
# This would require additional 'op' commands to list and delete old items
```

### Before major changes

Before making significant database configuration changes:

```bash
./sequel_ace_backup.py backup --title "Before Adding Production Servers"
```

### Team sharing (via shared vault)

Share connection favorites with your team:

```bash
# Create backup in shared vault
./sequel_ace_backup.py backup --vault "Team Database Connections" --title "Staging Environment Connections"

# Team members restore from shared vault
./sequel_ace_backup.py restore --vault "Team Database Connections"
```

### Clean install

If you need to start fresh:

```bash
# Backup first
./sequel_ace_backup.py backup --title "Pre-Clean Backup"

# Clear everything
./sequel_ace_backup.py clear

# Optionally restore later
./sequel_ace_backup.py restore
```

## Advanced Usage

### Multiple vaults

Store different types of backups in different vaults:

```bash
# Personal connections
./sequel_ace_backup.py backup --vault Private

# Work connections
./sequel_ace_backup.py backup --vault Work

# Shared team connections
./sequel_ace_backup.py backup --vault "Team Shared"
```

### Scripting

Use in scripts with error handling:

```bash
#!/bin/bash

if ./sequel_ace_backup.py backup --title "Nightly Backup"; then
    echo "Backup successful"
else
    echo "Backup failed" >&2
    # Send notification, log to monitoring, etc.
fi
```

### List specific backup details

```bash
# List all backups
./sequel_ace_backup.py list

# Show contents of a specific backup
./sequel_ace_backup.py show --title "Sequel Ace Backup - 2024-10-14 12:00:00"
```

## Command Reference

```
usage: sequel_ace_backup.py [-h] [--vault VAULT] {backup,restore,list,show,clear} ...

Commands:
  backup                Create a backup of favorites and passwords
    --title TITLE       Custom title for the backup

  restore              Restore favorites and passwords from backup
    --title TITLE       Title of backup to restore (defaults to most recent)

  list                 List all backups in 1Password

  show                 Show favorites in a backup
    --title TITLE       Title of backup to show (defaults to most recent)

  clear                Clear all Sequel Ace favorites and passwords
    --skip-backup       Skip backup prompt (dangerous!)

Global options:
  --vault VAULT        1Password vault to use (default: Private)
  -h, --help          Show this help message and exit
```

## Technical Details

### Files and Locations

- **Favorites plist**: `~/Library/Containers/com.sequel-ace.sequel-ace/Data/Library/Application Support/Sequel Ace/Data/Favorites.plist`
- **Backup location**: `.plist.backup` (created before restore)
- **Keychain**: macOS Keychain (accessed via `security` command)
- **1Password storage**: Secure Notes with tag `sequel-ace-backup`

### Python Requirements

- Python 3.6+
- Standard library only (no external dependencies)
- Uses: `argparse`, `json`, `plistlib`, `subprocess`, `pathlib`

### 1Password CLI Commands Used

- `op account list` - Check authentication
- `op item create` - Create backup
- `op item get` - Retrieve backup
- `op item list` - List backups

## License

This tool is provided as-is for personal use. Feel free to modify and distribute.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Credits

Created to solve the problem of migrating Sequel Ace favorites between machines while preserving passwords securely.
