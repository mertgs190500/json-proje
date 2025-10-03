import os
import time
import subprocess
import logging
import shutil
from pathlib import Path

# --- Configuration ---
# Using Path for cross-platform compatibility, though the user path is Windows-specific.
# IMPORTANT: This path is hardcoded as per the request.
# For better portability, this should be an environment variable or a config file setting.
PRODUCTION_PATH = Path("C:/Users/mert/Desktop/api/uretim")
PROJECT_OUTPUT_PATH = Path("./output")
LOG_FILE = "daemon.log"
SLEEP_INTERVAL_SECONDS = 30
GIT_BRANCH = "main"

# --- Logger Setup ---
def setup_logging():
    """Configures the logger to write to a file and the console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

# --- Git and Shell Operations ---
def run_command(command):
    """Executes a shell command and returns its output, handling errors."""
    try:
        logging.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        logging.info(f"Command successful. Output:\n{result.stdout.strip()}")
        return result.stdout.strip()
    except FileNotFoundError as e:
        logging.error(f"Error: Command not found - {e.filename}. Is Git installed and in your PATH?")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with exit code {e.returncode}.")
        logging.error(f"Stderr: {e.stderr.strip()}")
        logging.error(f"Stdout: {e.stdout.strip()}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while running command: {e}")
        return None

# --- Core Functions ---

def check_for_updates():
    """Checks for remote updates and pulls them if the local branch is behind."""
    logging.info("--- Checking for repository updates ---")

    # 1. Fetch latest info from origin
    if run_command(["git", "fetch", "origin"]) is None:
        logging.error("Failed to fetch from origin. Skipping update check.")
        return

    # 2. Check status
    status_output = run_command(["git", "status", "-uno"])
    if status_output is None:
        logging.error("Failed to get git status. Skipping update check.")
        return

    if f"Your branch is behind 'origin/{GIT_BRANCH}'" in status_output:
        logging.info("Local branch is behind. Pulling changes...")
        # 3. Pull changes
        pull_output = run_command(["git", "pull", "origin", GIT_BRANCH])
        if pull_output is not None:
            logging.info("Project updated successfully.")
        else:
            logging.error("Failed to pull updates from origin.")
    else:
        logging.info("Project is up-to-date.")

def check_for_production_output():
    """Checks for completed production outputs and pushes them to the repository."""
    logging.info("--- Checking for new production outputs ---")

    if not PRODUCTION_PATH.exists() or not PRODUCTION_PATH.is_dir():
        logging.warning(f"Production path '{PRODUCTION_PATH}' does not exist. Skipping.")
        return

    # 1. List all subdirectories
    try:
        subfolders = [d for d in PRODUCTION_PATH.iterdir() if d.is_dir()]
    except OSError as e:
        logging.error(f"Could not read directories in '{PRODUCTION_PATH}': {e}")
        return

    # 2. Filter out folders that already have a _PROCESSED file
    unprocessed_folders = []
    for folder in subfolders:
        if not (folder / "_PROCESSED").exists():
            unprocessed_folders.append(folder)

    if not unprocessed_folders:
        logging.info("No new unprocessed production folders found.")
        return

    # 3. Find the most recently modified folder among the unprocessed ones
    try:
        target_folder = max(unprocessed_folders, key=lambda f: f.stat().st_mtime)
    except ValueError:
        # This can happen if unprocessed_folders is empty, but we already checked.
        # It's good practice to keep it safe.
        return

    logging.info(f"Found candidate folder: {target_folder.name}")

    # 4. Check if the target folder has a _SUCCESS file
    success_file = target_folder / "_SUCCESS"
    if success_file.exists():
        logging.info(f"Found _SUCCESS file in '{target_folder.name}'. Starting push process.")

        # a. Get SKU from folder name
        sku = target_folder.name

        # b. Copy all files to the project's output/ directory
        try:
            if not PROJECT_OUTPUT_PATH.exists():
                PROJECT_OUTPUT_PATH.mkdir(parents=True)

            # Using shutil.copytree for robustness
            # It requires the destination to not exist, so we copy to a subfolder
            destination = PROJECT_OUTPUT_PATH / sku
            if destination.exists():
                shutil.rmtree(destination) # Clear old content if any
            shutil.copytree(target_folder, destination)
            logging.info(f"Successfully copied files from '{target_folder}' to '{destination}'")
        except Exception as e:
            logging.error(f"Failed to copy files for SKU {sku}: {e}")
            return # Stop processing this folder if copy fails

        # c. Git add
        if run_command(["git", "add", "."]) is None:
            logging.error("Failed to stage new files with 'git add'.")
            # We might want to clean up the copied files here, but for now, we'll just log and stop.
            return

        # d. Git commit
        commit_message = f"chore(publish): Add production output for SKU {sku}"
        if run_command(["git", "commit", "-m", commit_message]) is None:
            logging.error("Failed to commit changes.")
            # If commit fails (e.g., nothing to commit), we should still rename the file.
            # Let's check the status again.
            status_output = run_command(["git", "status", "-s"]) # short format
            if not status_output:
                logging.warning("Commit failed, but there are no changes to commit. Proceeding to mark as processed.")
            else:
                return # Real commit error, stop.

        # e. Git push
        if run_command(["git", "push"]) is None:
            logging.error("Failed to push changes to remote repository.")
            # If push fails, we should NOT rename the file, so it can be retried.
            return

        # f. Rename _SUCCESS to _PROCESSED
        try:
            processed_file = target_folder / "_PROCESSED"
            success_file.rename(processed_file)
            logging.info(f"Successfully marked folder '{sku}' as processed by renaming _SUCCESS to _PROCESSED.")
        except OSError as e:
            logging.error(f"CRITICAL: Failed to rename _SUCCESS to _PROCESSED for SKU {sku}: {e}")
            logging.error("This may cause the same folder to be processed again. Manual intervention required.")
    else:
        logging.info(f"No _SUCCESS file in '{target_folder.name}'. It's not ready yet.")


# --- Main Execution Loop ---
def main():
    """The main daemon loop."""
    setup_logging()
    logging.info("--- Workflow Daemon Started ---")
    try:
        while True:
            check_for_updates()
            check_for_production_output()
            logging.info(f"--- Cycle complete. Waiting for {SLEEP_INTERVAL_SECONDS} seconds. ---")
            time.sleep(SLEEP_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logging.info("--- Daemon stopped by user (Ctrl+C). ---")
    except Exception as e:
        logging.critical(f"An unhandled exception occurred in the main loop: {e}", exc_info=True)

if __name__ == "__main__":
    main()