"""Draw-a-digit demo UI (like the lab video).

Draw a digit -> it is shrunk to 28x28 (784 pixels, 0..127) -> the network runs
-> the UI shows the 32 hidden neurons and the 10 output digits.

Two modes:
  * No port connected: runs the same 8-bit math in Python, using
    data/weights.hex and data/biases.hex (the exact numbers the FPGA uses).
  * Port connected: sends the pixels to the FPGA over UART and shows its reply.

UART protocol (PROPOSAL - Board must implement the FPGA side, 115200 8N1):
  PC -> FPGA : 0xFF (start byte), then 784 pixel bytes (each 0..127)
  FPGA -> PC : 32 hidden bytes (0..127), then 1 digit byte (0..9)
  0xFF can never be a pixel (pixels are <= 127), so the FPGA can always resync.

Run:       python3 python/draw_ui.py
Self-test: python3 python/draw_ui.py --selftest
"""
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

import numpy as np
from PIL import Image, ImageDraw

from common import DATA, read_hex
from golden import vectorized_inference

BAUD = 115200
START = 0xFF
SIZE = 300          # drawing canvas size in screen pixels
BRUSH = 12          # brush radius

# Palette: dark lab-demo look. Blue = positive vote, red = negative vote,
# amber = neuron activity, green = the winning digit.
BG = "#0e1014"
PANEL = "#161920"
LINE = "#262a34"
TEXT = "#e7e9ee"
MUTED = "#8b92a1"
FAINT = "#5b6170"
NODE = "#2a2f3a"
POS = "#4d8dff"
NEG = "#ef5a5a"
HOT = "#f5a524"
WIN = "#2fd07a"


def load_model():
    w = read_hex(DATA / "weights.hex", 8)
    b = read_hex(DATA / "biases.hex", 16)
    # weights.hex is neuron-major: neuron n's inputs are contiguous.
    return {
        "w1": w[:32 * 784].reshape(32, 784).T,
        "w2": w[32 * 784:].reshape(10, 32).T,
        "b1": b[:32],
        "b2": b[32:42],
    }


def to_mnist(img):
    """Crop, scale to 20x20, centre by mass in 28x28 (how MNIST was made)."""
    box = img.getbbox()
    out = np.zeros((28, 28), dtype=np.float32)
    if box is None:
        return out.astype(np.uint8)
    digit = img.crop(box)
    scale = 20 / max(digit.size)
    w = max(1, round(digit.size[0] * scale))
    h = max(1, round(digit.size[1] * scale))
    d = np.asarray(digit.resize((w, h), Image.Resampling.LANCZOS), dtype=np.float32)
    ys, xs = np.indices(d.shape)
    total = d.sum() or 1
    top = int(np.clip(round(14 - (ys * d).sum() / total), 0, 28 - h))
    left = int(np.clip(round(14 - (xs * d).sum() / total), 0, 28 - w))
    out[top:top + h, left:left + w] = d
    return (np.clip(out, 0, 255).astype(np.uint8) >> 1)   # 0..127, like pixels_uint7


def selftest(model):
    images = read_hex(DATA / "images.hex", 8, signed=False).reshape(16, 784)
    expected = read_hex(DATA / "exp_digit.hex", 4, signed=False)
    _, _, digits = vectorized_inference(images, model)
    ok = np.array_equal(digits, expected)
    print("selftest:", "PASS" if ok else f"FAIL got {digits} expected {expected}")
    return ok


def mix(a, b, t):
    """Blend colour a toward b by t (0..1). Tk has no alpha, so fade = blend into BG."""
    t = max(0.0, min(1.0, t))
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def pick_font(root, *names):
    have = set(tkfont.families(root))
    return next((n for n in names if n in have), "TkDefaultFont")


