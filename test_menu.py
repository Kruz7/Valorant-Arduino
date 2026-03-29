import tkinter as tk
from tkinter import messagebox

THEME_BG = "#0a0a0a"
THEME_PANEL = "#121212"
THEME_BORDO = "#6e1620"
THEME_BORDO_LIGHT = "#8b2330"
THEME_BORDO_ACTIVE = "#a02838"
THEME_TEXT = "#ffffff"
THEME_TEXT_MUTED = "#c4c4c4"
THEME_BORDER = "#3d1519"


def _btn_style_primary():
    return {
        "bg": THEME_BORDO,
        "fg": THEME_TEXT,
        "activebackground": THEME_BORDO_ACTIVE,
        "activeforeground": THEME_TEXT,
        "bd": 0,
        "highlightthickness": 0,
        "relief": tk.FLAT,
        "cursor": "hand2",
        "font": ("Segoe UI", 10, "bold"),
    }


def _btn_style_nav(active=False):
    return {
        "bg": THEME_BORDO_LIGHT if active else THEME_PANEL,
        "fg": THEME_TEXT,
        "activebackground": THEME_BORDO_ACTIVE,
        "activeforeground": THEME_TEXT,
        "bd": 1,
        "highlightthickness": 0,
        "relief": tk.FLAT,
        "cursor": "hand2",
        "font": ("Segoe UI", 10),
    }


class DemoSlider(tk.Canvas):
    def __init__(self, master, width, height, min_value, max_value, initial_value, value_format="integer"):
        super().__init__(master, width=width, height=height, highlightthickness=0, bg=THEME_BG)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.value_format = value_format
        self.w = width
        self.h = height
        self.slider_w = 10
        r = 8
        self.create_rounded_rect(0, 0, width, height, r, fill=THEME_PANEL, outline="")
        self.handle = self.create_rectangle(0, 0, self.slider_w, height, fill=THEME_BORDO_LIGHT, outline="")
        self.fill_r = self.create_rectangle(0, 0, 0, height, fill=THEME_BORDO_LIGHT, outline="")
        self.val_txt = self.create_text(
            width - 4, height // 2, anchor="e", fill=THEME_TEXT, font=("Segoe UI", 9)
        )
        self.bind("<Button-1>", self._click)
        self.bind("<B1-Motion>", self._drag)
        self._sync()

    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kw):
        self.create_arc(x1, y1, x1 + 2 * radius, y1 + 2 * radius, start=90, extent=90, **kw)
        self.create_arc(x2 - 2 * radius, y1, x2, y1 + 2 * radius, start=0, extent=90, **kw)
        self.create_arc(x1, y2 - 2 * radius, x1 + 2 * radius, y2, start=180, extent=90, **kw)
        self.create_arc(x2 - 2 * radius, y2 - 2 * radius, x2, y2, start=270, extent=90, **kw)
        self.create_rectangle(x1 + radius, y1, x2 - radius, y2, **kw)

    def _set_x(self, x):
        w = self.w
        x = max(0, min(x, w))
        self.value = (x / w) * (self.max_value - self.min_value) + self.min_value
        self._sync()

    def _click(self, e):
        self._set_x(e.x)

    def _drag(self, e):
        self._set_x(e.x)

    def _sync(self):
        t = (self.value - self.min_value) / (self.max_value - self.min_value) if self.max_value != self.min_value else 0
        px = t * self.w
        self.coords(self.handle, px, 0, px + self.slider_w, self.h)
        self.coords(self.fill_r, 0, 0, px, self.h)
        if self.value_format == "raw":
            s = f"{self.value:.4f}"
        elif self.value_format == "raw2":
            s = f"{self.value:.2f}"
        elif self.value_format == "percentage":
            s = f"{int(self.value * 100)}%"
        else:
            s = str(int(self.value))
        self.itemconfig(self.val_txt, text=s)


