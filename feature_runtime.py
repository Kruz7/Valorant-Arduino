import json
import sys
import threading
import time

import cv2
import keyboard
import numpy as np
import win32api
from ctypes import WinDLL
from mss import mss
from valclient.client import Client

from hid_mouse_device import DeviceNotFoundError, MouseInstruct

user32, kernel32, shcore = (
    WinDLL("user32", use_last_error=True),
    WinDLL("kernel32", use_last_error=True),
    WinDLL("shcore", use_last_error=True),
)

shcore.SetProcessDpiAwareness(2)
WIDTH, HEIGHT = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

ZONE = 5
GRAB_ZONE = (
    int(WIDTH / 2 - ZONE),
    int(HEIGHT / 2 - ZONE),
    int(WIDTH / 2 + ZONE),
    int(HEIGHT / 2 + ZONE),
)

GRAB_ZONE_CENTER_X = (GRAB_ZONE[2] - GRAB_ZONE[0]) / 2
GRAB_ZONE_CENTER_Y = (GRAB_ZONE[3] - GRAB_ZONE[1]) / 2

cfg_path = "config.json"
arduino = None
_arduino_lock = threading.Lock()


def exit_process():
    sys.exit(0)


def set_runtime_config_path(path):
    global cfg_path
    cfg_path = path
    return cfg_path


def _reload_feature_flags():
    try:
        with open(cfg_path, encoding="utf-8") as json_file:
            data = json.load(json_file)
        return (
            data["aimbot"]["enable_aimbot"],
            data["triggerbot"]["enable_triggerbot"],
            data["instantlocker"]["enable_instantlocker"],
        )
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"Invalid config ({cfg_path}): {e}")
        exit_process()


enable_aim, enable_trigger, enable_instalock = _reload_feature_flags()


def refresh_runtime_flags():
    global enable_aim, enable_trigger, enable_instalock
    enable_aim, enable_trigger, enable_instalock = _reload_feature_flags()


def connect_mouse():
    try:
        device = MouseInstruct.getMouse()
        print("[+] HID mouse device found.")
        return device
    except DeviceNotFoundError as e:
        print(e)
        exit_process()


def _safe_move(dx, dy):
    global arduino
    if arduino is None:
        return
    with _arduino_lock:
        arduino.move(int(dx), int(dy))


def _safe_press():
    global arduino
    if arduino is None:
        return
    with _arduino_lock:
        arduino.press()


def _safe_release():
    global arduino
    if arduino is None:
        return
    with _arduino_lock:
        arduino.release()


