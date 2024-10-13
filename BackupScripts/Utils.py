import datetime
import json
import os
import platform
import sys
import zipfile


def resource_path(relative_path):
    """This method is mainly used for pyinstaller to get the paths to the images when building an exe file."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.getcwd()
    return os.path.join(base_path, relative_path)


ICON_IMG = resource_path("backup.ico")
PROFILE_PATH = os.getcwd() + "\\profiles.json"
LOG_FILE = os.getcwd() + "\\log.csv"
CONFIG_FILE = os.getcwd() + "\\config.ini"


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file),
                       os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))


def compress_folder(destination_path, folders):
    with zipfile.ZipFile(f'{destination_path}.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for i in folders:
            zipdir(i, zipf)


def check_folders(sources, dest):
    """Check if dest is in the source path."""
    dest = dest.split("/")[-1]
    for source in sources:
        for dir_path, dirs, files in os.walk(source):
            for i in dirs:
                if dest == i:
                    return True
    return False


def get_birth_time(filename):
    """Return the birth time of a file, reported by os.stat()."""
    return os.stat(filename).st_birthtime


def get_last_modification(filename):
    return os.stat(filename).st_mtime


def find_copies(backup_path, source_path):
    """Returns the number of copies of the 'source_path' folder in the 'backup_path' folder."""
    count = 0
    source_name = get_folder_name(source_path)
    source_name = os.path.splitext(source_name)[0]
    for path in os.listdir(backup_path):
        cur_folder = os.path.join(backup_path, path)
        if os.path.exists(cur_folder):
            name = get_folder_name(cur_folder)
            name = os.path.splitext(name)[0]
            name = name[:len(name) - 2]
            if source_name == name:
                count += 1
    return count


def get_folder_name(path):
    return os.path.basename(os.path.normpath(path))


def find_oldest_folder(backup_path, source_path):
    """Finds the oldest folder within the given 'backup_path', finding the name of the 'source_path'."""
    ages = {}
    source_name = get_folder_name(source_path)
    source_name = os.path.splitext(source_name)[0]
    for path in os.listdir(backup_path):
        cur_folder = os.path.join(backup_path, path)
        if os.path.exists(cur_folder):
            name = get_folder_name(cur_folder)
            tmp_name = os.path.splitext(name)
            name = tmp_name[0]
            # Strip last 2 characters off end of name, so it'll match with source_name 'folder_0' to 'folder'
            name = name[:len(name) - 2]
            if source_name == name:
                if tmp_name[1] == ".zip":
                    # For reasons unknown to me, zip files have to be done with last modifications and not birth time.
                    ages.update({get_last_modification(cur_folder): cur_folder})
                else:
                    ages.update({get_birth_time(cur_folder): cur_folder})
    oldest = min(ages)
    return ages[oldest]


def log(string):
    """Logs event into the 'log.csv' file."""
    date = str(datetime.datetime.now())[:-7]
    result = f"{date} - {string}\n"
    with open(LOG_FILE, 'a') as file:
        file.write(result)


def read_config(filepath: str):
    with open(filepath, 'r') as file:
        return json.load(file)


def dump_json(filepath: str, data: dict | str) -> None:
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)
        file.truncate()


def open_config():
    if platform.system() == "Windows":
        try:
            os.startfile(PROFILE_PATH)
        except FileNotFoundError:
            dump_json(PROFILE_PATH, {})
            open_config()


def update_json(new_config, saved_config):
    cur_config_key = [i for i in new_config.keys()][0]
    saved_config_keys = [i for i in saved_config.keys()]
    if cur_config_key in saved_config_keys:
        saved_config[cur_config_key] = new_config[cur_config_key]
    else:
        saved_config.update({cur_config_key: new_config[cur_config_key]})
    return saved_config
