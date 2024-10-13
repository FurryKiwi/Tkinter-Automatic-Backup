import os.path
import shutil
import threading
import time

from .Utils import *


# TODO: Add multi-threading.
#  Create a separate program to be ran with only icon, maybe a gui for setting up folders?
#  Add Zip compression for backups
class BackupThread:
    """Backup Thread class that's responsible for handling the backups of folders/files."""
    # These are the backup methods available to be called for backing up folders/files.
    _backup_methods = ["Rotate", "Daily"]

    def __init__(self, controller, icon):
        self.controller = controller
        self.backup_event = threading.Event()

        self.config_data = {}
        self.method = ""
        self.windows_icon = icon
        self.warning_time = self.controller.min_warning_time

        self.backup_process = None
        self.threads = []
        self.cur_profile = ""
        self.log_dest_folders = []
        self.compression = False
        self.exit_on_complete = False

        self.last_update_time = 0

    def start(self, config, profile_name):
        """Start method for starting a thread of a backup sequence."""
        # Check if there is a backup already active.
        if self.backup_process and self.backup_process.is_alive():
            self.windows_icon.notify_user("ERROR:", "Cannot start backup. There is an active process.")
            return
        self.cur_profile = profile_name
        self.config_data = config

        # Verify the profile config is correct prior to starting backup sequence.
        if self.controller.verify_profiles(self.config_data):
            self.method = self.config_data["Method"]
            self.warning_time = self.config_data["WarningTime"]
            self.compression = self.config_data["Compression"]
            self.windows_icon.config_data = self.config_data
            # Add here for new methods of backups.
            if self.method == "Rotate":
                self.backup_process = threading.Thread(target=self.rotate_backup, daemon=True)
            elif self.method == "Daily":
                self.exit_on_complete = True
                self.backup_process = threading.Thread(target=self.daily_backup, daemon=True)
            self.backup_process.start()
            self.controller.thread_running = True

    def get_backup_methods(self):
        """Returns a list of all the backup_methods supported. (Specified at beginning of class)"""
        return self._backup_methods

    def get_time_left(self):
        """Returns the amount of time left before the next backup used in the rotate_backup method."""
        time_passed = int(time.time() - self.last_update_time)
        return self.config_data["Interval"] - time_passed

    def get_last_folder_digit(self, folder_path):
        """Gets the last digit on the oldest folder found in the destination path, Deletes the oldest folder if the
        number of copies is greater than the set number of copies.
        :returns: int: last_folder_digit """
        copies_made = find_copies(self.config_data["Destination"], folder_path)
        if copies_made == 0:
            last_folder_digit = 0
        else:
            oldest_folder = find_oldest_folder(self.config_data["Destination"], folder_path)
            tmp_oldest_folder = os.path.splitext(oldest_folder)
            last_folder_digit = int(tmp_oldest_folder[0][len(tmp_oldest_folder[0]) - 1:])
            if copies_made <= self.config_data["Copies"]:
                last_folder_digit = copies_made

        if copies_made == self.config_data["Copies"]:
            oldest_folder = find_oldest_folder(self.config_data["Destination"], folder_path)
            tmp_oldest_folder = os.path.splitext(oldest_folder)
            last_folder_digit = int(tmp_oldest_folder[0][len(tmp_oldest_folder[0]) - 1:])
            if tmp_oldest_folder[1] == ".zip":
                os.remove(oldest_folder)
            else:
                shutil.rmtree(oldest_folder)
        return last_folder_digit

    def rotate_backup(self):
        """
        Creates amount of backups specified by profile and will keep that number of backups in destination location.
        Cycles through the backups replacing the oldest folder/file.
        :return:
        """
        try:
            recent_string = ""
            while not self.backup_event.is_set():
                self.last_update_time = int(time.time())
                self.log_dest_folders = []
                full_destination_folder = ""
                # loop through all folders in list
                for folder_to_backup in self.config_data["Folders"]:
                    if self.compression:
                        self.log_dest_folders.append(folder_to_backup)
                        if len(self.log_dest_folders) == len(self.config_data["Folders"]):
                            last_folder_digit = self.get_last_folder_digit(self.cur_profile)
                            dest_folder_zip = os.path.join(self.config_data["Destination"], self.cur_profile)
                            destination_folder = f"{dest_folder_zip}_{last_folder_digit}"
                            full_destination_folder = os.path.join(self.config_data["Destination"], destination_folder)
                            compress_folder(full_destination_folder, self.log_dest_folders)
                    else:
                        last_folder_digit = self.get_last_folder_digit(folder_to_backup)
                        destination_folder = f"{os.path.basename(folder_to_backup)}_{last_folder_digit}"
                        full_destination_folder = os.path.join(self.config_data["Destination"], destination_folder)
                        self.log_dest_folders.append(full_destination_folder)
                        shutil.copytree(folder_to_backup, full_destination_folder, dirs_exist_ok=True)

                    if len(self.log_dest_folders) == 1:
                        recent_string = f"Recent Backup created for profile: {self.cur_profile}\n"
                        if full_destination_folder:
                            recent_string += f"Folder: {full_destination_folder}\n"
                    else:
                        recent_string += f"Folder: {full_destination_folder}\n"
                    self.controller.recent_backup = recent_string
                if self.config_data["Interval"] > 0:
                    self.windows_icon.notify_user("ALERT:", f"Backup: {full_destination_folder}")

                    self.backup_event.wait(self.config_data["Interval"] - self.warning_time)
                    if not self.backup_event.is_set():
                        self.windows_icon.notify_user("ALERT:",
                                                      f"A backup is about to begin in {self.warning_time} seconds.")
                    self.backup_event.wait(self.warning_time)

        except Exception as e:
            self.windows_icon.notify_user("ERROR:", f"Unexpected error: {e}")
            log(f"ERROR: {e}")
        finally:
            self.backup_event.clear()

    def daily_backup(self):
        """
        Creates a backup once. This method is to be used with the task scheduler in windows and the 'auto-start'
        feature within the program.
        :return:
        """
        try:
            recent_string = ""
            while not self.backup_event.is_set():
                self.last_update_time = int(time.time())
                self.log_dest_folders = []
                full_destination_folder = ""
                # loop through all folders in list
                for folder_to_backup in self.config_data["Folders"]:
                    if self.compression:
                        self.log_dest_folders.append(folder_to_backup)
                        if len(self.log_dest_folders) == len(self.config_data["Folders"]):
                            last_folder_digit = self.get_last_folder_digit(self.cur_profile)
                            dest_folder_zip = os.path.join(self.config_data["Destination"], self.cur_profile)
                            destination_folder = f"{dest_folder_zip}_{last_folder_digit}"
                            full_destination_folder = os.path.join(self.config_data["Destination"], destination_folder)
                            compress_folder(full_destination_folder, self.log_dest_folders)
                    else:
                        last_folder_digit = self.get_last_folder_digit(folder_to_backup)
                        destination_folder = f"{os.path.basename(folder_to_backup)}_{last_folder_digit}"
                        full_destination_folder = os.path.join(self.config_data["Destination"], destination_folder)
                        self.log_dest_folders.append(full_destination_folder)
                        shutil.copytree(folder_to_backup, full_destination_folder, dirs_exist_ok=True)

                    if len(self.log_dest_folders) == 1:
                        recent_string = f"Recent Backup created for profile: {self.cur_profile}\n"
                        if full_destination_folder:
                            recent_string += f"Folder: {full_destination_folder}\n"
                    else:
                        recent_string += f"Folder: {full_destination_folder}\n"
                    self.controller.recent_backup = recent_string
                self.windows_icon.notify_user("ALERT:", f"Backup: {full_destination_folder}")
                self.backup_event.wait(2)
                self.stop_backup()
                if self.exit_on_complete:
                    self.controller.terminate()

        except Exception as e:
            self.windows_icon.notify_user("ERROR:", f"Unexpected error: {e}")
            log(f"ERROR: {e}")
        finally:
            self.backup_event.clear()

    def stop_backup(self, no_message=False):
        if self.backup_process and self.backup_process.is_alive():
            # Don't think this could happen, but I put it in just in case.
            if len(self.log_dest_folders) != len(self.config_data["Folders"]):
                self.windows_icon.notify_user("ERROR:", "Process terminated before all folders could be backed up.")
            try:
                log(self.controller.recent_backup)
            except Exception as e:
                # This happens when the csv file is opened in Microsoft Excel, not notepad or notepad++
                self.windows_icon.notify_user("ERROR:", f"Can not write to log file. {e}", override=True)
            self.windows_icon.notify_user("ALERT:", "Process terminated.")
            self.windows_icon.icon.remove_notification()
            self.backup_event.set()
            self.controller.thread_running = False
        else:
            if not no_message:
                self.windows_icon.notify_user("ALERT:", "No active process to terminate")
