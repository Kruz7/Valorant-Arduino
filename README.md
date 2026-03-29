# Kurulum
- **Arduino:** Leonardo, Micro veya Pro Micro — **ATmega32U4** (USB HID). Arduino IDE’de **HID-Project** kütüphanesini kurun. `firmware/arduino_hid_mouse/arduino_hid_mouse.ino` dosyasını açın (klasör adı `.ino` ile aynı olmalı), kartı seçip sketch’i yükleyin.
- **Python (Windows):** Proje klasöründe `python -m venv .venv` → `.venv\Scripts\activate` → `python -m pip install --upgrade pip` → `pip install -r requirements.txt`.

# Kullanım
- Ana uygulama: `python gui_launcher.py` veya `run.bat`.
- Sadece menü önizlemesi (tkinter, ek paket gerekmez): `python test_menu.py`.
- `config.json`: `arduino_settings.monitor_id` (çoklu monitör), `com_port`, `serial_id` (115200). Aimbot veya triggerbot açıkken Arduino takılı olmalı; sadece instantlocker için Arduino zorunlu değil. PC tarafı `hid_mouse_device.RAWHID_REPORT_SIZE` (varsayılan 64) ile firmware `RAWHID_SIZE` aynı olmalı.
