import hid

MOUSE_LEFT = 1
MOUSE_RIGHT = 2
MOUSE_MIDDLE = 4
MOUSE_ALL = MOUSE_LEFT | MOUSE_RIGHT | MOUSE_MIDDLE

RAWHID_REPORT_SIZE = 64


def _pad_report(payload: bytes) -> bytes:
    if len(payload) > RAWHID_REPORT_SIZE:
        return payload[:RAWHID_REPORT_SIZE]
    return payload + bytes(RAWHID_REPORT_SIZE - len(payload))


class MouseInstruct:
    def __init__(self, dev):
        self._buttons_mask = 0
        self._dev = dev
        self.move(0, 0)

    @classmethod
    def getMouse(cls, vid=0, pid=0, ping_code=0xF9):
        dev = find_mouse_device(vid, pid, ping_code)
        if not dev:
            vid_str = hex(vid) if vid else "Unspecified"
            pid_str = hex(pid) if pid else "Unspecified"
            ping_code_str = hex(ping_code) if ping_code else "Unspecified"
            error_msg = (
                "[-] Device "
                f"Vendor ID: {vid_str}, Product ID: {pid_str} "
                f"Pingcode: {ping_code_str} not found!"
            )
            raise DeviceNotFoundError(error_msg)
        return cls(dev)

    def _buttons(self, buttons):
        if buttons != self._buttons_mask:
            self._buttons_mask = buttons
            self.move(0, 0)

    def click(self, button=MOUSE_LEFT):
        self._buttons_mask = button
        self.move(0, 0)
        self._buttons_mask = 0
        self.move(0, 0)

    def press(self, button=MOUSE_LEFT):
        self._buttons(self._buttons_mask | button)

    def release(self, button=MOUSE_LEFT):
        self._buttons(self._buttons_mask & ~button)

    def is_pressed(self, button=MOUSE_LEFT):
        return bool(button & self._buttons_mask)

    def move(self, x, y):
        limited_x = limit_xy(x)
        limited_y = limit_xy(y)
        self._sendRawReport(self._makeReport(limited_x, limited_y))

    def _makeReport(self, x, y):
        return bytes(
            [
                self._buttons_mask,
                low_byte(x),
                high_byte(x),
                low_byte(y),
                high_byte(y),
            ]
        )

    def _sendRawReport(self, report_data: bytes):
        self._dev.write(_pad_report(report_data))


class DeviceNotFoundError(Exception):
    pass


def check_ping(dev, ping_code):
    dev.write(_pad_report(bytes([ping_code])))
    try:
        resp = dev.read(max_length=1, timeout_ms=10)
    except OSError:
        return False
    return bool(resp) and resp[0] == ping_code


def find_mouse_device(vid, pid, ping_code):
    for dev_info in hid.enumerate(vid, pid):
        dev = hid.device()
        try:
            dev.open_path(dev_info["path"])
        except OSError:
            continue
        if check_ping(dev, ping_code):
            return dev
        dev.close()
    return None


def limit_xy(xy):
    if xy < -32767:
        return -32767
    if xy > 32767:
        return 32767
    return xy


def low_byte(x):
    return x & 0xFF


def high_byte(x):
    return (x >> 8) & 0xFF
