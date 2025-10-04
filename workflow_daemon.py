import os
import time
import subprocess
import logging
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone
from version_control import VersionControl

# --- Configuration ---
PRODUCTION_PATH = Path("C:/Users/mert/Desktop/api/uretim")
PROJECT_OUTPUT_PATH = Path("./output")
SLEEP_INTERVAL_SECONDS = 30
GIT_BRANCH = "main"
CONFIG_FILE = "project_core/finalv1.json"

# --- Logger Setup (Console Only) ---
def setup_logging():
    """Configures the logger to write to the console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )

def load_config(file_path):
    """Loads the main JSON configuration file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"CRITICAL: Could not load or parse config file {file_path}: {e}")
        return None

# --- Git and Shell Operations ---
def run_command(command):
    """Executes a shell command and returns its output, handling errors."""
    try:
        logging.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command, check=True, capture_output=True, text=True, encoding='utf-8'
        )
        logging.info(f"Command successful. Output:\n{result.stdout.strip()}")
        return result.stdout.strip(), None
    except FileNotFoundError as e:
        error_msg = f"Error: Command not found - {e.filename}. Is Git installed and in your PATH?"
        logging.error(error_msg)
        return None, error_msg
    except subprocess.CalledProcessError as e:
        error_msg = (
            f"Command failed with exit code {e.returncode}.\n"
            f"Stderr: {e.stderr.strip()}\n"
            f"Stdout: {e.stdout.strip()}"
        )
        logging.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred while running command: {e}"
        logging.error(error_msg)
        return None, error_msg

# --- Core Functions ---
def check_for_updates(status_log):
    """
    Checks for remote updates, pulls if behind, and halts if diverged.
    """
    logging.info("--- Checking for repository updates ---")
    status_log.append({"event": "update_check_started", "timestamp": datetime.now(timezone.utc).isoformat()})

    # 1. Fetch the latest info from the remote
    run_command(["git", "fetch", "origin"])

    # 2. Check the status
    status_output, error = run_command(["git", "status", "-uno"])
    if error:
        status_log.append({"event": "git_status_failed", "error": error, "timestamp": datetime.now(timezone.utc).isoformat()})
        return

    # 3. Handle different Git states
    if "Your branch is up to date" in status_output:
        logging.info("Project is up-to-date.")
        status_log.append({"event": "repo_up_to_date", "timestamp": datetime.now(timezone.utc).isoformat()})

    elif "Your branch is behind" in status_output:
        logging.info("Local branch is behind. Pulling changes...")
        pull_output, pull_error = run_command(["git", "pull", "origin", "main"])
        if pull_error:
            logging.error(f"Failed to pull changes: {pull_error}")
            status_log.append({"event": "git_pull_failed", "error": pull_error, "timestamp": datetime.now(timezone.utc).isoformat()})
        else:
            logging.info("Project updated successfully.")
            status_log.append({"event": "git_pull_success", "timestamp": datetime.now(timezone.utc).isoformat()})

    elif "have diverged" in status_output:
        logging.critical("CRITICAL - Branch has diverged! Manual intervention required. Stopping update cycle.")
        status_log.append({"event": "branch_diverged", "error": "Branch has diverged", "timestamp": datetime.now(timezone.utc).isoformat()})
        # Stop further processing by returning immediately
        return

    else:
        logging.warning(f"Unknown git status. Full output:\n{status_output}")
        status_log.append({"event": "unknown_git_status", "details": status_output, "timestamp": datetime.now(timezone.utc).isoformat()})

