import tkinter as tk

from configupdater import ConfigUpdater

from BackupScripts.BackupThread import BackupThread
from BackupScripts.Utils import *
from BackupScripts.WindowIcon import WindowsIcon
from Gui.ProfileWindow import ProfileWindow
from Gui.Tk_AutoBackupGUI import AutomaticBackupGui

# The Default Config for the Controller class if 'config.ini' file does not existing.
DEFAULT_CONFIG = """
[LOCAL]
# Version #:
version = 1.0
# Shows notifications: ['True', 'False']
do_notifications = True
# Shows notification levels DEFAULT='all': ['all', 'error/alert', 'error']
notify_level = all
# Not used at the moment. DEFAULT=4
max_threads = 4
# Shows the GUI interface at start: ['True', 'False']
silent_start = False
# If true, logs everything to the 'log.csv' file: ['True', 'False']
debug = False
# Minimum copies set for backup rotate DEFAULT=1: integer
min_copies = 1
# Maximum copies set for backup rotate DEFAULT=8: integer
max_copies = 8
# Minimum interval (seconds) set for backup rotate DEFAULT=20: integer
min_interval = 20
# Maximum interval (seconds) set for backup rotate DEFAULT=10000: integer
max_interval = 10000
# Minimum warning time (seconds) the program will notify you prior to a backup commencing DEFAULT=10: integer
min_warning_time = 10
[AUTOSTART]
# Starts a backup for a specified profile: ['True', 'False']
enabled = False
# The profile name created in the 'profiles.json' file to be backed up when auto start is 'True': string
profile = """""


