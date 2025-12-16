#!/usr/bin/env python3
"""
Single-command sync system for cross-platform repo synchronization.
Canonical implementation - all sync logic lives here.
"""

import subprocess
import sys
import os
import time
import socket
import datetime
import signal
from pathlib import Path

# Exit codes
EXIT_SUCCESS = 0
EXIT_DIRTY_FOLLOWER = 2
EXIT_DIVERGENCE = 3
EXIT_PUSH_REJECTED = 4
EXIT_CONFLICT = 5

# Global flag for Ctrl+C handling
interrupted = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global interrupted
    interrupted = True
    print("\n[STOP] Interrupted by user. Exiting cleanly.")
    sys.exit(EXIT_SUCCESS)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def run(cmd, capture=True, check=False):
    """Run a git command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture,
            text=True,
            check=check
        )
        return (result.returncode == 0, result.stdout.strip(), result.stderr.strip())
    except Exception as e:
        return (False, "", str(e))


def get_hostname():
    """Get sanitized hostname."""
    hostname = socket.gethostname().lower()
    # Remove invalid chars for branch names
    hostname = ''.join(c if c.isalnum() or c == '-' else '-' for c in hostname)
    return hostname


def get_timestamp():
    """Get timestamp in YYYYMMDD-HHMMSS format."""
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def detect_role(args):
    """Detect role from CLI args, env var, or .sync-role file."""
    # CLI override
    if args.writer:
        return "WRITER"
    if args.follower:
        return "FOLLOWER"
    
    # Env override
    env_role = os.environ.get("SYNC_ROLE", "").upper()
    if env_role in ("WRITER", "FOLLOWER"):
        return env_role
    
    # File-based
    role_file = Path(".sync-role")
    if role_file.exists():
        try:
            content = role_file.read_text().strip().upper()
            if content in ("WRITER", "FOLLOWER"):
                return content
        except Exception:
            pass
    
    # Default
    return "FOLLOWER"


def get_git_info():
    """Get current git state."""
    info = {}
    
    # Current branch
    success, stdout, _ = run("git branch --show-current", check=False)
    info["branch"] = stdout if success else "unknown"
    
    # HEAD hash
    success, stdout, _ = run("git rev-parse --short HEAD", check=False)
    info["head_short"] = stdout if success else "unknown"
    
    # Upstream
    success, stdout, _ = run("git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null", check=False)
    info["upstream"] = stdout if success else None
    
    # Remote URL
    success, stdout, _ = run("git config --get remote.origin.url", check=False)
    info["remote_url"] = stdout if success else "unknown"
    
    # Dirty check
    success, stdout, _ = run("git status --porcelain", check=False)
    info["dirty"] = bool(stdout)
    info["dirty_files"] = stdout.split('\n') if stdout else []
    
    # Ahead/behind
    if info["upstream"]:
        # Use @{u} syntax - need to escape in shell command
        success, stdout, _ = run('git rev-list --left-right --count HEAD...@{u} 2>/dev/null', check=False)
        if success and stdout:
            parts = stdout.strip().split('\t')
            if len(parts) == 2:
                info["behind"] = int(parts[0])
                info["ahead"] = int(parts[1])
            else:
                info["behind"] = 0
                info["ahead"] = 0
        else:
            info["behind"] = 0
            info["ahead"] = 0
    else:
        info["behind"] = 0
        info["ahead"] = 0
    
    return info


def print_status(info, role):
    """Print current status."""
    print("═══════════════════════════════════════════════════════════")
    print("SYNC STATUS")
    print("═══════════════════════════════════════════════════════════")
    print(f"Branch: {info['branch']}")
    print(f"HEAD: {info['head_short']}")
    if info["upstream"]:
        print(f"Upstream: {info['upstream']}")
    else:
        print("Upstream: not set")
    print(f"Ahead: {info['ahead']} commits")
    print(f"Behind: {info['behind']} commits")
    print(f"Working tree: {'DIRTY' if info['dirty'] else 'CLEAN'}")
    if info['dirty'] and info['dirty_files']:
        print(f"  Modified files: {len(info['dirty_files'])}")
    print(f"Role: {role}")
    print(f"Remote: {info['remote_url']}")
    print("═══════════════════════════════════════════════════════════")
    print()


def create_backup_branch():
    """Create a backup branch at current HEAD."""
    hostname = get_hostname()
    timestamp = get_timestamp()
    backup_name = f"backup/{hostname}-{timestamp}"
    
    success, stdout, stderr = run(f"git branch {backup_name}", check=False)
    if success:
        print(f"✓ Backup branch created: {backup_name}")
        return backup_name
    else:
        print(f"✗ Failed to create backup branch: {stderr}")
        return None


def ensure_upstream(branch):
    """Ensure upstream is set."""
    success, stdout, _ = run(f"git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null", check=False)
    if not success or not stdout:
        print(f"Setting upstream to origin/{branch}...")
        run(f"git branch --set-upstream-to=origin/{branch} {branch}", check=False)
        return True
    return True


def follower_mode(args, info):
    """Follower mode: continuous pull loop."""
    branch = info["branch"]
    
    if info["dirty"]:
        print("STOP: You have local changes; commit/stash or switch to writer.")
        print("NEXT ACTION: Run with --writer flag or set SYNC_ROLE=WRITER")
        return EXIT_DIRTY_FOLLOWER
    
    ensure_upstream(branch)
    
    if args.once:
        print("Follower mode (one iteration)...")
        return follower_iteration(info)
    else:
        print("Follower mode: continuous pull loop (5s interval)")
        print("Press Ctrl+C to stop")
        print()
        
        while not interrupted:
            exit_code = follower_iteration(info)
            if exit_code != EXIT_SUCCESS:
                return exit_code
            time.sleep(5)
            info = get_git_info()  # Refresh info
        
        return EXIT_SUCCESS


def follower_iteration(info):
    """One follower iteration."""
    # Fetch
    run("git fetch --all --prune", check=False)
    
    # Refresh info
    info = get_git_info()
    ensure_upstream(info["branch"])
    
    # Check divergence
    if info["behind"] > 0 and info["ahead"] > 0:
        print("STOP: Divergence detected (both ahead and behind).")
        backup = create_backup_branch()
        print("NEXT ACTION: Switch to writer mode and reconcile:")
        print(f"  1. git checkout {backup}  # to see your local commits")
        print("  2. git checkout main")
        print("  3. git pull --rebase origin/main  # or merge as needed")
        print("  4. Resolve conflicts if any")
        print("  5. git push")
        return EXIT_DIVERGENCE
    
    # Pull if behind
    if info["behind"] > 0:
        success, stdout, stderr = run("git pull --ff-only", check=False)
        if success:
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{time_str}] ✓ Synced")
        else:
            print(f"STOP: Fast-forward pull failed: {stderr}")
            backup = create_backup_branch()
            return EXIT_DIVERGENCE
    elif info["ahead"] > 0:
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{time_str}] ✓ Up to date (ahead by {info['ahead']} commits)")
    else:
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{time_str}] ✓ Up to date")
    
    return EXIT_SUCCESS


def writer_mode(args, info):
    """Writer mode: one-shot sync (pull then push)."""
    branch = info["branch"]
    
    if args.dry_run:
        print("DRY RUN: Would perform the following actions:")
        print(f"  1. Ensure upstream is set to origin/{branch}")
        print("  2. git fetch --all --prune")
        if info["behind"] > 0:
            print(f"  3. git pull --rebase (behind by {info['behind']} commits)")
        if info["dirty"]:
            autocommit = os.environ.get("SYNC_AUTOCOMMIT", "0") == "1"
            if autocommit:
                print("  4. git add -u && git commit (auto-commit enabled)")
            else:
                print("  4. STOP: dirty tree (auto-commit disabled)")
        if info["ahead"] > 0:
            print(f"  5. git push (ahead by {info['ahead']} commits)")
        return EXIT_SUCCESS
    
    ensure_upstream(branch)
    
    # Fetch
    print("Fetching latest from origin...")
    run("git fetch --all --prune", check=False)
    info = get_git_info()  # Refresh
    
    # Pull if behind
    if info["behind"] > 0:
        print(f"Local branch is behind by {info['behind']} commits.")
        # Try ff-only first
        success, stdout, stderr = run("git pull --ff-only", check=False)
        if not success:
            print("Fast-forward not possible, trying rebase...")
            success, stdout, stderr = run("git pull --rebase", check=False)
            if not success:
                print("✗ Rebase conflict detected!")
                backup = create_backup_branch()
                print("NEXT ACTION:")
                print("  1. Resolve conflicts: git rebase --continue")
                print("  2. Or abort: git rebase --abort")
                if backup:
                    print(f"  3. To recover: git checkout {backup}")
                return EXIT_CONFLICT
        print("✓ Pulled successfully")
        info = get_git_info()  # Refresh
    
    # Handle dirty tree
    if info["dirty"]:
        autocommit = os.environ.get("SYNC_AUTOCOMMIT", "0") == "1"
        if autocommit:
            print("Auto-committing tracked changes...")
            run("git add -u", check=False)
            commit_msg = os.environ.get("SYNC_MESSAGE", "")
            if not commit_msg:
                hostname = get_hostname()
                timestamp = get_timestamp()
                commit_msg = f"chore(sync): checkpoint {hostname} {timestamp}"
            success, stdout, stderr = run(f'git commit -m "{commit_msg}"', check=False)
            if success:
                print("✓ Committed changes")
                info = get_git_info()  # Refresh
            else:
                print(f"✗ Commit failed: {stderr}")
                return EXIT_CONFLICT
        else:
            print("STOP: Working tree is dirty.")
            print("NEXT ACTION: Commit changes or set SYNC_AUTOCOMMIT=1")
            return EXIT_DIRTY_FOLLOWER
    
    # Push if ahead
    if info["ahead"] > 0:
        print(f"Pushing {info['ahead']} commit(s) to origin/{branch}...")
        success, stdout, stderr = run("git push", check=False)
        if not success:
            print("✗ Push rejected or failed!")
            backup = create_backup_branch()
            print("NEXT ACTION:")
            print("  1. Check remote: git fetch --all --prune")
            print("  2. Pull and rebase: git pull --rebase")
            print("  3. Resolve conflicts if any")
            print("  4. Push again: git push")
            if backup:
                print(f"  5. To recover: git checkout {backup}")
            return EXIT_PUSH_REJECTED
        print("✓ Push successful")
    else:
        print("✓ Already up to date. Nothing to push.")
    
    print()
    print("✓ Writer sync complete")
    return EXIT_SUCCESS


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Single-command sync system for cross-platform repo synchronization"
    )
    parser.add_argument("--writer", action="store_true", help="Force writer mode")
    parser.add_argument("--follower", action="store_true", help="Force follower mode")
    parser.add_argument("--once", action="store_true", help="Follower: run one iteration and exit")
    parser.add_argument("--dry-run", action="store_true", help="Writer: show what would happen without changing anything")
    
    args = parser.parse_args()
    
    # Detect role
    role = detect_role(args)
    
    # Get git info
    info = get_git_info()
    
    # Print status
    print_status(info, role)
    
    # Route to mode
    if role == "WRITER":
        return writer_mode(args, info)
    else:
        return follower_mode(args, info)


if __name__ == "__main__":
    sys.exit(main())