class AimbotRunner:
    def __init__(self):
        global cfg_path
        self.sct = mss()
        with open(cfg_path, encoding="utf-8") as json_file:
            data = json.load(json_file)

        try:
            self.aimbot_hotkey = int(data["aimbot"]["aimbot_hotkey"], 16)
            self.experimental_filtering = data["aimbot"]["experimental_filtering"]
            self.anti_astra = data["aimbot"]["anti_astra"]
            self.enable_rcs = data["aimbot"]["enable_rcs"]
            self.x_fov = data["aimbot"]["x_fov"]
            self.y_fov = data["aimbot"]["y_fov"]
            self.cop = data["aimbot"]["cop"]
            self.x_speed = float(data["aimbot"]["x_speed"])
            self.y_speed = float(data["aimbot"]["y_speed"])
            self.x_only = data["aimbot"]["x_only"]
            self.custom_yoffset = data["aimbot"]["custom_yoffset"]
            self.monitor_id = data["arduino_settings"]["monitor_id"]
        except (KeyError, TypeError, ValueError) as e:
            print(f"Aimbot config error: {e}")
            exit_process()

        self.screenshot = self.sct.monitors[self.monitor_id]
        self.roundedgrabx = int(self.x_fov)
        self.roundedgraby = int(self.y_fov)
        self.screenshot["left"] = int((self.screenshot["width"] / 2) - (self.roundedgrabx / 2))
        self.screenshot["top"] = int((self.screenshot["height"] / 2) - (self.roundedgraby / 2))
        self.screenshot["width"] = self.roundedgrabx
        self.screenshot["height"] = self.roundedgraby
        self.center_x = self.roundedgrabx / 2
        self.center_y = self.roundedgraby / 2

        if self.anti_astra is True:
            self.lower = np.array([140, 111, 160])
            self.upper = np.array([148, 154, 194])
        else:
            self.lower = np.array([140, 110, 150])
            self.upper = np.array([150, 195, 255])

        self.purple = (150, 119, 179)
        self.hue_threshold = 0
        self.similarity_threshold = (0.82, 0.85)
        if self.experimental_filtering is True:
            if self.cop == 1:
                self.cop_ready = 3
            elif self.cop == 2:
                self.cop_ready = -1
            elif self.cop == 3:
                self.cop_ready = -4
            else:
                self.cop_ready = 5
        else:
            if self.cop == 1:
                self.cop_ready = 5
            elif self.cop == 2:
                self.cop_ready = 3
            elif self.cop == 3:
                self.cop_ready = -1
            else:
                self.cop_ready = 5
        if self.custom_yoffset != 0:
            self.cop_ready = self.custom_yoffset

    def get_similarity_map(self, image_hsv, target_hsv):
        delta = np.abs(image_hsv - target_hsv)
        delta[:, :, 0] = np.minimum(delta[:, :, 0], 180 - delta[:, :, 0]) / 180
        delta[:, :, 1] /= 255
        delta[:, :, 2] /= 255
        similarity = 1 - np.sqrt(np.sum(delta[:, :, :] ** 2, axis=2)) / np.sqrt(3)
        mask = np.logical_and(
            delta[:, :, 0] <= self.hue_threshold,
            np.logical_and(
                self.similarity_threshold[0] <= similarity,
                similarity <= self.similarity_threshold[1],
            ),
        )
        return np.where(mask, similarity, 0)

    def run(self):
        if win32api.GetAsyncKeyState(self.aimbot_hotkey) < 0:
            if self.experimental_filtering is True:
                frame = np.array(self.sct.grab(self.screenshot))
                roi = frame[
                    int(self.center_y - self.roundedgraby / 2) : int(self.center_y + self.roundedgraby / 2),
                    int(self.center_x - self.roundedgrabx / 2) : int(self.center_x + self.roundedgrabx / 2),
                ]
                roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                roi = np.array(roi, dtype=np.float32)
                similarity_map = self.get_similarity_map(roi, self.purple)
                similarity_map = (similarity_map * 255).astype(np.uint8)
                kernel = np.ones((3, 3), np.uint8)
                dilated = cv2.dilate(similarity_map, kernel, iterations=5)
                thresh = cv2.threshold(dilated, 60, 255, cv2.THRESH_BINARY)[1]
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            else:
                img = np.array(self.sct.grab(self.screenshot))
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, self.lower, self.upper)
                kernel = np.ones((3, 3), np.uint8)
                dilated = cv2.dilate(mask, kernel, iterations=5)
                thresh = cv2.threshold(dilated, 60, 255, cv2.THRESH_BINARY)[1]
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

            if len(contours) != 0:
                M = cv2.moments(thresh)
                m00 = M["m00"]
                if m00 == 0:
                    return
                point_to_aim = (int(M["m10"] / m00), int(M["m01"] / m00))
                closestX = point_to_aim[0] + 1
                closestY = point_to_aim[1] - self.cop_ready
                diff_x = closestX - self.center_x
                diff_y = closestY - self.center_y
                target_x = diff_x * self.x_speed
                target_y = diff_y * self.y_speed
                if self.x_only is True:
                    target_y = 0
                if self.enable_rcs is True and win32api.GetAsyncKeyState(0x01) < 0:
                    time.sleep(0.001)
                    target_y += 6

                _safe_move(target_x, target_y)
        else:
            time.sleep(0.002)

    def run_loop(self):
        try:
            while True:
                self.run()
        except Exception as e:
            print("Aimbot thread error:", e)