class Controller:
    """
    Controller class that connects BackupThread, WindowsIcon, AutomaticBackupGui and ProfileWindow all together.
    It also controls the auto-start feature of the program so Task Scheduler can be used to start 'Daily Backups'.
    All parameters can be configured within the 'config.ini' file and some through the GUI.
    This way the GUI class may be swapped out with other GUI frameworks like PyQT with minimal changes to this class.

    If you want to use another GUI framework, AutomaticBackupGui and ProfileWindow will have to be rewritten or not used
    at all.

    BackupThread, WindowsIcon and parts of the Controller class is really all that's needed to start and create backups.
    If no GUI is wanted, modifying the 5 lines of code specified with a comment above them is required.

    All Profile configs are saved in the 'profiles.json' file and can be written into there and reloaded into the
    WindowsIcon class.

    Profile data setup is as specified:
    {
    "Profile-Name-To-Be-Set": {
        "Folders": [
            "Folder-0-path-to-be-backed-up",
            "Folder-1-path-to-be-backed-up",
            ...
        ],
        "Destination": "Path-to-Destination",
        "Interval": 20,
        "Copies": 2,
        "Method": "Rotate",
        "WarningTime": 10,
        "Compression": true
            }
    }
    """
    _version = 1.0

    def __init__(self, root=None):
        self.recent_backup = ""
        self.thread_running = False
        self.notifications = False
        self.notify_level = "all"
        self.max_threads = 4
        self.silent_start = False
        self.auto_start = False
        self.debug = False
        self.min_copies = 1
        self.max_copies = 8
        self.min_interval = 20
        self.max_interval = 10000
        self.min_warning_time = 10
        self.auto_start_profile = ""

        self.config = ConfigUpdater()
        try:
            self.config.read(CONFIG_FILE)
        except FileNotFoundError:
            self.config.read_string(DEFAULT_CONFIG)
            with open(CONFIG_FILE, 'w') as configfile:
                self.config.write(configfile)

        self.setup()

        self.root = root
        self.windows_icon = WindowsIcon(self, self.notifications, self.notify_level)
        self.thread = BackupThread(self, self.windows_icon)

        # ******* Comment this line and set 'gui' to None if no GUI is wanted. *******
        self.gui = AutomaticBackupGui(self.root, self, self.windows_icon, self.silent_start)
        # self.gui = None

        # ******* Comment these lines and set 'profile_window' to None if no GUI is wanted. *******
        self.profile_window = ProfileWindow(self.root, self)
        self.profile_window.hide()
        # self.profile_window = None
        # ******* Comment this line if no GUI is wanted. *******
        self.gui.show_gui()

        if self.auto_start:
            self.thread.backup_event.wait(1)
            self.windows_icon.notify_user("ALERT:",
                                          f"Autostart has been activated for profile: {self.auto_start_profile}",
                                          override=True)
            self.thread.backup_event.wait(2)
            profiles = self.load_saved_profiles(initial_start=True)
            config = profiles[self.auto_start_profile]
            self.start_backup(config, self.auto_start_profile)

    def setup(self):
        try:
            self.notifications = eval(self.config["LOCAL"].get("do_notifications").value)
            self.notify_level = self.config["LOCAL"].get("notify_level").value
            self.max_threads = int(self.config["LOCAL"].get("max_threads").value)
            self.silent_start = eval(self.config["LOCAL"].get("silent_start").value)
            self.debug = eval(self.config["LOCAL"].get("debug").value)
            self.min_copies = int(self.config["LOCAL"].get("min_copies").value)
            self.max_copies = int(self.config["LOCAL"].get("max_copies").value)
            self.min_interval = int(self.config["LOCAL"].get("min_interval").value)
            self.max_interval = int(self.config["LOCAL"].get("max_interval").value)
            self.min_warning_time = int(self.config["LOCAL"].get("min_warning_time").value)

            self.auto_start = eval(self.config["AUTOSTART"].get("enabled").value)
            self.auto_start_profile = self.config["AUTOSTART"].get("profile").value
        except Exception as e:
            log(f"ERROR: {e}")
            sys.exit(f"Config could not be loaded: {e}")

    def update_gui_config(self, terminate=False):
        self.config["AUTOSTART"]["enabled"].value = str(self.auto_start)
        self.config["AUTOSTART"]["profile"].value = self.auto_start_profile
        self.config["LOCAL"]["do_notifications"].value = str(self.notifications)
        self.config["LOCAL"]["silent_start"].value = str(self.silent_start)
        try:
            self.config.update_file(validate=True)
            if not terminate:
                self.windows_icon.notify_user("INFO:", "Config has been updated.")
        except Exception as e:
            log(f"ERROR: {e}")
            self.windows_icon.notify_user("ERROR:", "Config could not be updated.")

    def enable_autostart(self, profile_name):
        self.auto_start = True
        self.auto_start_profile = profile_name
        self.update_gui_config()

    def disable_autostart(self):
        self.auto_start = False
        self.auto_start_profile = ""
        self.update_gui_config()

    def toggle_silent_start(self, state):
        self.silent_start = state

    def toggle_notifications(self, state):
        self.notifications = state

    def start_backup(self, config, profile_name):
        self.thread.start(config, profile_name)

    def stop_backup(self):
        self.thread.stop_backup()

    def create_profile_window(self, config=None, profile_name=None):
        # If profile_window is not created with any GUI framework. Open 'profiles.json' file instead.
        if self.profile_window is None:
            open_config()
            return
        if config is not None and profile_name is not None:
            self.profile_window.edit_profile(config, profile_name)
            self.profile_window.show()
            return
        self.profile_window.show(clear=True)

    def get_time_left(self):
        return self.thread.get_time_left()

    def verify_profiles(self, profile_data):
        """Verifies all profile parameters according to spec."""
        if not profile_data:
            return False
        try:
            num_copies = int(profile_data["Copies"])
            profile_data["Copies"] = num_copies
            if num_copies < self.min_copies:
                profile_data["Copies"] = self.min_copies
            if num_copies > self.max_copies:
                profile_data["Copies"] = self.max_copies
        except ValueError:
            profile_data["Copies"] = self.min_copies

        try:
            interval = int(profile_data["Interval"])
            profile_data["Interval"] = interval
            if interval < self.min_interval:
                profile_data["Interval"] = self.min_interval
            elif interval >= self.max_interval:
                profile_data["Interval"] = self.max_interval
        except ValueError:
            profile_data["Interval"] = self.min_interval

        try:
            warning_time = int(profile_data["WarningTime"])
            profile_data["WarningTime"] = warning_time
            if profile_data["WarningTime"] >= profile_data["Interval"]:
                profile_data["WarningTime"] = self.min_warning_time
        except ValueError:
            profile_data["WarningTime"] = self.min_warning_time

        if profile_data["Method"] not in self.thread.get_backup_methods():
            self.windows_icon.notify_user("ERROR:", "Backup Method does not exist.")
            return False

        if not profile_data["Destination"]:
            self.windows_icon.notify_user("ERROR:", "Destination folder is not set.")
            return False

        if not profile_data["Folders"]:
            self.windows_icon.notify_user("ERROR:", "No folders are set to backup.")
            return False

        try:
            for i in profile_data["Folders"]:
                if not os.path.exists(i):
                    self.windows_icon.notify_user("ERROR:",
                                                  "Folder paths do not exist, recommend deleting them from the config.")
                    return False
        except IndexError:
            self.windows_icon.notify_user("ERROR:", "Source folder(s) is not set.")
            return False

        if not os.path.exists(profile_data["Destination"]):
            self.windows_icon.notify_user("ERROR:",
                                          "Destination path do not exist, recommend deleting them from the config.")
            return False

        if check_folders(profile_data["Folders"], profile_data["Destination"]):
            self.windows_icon.notify_user("ERROR:", "Destination Path cannot be in folder as Source.")
            return False

        if len(profile_data["Folders"]) != len(set(profile_data["Folders"])):
            self.windows_icon.notify_user("ERROR:",
                                          "Duplicate folder paths have been set. Please modify profile accordingly.")
            return False

        return True

    def update_profiles(self, profiles):
        dump_json(PROFILE_PATH, profiles)
        self.windows_icon.notify_user("INFO:", "Profile has been saved.")
        self.load_saved_profiles()

    def save_profile(self, config, profile_name):
        if not profile_name:
            self.windows_icon.notify_user("ERROR:", "No Profile Name set.")
            return
        if self.verify_profiles(config):
            try:
                new_profile = {profile_name: config}
                if os.path.exists(PROFILE_PATH):
                    old_profiles = read_config(PROFILE_PATH)
                    new_profile = update_json(new_profile, old_profiles)
                else:
                    new_profile = new_profile
                dump_json(PROFILE_PATH, new_profile)
                self.windows_icon.notify_user("INFO:", "Profile has been saved.")
                self.gui.load_saved_profiles()
            except Exception as e:
                self.windows_icon.notify_user("ERROR:", f"Profile could not be saved.")
                self.windows_icon.notify_user("ERROR:", f"Unexpected error: {e}")

    def load_saved_profiles(self, initial_start=False):
        return self.windows_icon.load_saved_profiles(initial_start)

    def terminate(self):
        self.thread.stop_backup(no_message=True)
        self.windows_icon.icon.stop()
        if self.gui is not None:
            self.update_gui_config(terminate=True)
        # Not sure what's going on, but main thread doesn't close when root.destroy() is called. So this,
        # is forcing everything to close after everything is saved.
        os._exit(0)

    def restart_gui(self):
        if self.gui is None:
            self.windows_icon.notify_user("ALERT:", "No GUI Framework exists.")
            return
        self.gui.show_gui()


if __name__ == '__main__':
    # ******* Comment this line and set 'tk_root' to None if no GUI is wanted. *******
    tk_root = tk.Tk()
    # tk_root = None
    c = Controller(tk_root)
    # ******* Comment this line if no GUI is wanted. *******
    tk_root.mainloop()
