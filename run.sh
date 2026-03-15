#!/bin/bash
cd /home/sergio/Documents/Webnovel-Scanner || exit 1
source venv/bin/activate
python -m app.main

# For Linux you can create a .desktop:
  #[Desktop Entry]
  #Version=2.0
  #Type=Application
  #Name=Webnovel Scanner
  #Exec=/home/user/Documents/Webnovel-Scanner/run.sh
  #Icon=/home/user/Documents/Webnovel-Scanner/assets/icon.png
  #Path=/home/user/Documents/Webnovel-Scanner
  #Comment=Webnovels scanner
  #Categories=Utility;
  #Terminal=true
  #StartupWMClass=Noveldownloader
  #StartupNotify=true