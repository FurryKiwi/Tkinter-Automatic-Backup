import pystray
from PIL import Image

from BackupScripts.Utils import *


class WindowsIcon:
    """The Windows Task Icon used for starting, creating, stopping, etc. of the BackupThread class."""
    # Icon to be displayed
    _pil_image = Image.open(resource_path("backup.ico"))
    # The log event levels
    _levels = {"all": ["INFO:", "ALERT:", "ERROR:"],
               "error/alert": ["ERROR:", "ALERT:"],
               "error": ["ERROR:"]
               }

    def __init__(self, controller, notification_switch, notify_level):
        self.controller = controller
        self.notification_switch = notification_switch
        self.notify_level = notify_level

        self.config_data = {}
        self.saved_config = {}
        self.icon = None

        self.debug = self.controller.debug

        self.load_saved_profiles(initial_start=True)

        self.setup()

        self.run()

    def setup(self):
        if self.saved_config:
            submenus = self.create_dynamic_menus()
            if not self.icon:
                self.icon = pystray.Icon("Automatic Backup", title="Automatic Backup", icon=self._pil_image)
                self.icon.menu = pystray.Menu(*submenus)
            else:
                self.icon.menu = pystray.Menu(*submenus)
                self.icon.update_menu()
        else:
            if not self.icon:
                self.icon = pystray.Icon("Automatic Backup", title="Automatic Backup", icon=self._pil_image)
                self.icon.menu = self.create_standard_menu()
            else:
                self.icon.menu = self.create_standard_menu()
                self.icon.update_menu()

    def create_standard_menu(self):
        """Creates the standard menu with no 'recent backups' to be quickly started from."""
        return pystray.Menu(pystray.MenuItem("Show Recent", self.show_recent),
                            pystray.MenuItem("Show Alerts", self.toggle_notifications,
                                             checked=lambda i: bool(self.notification_switch)),
                            pystray.MenuItem("Profiles", pystray.Menu(
                                pystray.MenuItem("Open Profiles", open_config),
                                pystray.MenuItem("Create Profile", self.create_profile),
                                pystray.MenuItem("Reload Profiles", lambda: self.load_saved_profiles()))),
                            pystray.MenuItem("Stop Backup", self.stop_backup),
                            pystray.MenuItem("Restart GUI", self.controller.restart_gui),
                            pystray.MenuItem("Exit", self.terminate))

    def create_dynamic_menus(self):
        """Creates the menu with the saved profiles in the menu to be quickly accessed and started."""
        key_names = [i for i in self.saved_config.keys()]
        sub_menus = [pystray.MenuItem("Show Recent", self.show_recent),
                     pystray.MenuItem("Show Alerts", self.toggle_notifications,
                                      checked=lambda i: bool(self.notification_switch)),
                     pystray.MenuItem("Profiles", pystray.Menu(
                         pystray.MenuItem("Open Profiles", open_config),
                         pystray.MenuItem("Create Profile", self.create_profile),
                         pystray.MenuItem("Reload Profiles", lambda: self.load_saved_profiles())
                     ))]
        menus = []
        for i in key_names:
            submenu = pystray.MenuItem(i, self.start_backup)
            menus.append(submenu)
        sub_menus.append(pystray.MenuItem("Load Recent", pystray.Menu(*menus)))
        sub_menus.append(pystray.MenuItem("Stop Backup", self.stop_backup))
        sub_menus.append(pystray.MenuItem("Restart GUI", self.controller.restart_gui))
        sub_menus.append(pystray.MenuItem("Exit", self.terminate))
        return sub_menus

    def load_saved_profiles(self, initial_start=False):
        try:
            self.saved_config = read_config(PROFILE_PATH)
        except FileNotFoundError:
            self.saved_config = {}
        if self.icon and not initial_start:
            self.setup()
            self.notify_user("INFO:", "Reload successful.")
        return self.saved_config

    def run(self):
        self.icon.run_detached()

    def toggle_notifications(self, icon=None):
        if self.notification_switch:
            self.notification_switch = False
        else:
            self.notification_switch = True
        self.controller.toggle_notifications(self.notification_switch)

    def notify_user(self, header, message, override=False):
        """
        Main method to be called when notifying the user of something.
        'override' parameter to be used when notifications are turned off but user must be notified of a specific event.
        If 'debug' is true, program will log every notification to the 'log.csv' file.
        :param header:
        :param message:
        :param override:
        :return:
        """
        if self.debug:
            date = str(datetime.datetime.now())[:-7]
            event = f"{date} - {header} {message}"
            log(event)
        if self.notification_switch:
            if self.notify_level == "all":
                event_types = self._levels[self.notify_level]
                if header in event_types:
                    self.icon.notify(message, header)
            elif self.notify_level == "error/alert":
                event_types = self._levels[self.notify_level]
                if header in event_types:
                    self.icon.notify(message, header)
            elif self.notify_level == "error":
                event_types = self._levels[self.notify_level]
                if header in event_types:
                    self.icon.notify(message, header)
        if override:
            self.icon.notify(message, header)

    def start_backup(self, icon, item):
        self.config_data = self.saved_config[str(item)]
        self.controller.start_backup(self.config_data, str(item))

    def stop_backup(self):
        self.controller.stop_backup()

    def create_profile(self):
        self.controller.create_profile_window()

    def show_recent(self, i, item):
        """Shows the user the most recent backup and the time remaining till the next backup if a backup is active."""
        if self.controller.recent_backup and self.controller.thread_running:
            self.notify_user("INFO:", f"{self.controller.recent_backup}\n"
                                               f"Time left: {self.controller.get_time_left()} seconds", override=True)
        elif self.controller.recent_backup:
            self.notify_user("INFO:", f"{self.controller.recent_backup}", override=True)
        else:
            self.notify_user("INFO:", "No recent backups were made.", override=True)

    def terminate(self):
        self.controller.terminate()
