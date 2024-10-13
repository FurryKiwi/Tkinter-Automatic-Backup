# Tkinter-Automatic-Backup
A basic auto backup program using Pystray and Tkinter.

Functions:
  - Rotate Backups up to a specified number of backups.
  - Compression to zip files.
  - Daily Backups, so you can schedule the program to run at specific times with Windows Task Scheduler. (config.ini file has to be configure to 'auto-start' with the profile name specified.)
  - Create/Edit Profiles to backup folder(s) to designated paths. (Local backups only for now.)
  - Basic Windows Notifications with a Windows Tray Icon.

All functions can be utilized either through the GUI provided with Tkinter or with the Windows Task Icon through Pystray.

The three classes 'Controller', 'BackupThread' and 'WindowIcon' can be utilized by themselves without the GUI if you want, a few lines specified by comments would need to be changed to do so but it can work compeletely seperate.
Or if you're wanting a different GUI framework like PyQT, you could easily implement a seperate GUI into the program utilizing the other 3 classes.

![Capture](https://github.com/user-attachments/assets/f16c8347-7663-4e1c-8aae-1ba969789aaf)![Capture1](https://github.com/user-attachments/assets/984bc61a-ab61-489c-9149-397b20b55405)