class App:
    def __init__(self, root, model):
        self.root, self.model, self.ser = root, model, None
        self.img = Image.new("L", (SIZE, SIZE), 0)
        self.pen = ImageDraw.Draw(self.img)
        self.last = None
        self.view = (np.zeros(784, np.uint8), np.zeros(32, np.uint8), None, None)

        sans = pick_font(root, "Inter", "Adwaita Sans", "Segoe UI", "Helvetica", "DejaVu Sans")
        mono = pick_font(root, "Hack", "Adwaita Mono", "Consolas", "DejaVu Sans Mono")
        self.f_title = (sans, 15, "bold")
        self.f_label = (sans, 10)
        self.f_node = (sans, 11, "bold")
        self.f_num = (mono, 9)
        self.f_big = (sans, 96, "bold")

        root.title("MNIST FPGA demo")
        root.configure(bg=BG)
        root.geometry("1200x680")
        root.minsize(980, 600)
        self._style(sans)

        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        # ---- left: drawing + prediction ----
        left = tk.Frame(root, bg=BG)
        left.grid(row=0, column=0, sticky="ns", padx=(20, 10), pady=(18, 8))
        tk.Label(left, text="Draw a digit", fg=TEXT, bg=BG, font=self.f_title).pack(anchor="w")
        tk.Label(left, text="Release the mouse to run it. Press C to clear.",
                 fg=MUTED, bg=BG, font=self.f_label).pack(anchor="w", pady=(2, 10))
        self.draw = tk.Canvas(left, width=SIZE, height=SIZE, bg="black", cursor="pencil",
                              highlightthickness=1, highlightbackground=LINE)
        self.draw.pack()
        self.draw.bind("<B1-Motion>", self.stroke)
        self.draw.bind("<ButtonPress-1>", self.stroke)
        self.draw.bind("<ButtonRelease-1>", self.release)
        ttk.Button(left, text="Clear", command=self.clear).pack(fill="x", pady=(10, 0))
        root.bind("<KeyPress-c>", lambda _e: self.clear())
        root.bind("<KeyPress-C>", lambda _e: self.clear())

        card = tk.Frame(left, bg=PANEL, highlightthickness=1, highlightbackground=LINE)
        card.pack(fill="x", pady=(16, 0))
        tk.Label(card, text="Prediction", fg=MUTED, bg=PANEL, font=self.f_label).pack(
            anchor="w", padx=14, pady=(10, 0))
        self.pred = tk.Label(card, text="?", fg=FAINT, bg=PANEL, font=self.f_big)
        self.pred.pack(pady=(0, 0))
        self.pred_note = tk.Label(card, text="Nothing drawn yet", fg=MUTED, bg=PANEL,
                                  font=self.f_label, justify="center")
        self.pred_note.pack(pady=(0, 12))

        # ---- right: network picture (redraws to fit the window) ----
        right = tk.Frame(root, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=(18, 8))
        tk.Label(right, text="The network   784 pixels  →  32 hidden neurons  →  10 digits",
                 fg=TEXT, bg=BG, font=self.f_title).pack(anchor="w")
        tk.Label(right, text="Line colour shows each hidden neuron's vote: blue pushes a digit up, "
                 "red pushes it down. Brighter means a stronger vote.",
                 fg=MUTED, bg=BG, font=self.f_label).pack(anchor="w", pady=(2, 10))
        self.net = tk.Canvas(right, bg=PANEL, highlightthickness=1, highlightbackground=LINE)
        self.net.pack(fill="both", expand=True)
        self.net.bind("<Configure>", lambda _e: self.show(*self.view))

        # ---- bottom: connection bar ----
        bar = tk.Frame(root, bg=PANEL, highlightthickness=1, highlightbackground=LINE)
        bar.grid(row=1, column=0, columnspan=2, sticky="we", padx=20, pady=(8, 18))
        self.mode = tk.Label(bar, fg=BG, bg=WIN, font=(sans, 9, "bold"), padx=8, pady=2)
        self.mode.pack(side="left", padx=(12, 10), pady=10)
        self.status = tk.Label(bar, fg=TEXT, bg=PANEL, font=self.f_label, anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        self.conn_btn = ttk.Button(bar, text="Connect", style="Accent.TButton", command=self.toggle)
        self.conn_btn.pack(side="right", padx=(6, 12), pady=8)
        ttk.Button(bar, text="Refresh", command=self.refresh).pack(side="right")
        self.port = ttk.Combobox(bar, width=16, state="readonly")
        self.port.pack(side="right", padx=6)
        tk.Label(bar, text="Port", fg=MUTED, bg=PANEL, font=self.f_label).pack(side="right")

        self.refresh()
        self.set_mode()
        self.clear()

    def _style(self, sans):
        s = ttk.Style(self.root)
        s.theme_use("clam")
        s.configure("TButton", background=NODE, foreground=TEXT, bordercolor=LINE,
                    lightcolor=NODE, darkcolor=NODE, focuscolor=POS,
                    font=(sans, 10), padding=(12, 5))
        s.map("TButton", background=[("pressed", LINE), ("active", "#343a47")],
              foreground=[("disabled", FAINT)])
        s.configure("Accent.TButton", background=POS, foreground="#ffffff", bordercolor=POS,
                    lightcolor=POS, darkcolor=POS)
        s.map("Accent.TButton", background=[("pressed", "#3a74db"), ("active", "#6aa0ff")])
        s.configure("TCombobox", fieldbackground=NODE, background=NODE, foreground=TEXT,
                    bordercolor=LINE, arrowcolor=TEXT, lightcolor=NODE, darkcolor=NODE)
        s.map("TCombobox", fieldbackground=[("readonly", NODE)],
              foreground=[("readonly", TEXT)], selectbackground=[("readonly", NODE)],
              selectforeground=[("readonly", TEXT)])
        self.root.option_add("*TCombobox*Listbox.background", PANEL)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", POS)

    # ---- drawing ----
    def stroke(self, e):
        x, y = e.x, e.y
        self.draw.delete("hint")
        if self.last:
            self.draw.create_line(*self.last, x, y, fill="white", width=2 * BRUSH,
                                  capstyle="round", smooth=True)
            self.pen.line([self.last, (x, y)], fill=255, width=2 * BRUSH)
        self.draw.create_oval(x - BRUSH, y - BRUSH, x + BRUSH, y + BRUSH, fill="white", width=0)
        self.pen.ellipse([x - BRUSH, y - BRUSH, x + BRUSH, y + BRUSH], fill=255)
        self.last = (x, y)

    def release(self, _):
        self.last = None
        self.run()

    def clear(self):
        self.draw.delete("all")
        self.draw.create_text(SIZE // 2, SIZE // 2, text="Draw a digit 0–9 here",
                              fill=FAINT, font=self.f_label, tags="hint")
        self.pen.rectangle([0, 0, SIZE, SIZE], fill=0)
        self.pred.config(text="?", fg=FAINT)
        self.pred_note.config(text="Nothing drawn yet")
        self.show(np.zeros(784, np.uint8), np.zeros(32, np.uint8), None, None)

    # ---- inference ----
    def run(self):
        px = to_mnist(self.img).reshape(784)
        hidden, scores, digit = vectorized_inference(px, self.model)
        py_digit = int(digit[0])
        if self.ser is None:
            self.show(px, hidden[0], scores[0], py_digit)
            s = np.sort(scores[0])
            self.predict(py_digit, f"from the Python model\nlead over 2nd place: {int(s[-1] - s[-2])}")
            self.say(f"Python model says {py_digit}. Same 8-bit math and weights as the FPGA.")
            return
        self.say("Sending 784 pixels to the FPGA…")
        self.root.update_idletasks()
        try:
            self.ser.reset_input_buffer()
            self.ser.write(bytes([START]) + px.tobytes())
            reply = self.ser.read(33)
        except Exception as err:   # cable pulled etc.: report, don't crash the UI
            self.say(f"Serial error: {err}. Check the cable, then Disconnect and Connect.", bad=True)
            return
        if len(reply) != 33:
            self.say(f"FPGA sent {len(reply)} of 33 bytes before timing out. "
                     "Is the bitstream loaded and the board reset?", bad=True)
            return
        fpga_digit = reply[32]
        self.show(px, np.frombuffer(reply[:32], np.uint8), None, fpga_digit)
        same = fpga_digit == py_digit
        self.predict(fpga_digit, "from the FPGA\n" + ("matches the Python model" if same
                                                       else f"Python model says {py_digit}"))
        self.say(f"FPGA says {fpga_digit}. " + ("Matches the Python model."
                                                 if same else f"MISMATCH: Python says {py_digit}."),
                 bad=not same)

    def predict(self, digit, note):
        self.pred.config(text=str(digit), fg=WIN)
        self.pred_note.config(text=note)

    def say(self, text, bad=False):
        self.status.config(text=text, fg=NEG if bad else TEXT)

    # ---- network picture ----
    def show(self, px, hidden, scores, digit):
        self.view = (px, hidden, scores, digit)
        c = self.net
        c.delete("all")
        W, H = max(c.winfo_width(), 600), max(c.winfo_height(), 400)
        top, bot = 46, H - 24

        # column positions
        cell = max(3, min(6, (H - 120) // 28))
        ix, iy = 28, (H - 28 * cell) // 2
        hx = int(W * 0.47)
        ox = int(W * 0.74)
        hy = np.linspace(top, bot, 32).tolist()
        oy = np.linspace(top + 10, bot - 10, 10).tolist()

        for x, label in ((ix + 14 * cell, "INPUT  28×28"), (hx, "HIDDEN  32"), (ox, "OUTPUT  10")):
            c.create_text(x, 20, text=label, fill=MUTED, font=self.f_label)

        # input image, exactly what is sent
        c.create_rectangle(ix - 1, iy - 1, ix + 28 * cell, iy + 28 * cell, outline=LINE, fill="black")
        for i in np.flatnonzero(px).tolist():
            g = mix("#000000", "#ffffff", px[i] / 127)
            x, y = ix + (i % 28) * cell, iy + (i // 28) * cell
            c.create_rectangle(x, y, x + cell, y + cell, fill=g, width=0)

        act = hidden.astype(np.float64) / max(1, int(hidden.max()))   # brightest neuron = full amber
        # input -> hidden: brightness = how active the neuron is
        ex = ix + 28 * cell + 4
        for k in np.flatnonzero(hidden):
            c.create_line(ex, H / 2, hx - 8, hy[k], fill=mix(PANEL, HOT, 0.15 + 0.5 * act[k]))

        # hidden -> output: each line is hidden[k] * weight = that neuron's vote
        votes = hidden.astype(np.int64)[:, None] * self.model["w2"]
        vmax = max(1, int(np.abs(votes).max()))
        order = []
        for k in range(32):
            for j in range(10):
                v = votes[k, j] / vmax
                if abs(v) < (0.06 if j == digit else 0.2):
                    continue
                strength = abs(v) if j == digit else abs(v) * 0.2
                order.append((strength, k, j, v))
        for strength, k, j, v in sorted(order):          # weak first, strong on top
            c.create_line(hx + 8, hy[k], ox - 16, oy[j],
                          fill=mix(PANEL, POS if v > 0 else NEG, 0.15 + 0.85 * strength),
                          width=2 if j == digit and strength > 0.4 else 1)

        for k in range(32):
            col = mix(NODE, HOT, act[k]) if hidden[k] else NODE
            c.create_oval(hx - 7, hy[k] - 7, hx + 7, hy[k] + 7, fill=col, outline=PANEL)
        if not hidden.any():
            c.create_text((ex + hx) / 2, H / 2, text="Draw a digit to see\nthe neurons light up",
                          fill=FAINT, font=self.f_label, justify="center")

        # outputs: digit node + score bar
        bx0, bx1 = ox + 30, W - 70
        if scores is not None:
            lo, hi = float(scores.min()), float(scores.max())
            span = max(1.0, hi - lo)
        for j in range(10):
            win = j == digit
            r = 15
            c.create_oval(ox - r, oy[j] - r, ox + r, oy[j] + r,
                          fill=WIN if win else NODE, outline=WIN if win else LINE)
            c.create_text(ox, oy[j], text=str(j), font=self.f_node, fill=BG if win else TEXT)
            if scores is not None:
                frac = (scores[j] - lo) / span
                c.create_rectangle(bx0, oy[j] - 4, bx1, oy[j] + 4, fill=NODE, width=0)
                c.create_rectangle(bx0, oy[j] - 4, bx0 + (bx1 - bx0) * frac, oy[j] + 4,
                                   fill=WIN if win else MUTED, width=0)
                c.create_text(W - 16, oy[j], text=f"{int(scores[j]):,}", anchor="e",
                              fill=TEXT if win else MUTED, font=self.f_num)
        if scores is None and digit is not None:
            c.create_text((bx0 + bx1) / 2, bot + 8, text="scores stay on the FPGA",
                          fill=FAINT, font=self.f_label)

    # ---- serial ----
    def set_mode(self):
        if self.ser:
            self.mode.config(text="FPGA", bg=POS)
        else:
            self.mode.config(text="PYTHON MODEL", bg=WIN)

    def refresh(self):
        try:
            from serial.tools import list_ports
            ports = [p.device for p in list_ports.comports() if p.hwid != "n/a"]
        except ImportError:
            ports = []
        self.port["values"] = ports
        if ports and not self.port.get():
            self.port.set(ports[0])
        if not ports:
            self.say("No board found. Plug in the USB cable and press Refresh. "
                     "Until then, the Python model answers.")

    def toggle(self):
        if self.ser:
            self.ser.close()
            self.ser = None
            self.conn_btn.config(text="Connect")
            self.set_mode()
            self.say("Disconnected. The Python model answers now.")
            return
        if not self.port.get():
            self.say("Pick a port first. If the list is empty, plug in the board and press Refresh.",
                     bad=True)
            return
        try:
            import serial
            self.ser = serial.Serial(self.port.get(), BAUD, timeout=2)
        except Exception as err:
            self.say(f"Could not open {self.port.get()}: {err}", bad=True)
            return
        self.conn_btn.config(text="Disconnect")
        self.set_mode()
        self.say(f"Connected to {self.port.get()}. The digit also shows on the 7-segment display.")


def main():
    model = load_model()
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest(model) else 1)
    root = tk.Tk()
    App(root, model)
    root.mainloop()


if __name__ == "__main__":
    main()
