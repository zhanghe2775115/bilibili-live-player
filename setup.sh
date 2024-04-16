#!/bin/bash
sudo apt install python3-pyqt5
apt install python3-aiohttp
apt install python3-pyqt5.qtmultimedia
apt install python3-pygame
apt install python3-pyttsx3
python3 -m venv my-venv --system-site-packages
source my-venv/bin/activate
pip3 install pyttsx3
apt install espeak libespeak1
apt install tigervnc*

#vncserver :0 -geometry 2000x1200 -dpi 150 -localhost -useold :0 -fakescreenfps 90 -FrameRate 90