class TriggerbotRunner:
    def __init__(self):
        global cfg_path
        self.sct = mss()
        self.triggerbot = False
        self.triggerbot_toggle = True
        self.exit_program = False
        self.toggle_lock = threading.Lock()

        with open(cfg_path, encoding="utf-8") as json_file:
            data = json.load(json_file)

        try:
            self.keybind_toggle = int(data["triggerbot"]["trigger_hotkey"], 16)
            self.always_enabled = data["triggerbot"]["always_enabled"]
            self.trigger_delay = data["triggerbot"]["trigger_delay"]
            self.base_delay = data["triggerbot"]["base_delay"]
            self.color_tolerance = data["triggerbot"]["color_tolerance"]
            self.monitor_id = data["arduino_settings"]["monitor_id"]
            self.R, self.G, self.B = (250, 100, 250)
        except (KeyError, TypeError, ValueError) as e:
            print(f"Triggerbot config error: {e}")
            exit_process()

        self.screenshot = self.sct.monitors[self.monitor_id]

    def cooldown(self):
        time.sleep(0.1)
        with self.toggle_lock:
            self.triggerbot_toggle = True
            if self.triggerbot:
                kernel32.Beep(440, 75)
                kernel32.Beep(700, 100)
            else:
                kernel32.Beep(440, 75)
                kernel32.Beep(200, 100)

    def searcherino(self):
        frame = np.array(self.sct.grab(self.screenshot))
        img = frame[GRAB_ZONE[1] : GRAB_ZONE[3], GRAB_ZONE[0] : GRAB_ZONE[2]]

        pmap = np.array(img)
        pixels = pmap.reshape(-1, 4)
        color_mask = (
            (pixels[:, 0] > self.R - self.color_tolerance)
            & (pixels[:, 0] < self.R + self.color_tolerance)
            & (pixels[:, 1] > self.G - self.color_tolerance)
            & (pixels[:, 1] < self.G + self.color_tolerance)
            & (pixels[:, 2] > self.B - self.color_tolerance)
            & (pixels[:, 2] < self.B + self.color_tolerance)
        )
        matching_pixels = pixels[color_mask]

        if self.triggerbot and len(matching_pixels) > 0:
            delay_percentage = self.trigger_delay / 100.0
            actual_delay = self.base_delay + self.base_delay * delay_percentage
            time.sleep(actual_delay)
            _safe_press()
            time.sleep(0.005)
            _safe_release()

    def toggle(self):
        if keyboard.is_pressed("f10"):
            with self.toggle_lock:
                if self.triggerbot_toggle:
                    self.triggerbot = not self.triggerbot
                    print(self.triggerbot)
                    self.triggerbot_toggle = False
                    threading.Thread(target=self.cooldown, daemon=True).start()

    def hold(self):
        while True:
            while win32api.GetAsyncKeyState(self.keybind_toggle) < 0:
                self.triggerbot = True
                self.searcherino()
            else:
                time.sleep(0.1)

    def run_loop(self):
        while not self.exit_program:
            if self.always_enabled is True:
                self.toggle()
                self.searcherino() if self.triggerbot else time.sleep(0.1)
            else:
                self.hold()


