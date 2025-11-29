#!/bin/bash

# Sequel Ace Complete Uninstall Script
# This script removes Sequel Ace and all its data from macOS

set -e  # Exit on error (except where we handle errors explicitly)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
DELETED_COUNT=0
NOT_FOUND_COUNT=0
FAILED_COUNT=0
KEYCHAIN_DELETED=0
KEYCHAIN_FAILED=0

# Parse command line arguments
DRY_RUN=false
FORCE=false
KEEP_KEYCHAIN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --keep-keychain)
            KEEP_KEYCHAIN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run         Show what would be deleted without actually deleting"
            echo "  --force           Skip confirmation prompt"
            echo "  --keep-keychain   Preserve keychain entries (don't delete passwords)"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Pre-flight checks
echo -e "${BLUE}=== Sequel Ace Uninstall Script ===${NC}"
echo ""

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo -e "${RED}Error: This script only works on macOS${NC}"
    exit 1
fi

# Check if running with sudo
if [[ "$EUID" -eq 0 ]]; then
    echo -e "${RED}Error: Do not run this script with sudo${NC}"
    echo "It needs to access your user's Library directory"
    exit 1
fi

# Display mode
if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}DRY RUN MODE - Nothing will actually be deleted${NC}"
    echo ""
fi

# Display warning
echo -e "${YELLOW}WARNING: This will permanently delete:${NC}"
echo "  - Sequel Ace application"
echo "  - All connection favorites"
echo "  - All application data and preferences"
echo "  - Cache and saved state"
if [[ "$KEEP_KEYCHAIN" == false ]]; then
    echo "  - All saved passwords from Keychain"
fi
echo ""

# Confirmation
if [[ "$FORCE" == false ]]; then
    read -p "Are you sure you want to continue? (type 'DELETE' to confirm): " confirm
    if [[ "$confirm" != "DELETE" ]]; then
        echo "Uninstall cancelled"
        exit 0
    fi
    echo ""
fi