def check_for_production_output(status_log):
    """Checks for completed production outputs and pushes them to the repository."""
    logging.info("--- Checking for new production outputs ---")
    status_log.append({"event": "production_check_started", "timestamp": datetime.now(timezone.utc).isoformat()})

    if not PRODUCTION_PATH.exists() or not PRODUCTION_PATH.is_dir():
        msg = f"Production path '{PRODUCTION_PATH}' does not exist. Skipping."
        logging.warning(msg)
        status_log.append({"event": "production_path_not_found", "message": msg, "timestamp": datetime.now(timezone.utc).isoformat()})
        return

    try:
        subfolders = [d for d in PRODUCTION_PATH.iterdir() if d.is_dir()]
        unprocessed_folders = [f for f in subfolders if not (f / "_PROCESSED").exists()]
    except OSError as e:
        msg = f"Could not read directories in '{PRODUCTION_PATH}': {e}"
        logging.error(msg)
        status_log.append({"event": "directory_read_error", "error": msg, "timestamp": datetime.now(timezone.utc).isoformat()})
        return

    if not unprocessed_folders:
        logging.info("No new unprocessed production folders found.")
        return

    target_folder = max(unprocessed_folders, key=lambda f: f.stat().st_mtime)
    logging.info(f"Found candidate folder: {target_folder.name}")

    if (target_folder / "_SUCCESS").exists():
        process_successful_job(target_folder, status_log)
    else:
        logging.info(f"No _SUCCESS file in '{target_folder.name}'. It's not ready yet.")

def process_successful_job(target_folder, status_log):
    """Handles the processing of a validated, successful job folder."""
    sku = target_folder.name
    event = {"event": "job_processing_started", "sku": sku, "timestamp": datetime.now(timezone.utc).isoformat()}
    logging.info(f"Found _SUCCESS file in '{sku}'. Starting push process.")

    try:
        destination = PROJECT_OUTPUT_PATH / sku
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(target_folder, destination)
        logging.info(f"Successfully copied files from '{target_folder}' to '{destination}'")
    except Exception as e:
        event["error"] = f"Failed to copy files for SKU {sku}: {e}"
        logging.error(event["error"])
        status_log.append(event)
        return

    _, error = run_command(["git", "add", "."])
    if error:
        event["error"] = f"Failed to stage files: {error}"
        status_log.append(event)
        return

    commit_message = f"chore(publish): Add production output for SKU {sku}"
    _, error = run_command(["git", "commit", "-m", commit_message])
    if error:
        status_output, _ = run_command(["git", "status", "-s"])
        if not status_output: # No changes to commit
            logging.warning("Commit failed, but no changes to commit. Proceeding.")
        else:
            event["error"] = f"Failed to commit changes: {error}"
            status_log.append(event)
            return

    _, error = run_command(["git", "push"])
    if error:
        event["error"] = f"Failed to push changes: {error}"
        status_log.append(event)
        return

    try:
        (target_folder / "_SUCCESS").rename(target_folder / "_PROCESSED")
        msg = f"Successfully marked folder '{sku}' as processed."
        logging.info(msg)
        event["status"] = "success"
        event["message"] = msg
    except OSError as e:
        event["error"] = f"CRITICAL: Failed to rename _SUCCESS to _PROCESSED for SKU {sku}: {e}"
        logging.error(event["error"])

    status_log.append(event)

# --- Main Execution Loop ---
def main():
    """The main daemon loop."""
    setup_logging()
    config = load_config(CONFIG_FILE)
    if not config or "fs" not in config or "ver" not in config["fs"]:
        logging.critical("Daemon cannot start without 'fs.ver' configuration.")
        return

    vc = VersionControl(config["fs"]["ver"])
    logging.info("--- Workflow Daemon Started ---")

    try:
        while True:
            status_snapshot = {
                "run_id": f"daemon_run_{datetime.now(timezone.utc).isoformat()}",
                "status": "starting_cycle",
                "events": []
            }

            check_for_updates(status_snapshot["events"])
            check_for_production_output(status_snapshot["events"])

            status_snapshot["status"] = "cycle_complete"
            vc.save_with_metadata(
                base_path='logs/daemon_status.json',
                data=status_snapshot,
                actor='workflow_daemon.py',
                reason='Periodic daemon status and event snapshot.'
            )

            logging.info(f"--- Cycle complete. Waiting for {SLEEP_INTERVAL_SECONDS} seconds. ---")
            time.sleep(SLEEP_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logging.info("--- Daemon stopped by user (Ctrl+C). ---")
    except Exception as e:
        logging.critical(f"An unhandled exception occurred in the main loop: {e}", exc_info=True)
        # Optionally save a final crash report
        vc.save_with_metadata(
            base_path='logs/daemon_crash.json',
            data={"error": str(e), "traceback": logging.traceback.format_exc()},
            actor='workflow_daemon.py',
            reason='Unhandled exception in main loop.'
        )

if __name__ == "__main__":
    main()