class InstalockerAgent:
    def __init__(self):
        global cfg_path
        with open(cfg_path, encoding="utf-8") as json_file:
            data = json.load(json_file)

        try:
            self.region = data["instantlocker"]["region"].lower()
            self.preferred_agent = data["instantlocker"]["preferred_agent"].lower()
        except (KeyError, TypeError) as e:
            print(f"Instalocker config error: {e}")
            exit_process()

        self.agents = {
            "jett": "add6443a-41bd-e414-f6ad-e58d267f4e95",
            "reyna": "a3bfb853-43b2-7238-a4f1-ad90e9e46bcc",
            "raze": "f94c3b30-42be-e959-889c-5aa313dba261",
            "yoru": "7f94d92c-4234-0a36-9646-3a87eb8b5c89",
            "phoenix": "eb93336a-449b-9c1b-0a54-a891f7921d69",
            "neon": "bb2a4828-46eb-8cd1-e765-15848195d751",
            "breach": "5f8d3a7f-467b-97f3-062c-13acf203c006",
            "skye": "6f2a04ca-43e0-be17-7f36-b3908627744d",
            "sova": "320b2a48-4d9b-a075-30f1-1f93a9b638fa",
            "kayo": "601dbbe7-43ce-be57-2a40-4abd24953621",
            "killjoy": "1e58de9c-4950-5125-93e9-a0aee9f98746",
            "cypher": "117ed9e3-49f3-6512-3ccf-0cada7e3823b",
            "sage": "569fdd95-4d10-43ab-ca70-79becc718b46",
            "chamber": "22697a3d-45bf-8dd7-4fec-84a9e28c69d7",
            "omen": "8e253930-4c05-31dd-1b6c-968525494517",
            "brimstone": "9f0d8ba9-4140-b941-57d3-a7ad57c6b417",
            "astra": "41fb69c1-4189-7b37-f117-bcaf1e96f1bf",
            "viper": "707eab51-4836-f488-046a-cda6bf494859",
            "fade": "dade69b4-4f5a-8528-247b-219e5a1facd6",
            "gekko": "e370fa57-4757-3604-3648-499e1f642d3f",
            "harbor": "95b78ed7-4637-86d9-7e41-71ba8c293152",
            "deadlock": "cc8b64c8-4b25-4ff9-6e7f-37b4da43d235",
        }

        self.seenMatches = []

    def initialize_client(self):
        while True:
            try:
                self.client = Client(region=self.region)
                self.client.activate()
            except Exception:
                print("open game dummy")
            else:
                self.run_instalocker()
            time.sleep(2)

    def choose_preferred_agent(self):
        while True:
            try:
                if self.preferred_agent in self.agents:
                    return self.preferred_agent
                print("Invalid Agent")
            except Exception:
                print("Input Error")

    def run_instalocker(self):
        print("Waiting for Agent Select")
        while True:
            time.sleep(1)
            try:
                session_state = self.client.fetch_presence(self.client.puuid)["sessionLoopState"]
                match_id = self.client.pregame_fetch_match()["ID"]

                if session_state == "PREGAME" and match_id not in self.seenMatches:
                    print("Agent Select Found")
                    preferred_agent = self.choose_preferred_agent()
                    agent_id = self.agents[preferred_agent]
                    self.client.pregame_select_character(agent_id)
                    self.client.pregame_lock_character(agent_id)
                    self.seenMatches.append(match_id)
                    print(f"Successfully Locked {preferred_agent.capitalize()}")
            except Exception:
                pass


def start_feature_runtime():
    global arduino
    refresh_runtime_flags()
    arduino = None
    if enable_aim or enable_trigger:
        arduino = connect_mouse()

    print(cfg_path)

    if enable_aim is True:
        aimbot_instance = AimbotRunner()
        aimbot_thread = threading.Thread(target=aimbot_instance.run_loop, daemon=True, name="aimbot")
        aimbot_thread.start()
        print("aimbot started")

    if enable_trigger is True:
        triggerbot_instance = TriggerbotRunner()
        triggerbot_thread = threading.Thread(target=triggerbot_instance.run_loop, daemon=True, name="triggerbot")
        triggerbot_thread.start()
        print("triggerbot started")

    if enable_instalock is True:
        instalocker_instance = InstalockerAgent()
        instantlock_thread = threading.Thread(
            target=instalocker_instance.initialize_client, daemon=True, name="instalocker"
        )
        instantlock_thread.start()
        print("instantlocker started")

    try:
        while True:
            if keyboard.is_pressed("ctrl+shift+x"):
                exit_process()
            time.sleep(0.01)
    except KeyboardInterrupt:
        exit_process()