# Function to delete a file or directory
delete_path() {
    local path="$1"
    local description="$2"

    if [[ -e "$path" ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            echo -e "${YELLOW}[DRY RUN]${NC} Would delete: $description"
            DELETED_COUNT=$((DELETED_COUNT + 1))
        else
            if rm -rf "$path" 2>/dev/null; then
                echo -e "${GREEN}✓${NC} Deleted: $description"
                DELETED_COUNT=$((DELETED_COUNT + 1))
            else
                echo -e "${RED}✗${NC} Failed to delete: $description"
                FAILED_COUNT=$((FAILED_COUNT + 1))
            fi
        fi
    else
        echo -e "${BLUE}○${NC} Not found: $description"
        NOT_FOUND_COUNT=$((NOT_FOUND_COUNT + 1))
    fi
}

# Step 1: Quit Sequel Ace if running
echo -e "${BLUE}[1/7] Quitting Sequel Ace...${NC}"
if pgrep -x "Sequel Ace" > /dev/null; then
    if [[ "$DRY_RUN" == false ]]; then
        osascript -e 'quit app "Sequel Ace"' 2>/dev/null || true
        sleep 2

        # Force kill if still running
        if pgrep -x "Sequel Ace" > /dev/null; then
            killall "Sequel Ace" 2>/dev/null || true
            sleep 1
        fi
        echo -e "${GREEN}✓${NC} Sequel Ace quit successfully"
    else
        echo -e "${YELLOW}[DRY RUN]${NC} Would quit Sequel Ace"
    fi
else
    echo -e "${BLUE}○${NC} Sequel Ace is not running"
fi
echo ""

# Step 2: Remove Application Bundle
echo -e "${BLUE}[2/7] Removing application bundle...${NC}"
delete_path "/Applications/Sequel Ace.app" "Application bundle"
echo ""

# Step 3: Remove Container Data
echo -e "${BLUE}[3/7] Removing container data...${NC}"
delete_path "$HOME/Library/Containers/com.sequel-ace.sequel-ace" "Container directory (includes favorites and all app data)"
echo ""

# Step 4: Remove Preferences
echo -e "${BLUE}[4/7] Removing preferences...${NC}"
delete_path "$HOME/Library/Preferences/com.sequel-ace.sequel-ace.plist" "Preferences file"
echo ""

# Step 5: Remove Cache
echo -e "${BLUE}[5/7] Removing cache...${NC}"
delete_path "$HOME/Library/Caches/com.sequel-ace.sequel-ace" "Cache directory"
echo ""

# Step 6: Remove Saved Application State
echo -e "${BLUE}[6/7] Removing saved application state...${NC}"
delete_path "$HOME/Library/Saved Application State/com.sequel-ace.sequel-ace.savedState" "Saved application state"
echo ""

# Step 7: Remove Keychain Entries
echo -e "${BLUE}[7/7] Removing keychain entries...${NC}"

if [[ "$KEEP_KEYCHAIN" == true ]]; then
    echo -e "${YELLOW}○${NC} Skipping keychain deletion (--keep-keychain flag set)"
else
    # Function to delete keychain entries by service pattern
    delete_keychain_entries() {
        local service_pattern="$1"
        local description="$2"

        # Find all matching keychain entries
        # We need to get the service name for each entry
        local entries=$(security dump-keychain 2>/dev/null | grep -A 1 "\"svce\"<blob>=\"$service_pattern" | grep "acct" | sed 's/.*"acct"<blob>="\(.*\)".*/\1/' || true)

        if [[ -z "$entries" ]]; then
            # Try alternative method using security find-generic-password
            entries=$(security find-generic-password -s "$service_pattern" 2>&1 | grep "password:" | wc -l || echo "0")
            if [[ "$entries" == "0" ]]; then
                echo -e "${BLUE}○${NC} No $description found"
                return
            fi
        fi

        # Count entries by trying to find them
        local count=0
        local deleted=0
        local failed=0

        # Get all keychain items and filter for Sequel Ace
        while IFS= read -r line; do
            if [[ "$DRY_RUN" == true ]]; then
                echo -e "${YELLOW}[DRY RUN]${NC} Would delete: $description entry"
                deleted=$((deleted + 1))
            else
                # Try to delete the entry
                if security delete-generic-password -s "$service_pattern" 2>/dev/null; then
                    deleted=$((deleted + 1))
                else
                    # Entry might not exist or user cancelled - this is OK
                    break
                fi
            fi
        done < <(security dump-keychain 2>/dev/null | grep "\"svce\"<blob>=\"$service_pattern" || true)

        if [[ $deleted -gt 0 ]]; then
            echo -e "${GREEN}✓${NC} Deleted $deleted $description"
            KEYCHAIN_DELETED=$((KEYCHAIN_DELETED + deleted))
        fi

        if [[ $failed -gt 0 ]]; then
            echo -e "${RED}✗${NC} Failed to delete $failed $description"
            KEYCHAIN_FAILED=$((KEYCHAIN_FAILED + failed))
        fi
    }

    # Alternative approach: Use security find-generic-password with grep
    if [[ "$DRY_RUN" == false ]]; then
        # Delete MySQL password entries
        mysql_count=0
        while security find-generic-password -s "Sequel Ace" 2>/dev/null | grep -q "password:"; do
            if security delete-generic-password -s "Sequel Ace" 2>/dev/null; then
                mysql_count=$((mysql_count + 1))
            else
                break
            fi
        done

        if [[ $mysql_count -gt 0 ]]; then
            echo -e "${GREEN}✓${NC} Deleted $mysql_count MySQL password entries"
            KEYCHAIN_DELETED=$((KEYCHAIN_DELETED + mysql_count))
        else
            echo -e "${BLUE}○${NC} No MySQL password entries found"
        fi

        # Delete SSH password entries
        ssh_count=0
        while security find-generic-password -s "Sequel Ace SSHTunnel" 2>/dev/null | grep -q "password:"; do
            if security delete-generic-password -s "Sequel Ace SSHTunnel" 2>/dev/null; then
                ssh_count=$((ssh_count + 1))
            else
                break
            fi
        done

        if [[ $ssh_count -gt 0 ]]; then
            echo -e "${GREEN}✓${NC} Deleted $ssh_count SSH password entries"
            KEYCHAIN_DELETED=$((KEYCHAIN_DELETED + ssh_count))
        else
            echo -e "${BLUE}○${NC} No SSH password entries found"
        fi
    else
        # Dry run - just count them
        mysql_count=$(security dump-keychain 2>/dev/null | grep "\"svce\"<blob>=\"Sequel Ace\"" | wc -l | tr -d ' ')
        ssh_count=$(security dump-keychain 2>/dev/null | grep "\"svce\"<blob>=\"Sequel Ace SSHTunnel\"" | wc -l | tr -d ' ')

        # Ensure we have valid numbers
        mysql_count=${mysql_count:-0}
        ssh_count=${ssh_count:-0}

        if [[ $mysql_count -gt 0 ]]; then
            echo -e "${YELLOW}[DRY RUN]${NC} Would delete ~$mysql_count MySQL password entries"
            KEYCHAIN_DELETED=$((KEYCHAIN_DELETED + mysql_count))
        else
            echo -e "${BLUE}○${NC} No MySQL password entries found"
        fi

        if [[ $ssh_count -gt 0 ]]; then
            echo -e "${YELLOW}[DRY RUN]${NC} Would delete ~$ssh_count SSH password entries"
            KEYCHAIN_DELETED=$((KEYCHAIN_DELETED + ssh_count))
        else
            echo -e "${BLUE}○${NC} No SSH password entries found"
        fi
    fi
fi

echo ""

# Summary
echo -e "${BLUE}=== Summary ===${NC}"
echo -e "${GREEN}Deleted:${NC} $DELETED_COUNT items"
echo -e "${BLUE}Not found:${NC} $NOT_FOUND_COUNT items (already deleted)"
if [[ "$KEEP_KEYCHAIN" == false ]]; then
    echo -e "${GREEN}Keychain entries deleted:${NC} $KEYCHAIN_DELETED"
    if [[ $KEYCHAIN_FAILED -gt 0 ]]; then
        echo -e "${RED}Keychain entries failed:${NC} $KEYCHAIN_FAILED"
    fi
fi
if [[ $FAILED_COUNT -gt 0 ]]; then
    echo -e "${RED}Failed:${NC} $FAILED_COUNT items"
fi
echo ""

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}This was a dry run. Run without --dry-run to actually delete.${NC}"
    exit 0
fi

if [[ $FAILED_COUNT -gt 0 ]]; then
    echo -e "${YELLOW}Uninstall completed with some errors${NC}"
    exit 1
else
    echo -e "${GREEN}Sequel Ace has been completely uninstalled!${NC}"
    exit 0
fi
