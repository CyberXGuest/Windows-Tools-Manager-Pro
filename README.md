#Installation commandss
git clone https://github.com/CyberXGuest/Windows-Tools-Manager-Pro.git
cd Windows-Tools-Manager-Pro
python3 -m venv venv
source venv/bin/activate
# Install common dependencies manually
pip3 install psutil Pillow pyudev
python3 windows_manager_ultra.py
or python3 windows_pro.py