class MenuPreview:
    def __init__(self, root):
        self.root = root
        self.root.title("Nevers — menu preview")
        self.root.geometry("680x420")
        self.root.configure(bg=THEME_BG)
        self._nav = 1

        self.canvas = tk.Canvas(
            self.root,
            bg=THEME_BG,
            height=420,
            width=680,
            bd=0,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.canvas.create_rectangle(0, 0, 148, 420, fill=THEME_PANEL, outline=THEME_BORDER, width=1)
        self.canvas.create_text(74, 30, text="Nevers", fill=THEME_TEXT, font=("Segoe UI", 15, "bold"))
        self.canvas.create_line(8, 52, 140, 52, fill=THEME_BORDO, width=2)

        self.nav_btns = []
        labels = ["Aimbot", "Triggerbot", "Instalock", "Settings"]
        for i, lab in enumerate(labels, start=1):
            b = tk.Button(
                self.canvas,
                text=lab,
                command=lambda n=i: self._select_nav(n),
                **_btn_style_nav(i == 1),
            )
            b.place(x=10, y=64 + (i - 1) * 52, width=128, height=44)
            self.nav_btns.append(b)

        self.canvas.create_rectangle(156, 56, 672, 356, fill=THEME_BG, outline=THEME_BORDER, width=1)
        self.canvas.create_text(414, 32, text="Features", fill=THEME_TEXT, font=("Segoe UI", 12, "bold"))
        self.canvas.create_line(170, 48, 658, 48, fill=THEME_BORDO, width=1)

        self.canvas.create_text(
            414,
            372,
            text="Preview — no config, HID, or game hooks. Close with ✕ or window border.",
            fill=THEME_TEXT_MUTED,
            font=("Segoe UI", 8),
        )

        self.btn_start = tk.Button(
            self.canvas,
            text="▶  START",
            command=self._fake_start,
            **_btn_style_primary(),
        )
        self.btn_start.place(x=520, y=368, width=140, height=40)

        self.btn_close = tk.Button(
            self.canvas,
            text="✕",
            command=root.destroy,
            bg=THEME_PANEL,
            fg=THEME_TEXT,
            activebackground=THEME_BORDO,
            activeforeground=THEME_TEXT,
            bd=0,
            font=("Segoe UI", 11),
            highlightthickness=0,
            cursor="hand2",
            width=2,
            height=1,
        )
        self.btn_close.place(x=642, y=6, width=32, height=28)

        self._panel = tk.Frame(self.canvas, bg=THEME_BG)
        self.canvas.create_window(160, 56, window=self._panel, anchor="nw", width=508, height=288)

        self._select_nav(1)

    def _clear_panel(self):
        for child in self._panel.winfo_children():
            child.destroy()

    def _select_nav(self, idx):
        self._nav = idx
        for i, b in enumerate(self.nav_btns, start=1):
            b.config(**_btn_style_nav(i == idx))
        self._clear_panel()
        {
            1: self._build_aim,
            2: self._build_trigger,
            3: self._build_instalock,
            4: self._build_settings,
        }[idx]()

    def _fake_start(self):
        messagebox.showinfo(
            "Preview",
            "This is test_menu.py only.\nRun gui_launcher.py for the real application.",
            parent=self.root,
        )

    def _build_aim(self):
        f = self._panel
        tk.Label(
            f,
            text="Enable Aim",
            bg=THEME_BG,
            fg=THEME_TEXT,
            font=("Segoe UI", 10, "bold"),
        ).place(x=8, y=6)
        tk.Label(f, text="X-FOV", bg=THEME_BG, fg=THEME_TEXT_MUTED, font=("Segoe UI", 9)).place(x=8, y=38)
        s1 = DemoSlider(f, 320, 18, 0, 200, 90, "integer")
        s1.place(x=100, y=36)
        tk.Label(f, text="Y-FOV", bg=THEME_BG, fg=THEME_TEXT_MUTED, font=("Segoe UI", 9)).place(x=8, y=70)
        s2 = DemoSlider(f, 320, 18, 0, 200, 60, "integer")
        s2.place(x=100, y=68)
        tk.Label(
            f,
            text="X / Y speed (demo)",
            bg=THEME_BG,
            fg=THEME_TEXT_MUTED,
            font=("Segoe UI", 9),
        ).place(x=8, y=102)
        s3 = DemoSlider(f, 400, 18, 0.01, 2, 0.5, "raw2")
        s3.place(x=8, y=126)

    def _build_trigger(self):
        f = self._panel
        tk.Label(
            f,
            text="Triggerbot",
            bg=THEME_BG,
            fg=THEME_TEXT,
            font=("Segoe UI", 10, "bold"),
        ).place(x=8, y=6)
        tk.Label(f, text="Base delay", bg=THEME_BG, fg=THEME_TEXT_MUTED, font=("Segoe UI", 9)).place(x=8, y=40)
        s1 = DemoSlider(f, 380, 18, 0.0001, 0.1, 0.02, "raw")
        s1.place(x=8, y=62)
        tk.Label(f, text="Color tolerance", bg=THEME_BG, fg=THEME_TEXT_MUTED, font=("Segoe UI", 9)).place(
            x=8, y=94
        )
        s2 = DemoSlider(f, 380, 18, 1, 100, 70, "integer")
        s2.place(x=8, y=116)

    def _build_instalock(self):
        f = self._panel
        tk.Label(
            f,
            text="Instant locker",
            bg=THEME_BG,
            fg=THEME_TEXT,
            font=("Segoe UI", 10, "bold"),
        ).place(x=8, y=6)
        tk.Label(f, text="Region", bg=THEME_BG, fg=THEME_TEXT_MUTED, font=("Segoe UI", 9)).place(x=8, y=38)
        e1 = tk.Entry(f, bg=THEME_PANEL, fg=THEME_TEXT, insertbackground=THEME_TEXT, width=28)
        e1.insert(0, "eu")
        e1.place(x=8, y=58)
        tk.Label(f, text="Agent", bg=THEME_BG, fg=THEME_TEXT_MUTED, font=("Segoe UI", 9)).place(x=8, y=96)
        e2 = tk.Entry(f, bg=THEME_PANEL, fg=THEME_TEXT, insertbackground=THEME_TEXT, width=28)
        e2.insert(0, "jett")
        e2.place(x=8, y=116)

    def _build_settings(self):
        f = self._panel
        tk.Label(
            f,
            text="Config profiles",
            bg=THEME_BG,
            fg=THEME_TEXT,
            font=("Segoe UI", 10, "bold"),
        ).place(x=8, y=6)
        tk.Label(
            f,
            text="Files in folder:",
            bg=THEME_BG,
            fg=THEME_TEXT_MUTED,
            font=("Segoe UI", 9),
        ).place(x=8, y=34)
        tk.Label(
            f,
            text="config.json\nprofile_backup.json",
            bg=THEME_BG,
            fg=THEME_TEXT,
            font=("Consolas", 9),
            justify=tk.LEFT,
        ).place(x=8, y=54, anchor="nw")
        tk.Label(f, text="Profile path", bg=THEME_BG, fg=THEME_TEXT_MUTED, font=("Segoe UI", 9)).place(
            x=8, y=108
        )
        e = tk.Entry(f, bg=THEME_PANEL, fg=THEME_TEXT, insertbackground=THEME_TEXT, width=52)
        e.insert(0, "config.json")
        e.place(x=8, y=130)
        for i, lab in enumerate(["Load", "Save", "Delete"]):
            b = tk.Button(f, text=lab, **_btn_style_primary())
            b.place(x=8 + i * 110, y=172, width=100, height=34)


def main():
    root = tk.Tk()
    MenuPreview(root)
    root.mainloop()


if __name__ == "__main__":
    main()
