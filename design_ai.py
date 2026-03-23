#asked ai to add comments to understand it well......and i added a splash window to this check it cout later


"""
weather_frontend.py
═══════════════════════════════════════════════════════════════════════════════
FRONTEND LAYER — PySide6 Weather Application
─────────────────────────────────────────────
This file is purely responsible for the UI. It owns:
  • All widget construction and layout
  • All visual styling (palette, stylesheets, custom-painted widgets)
  • The animated Aurora background
  • 4 tabs: Current, Compare, History, Trends

What this file does NOT do:
  • Make any network requests
  • Read/write any database
  • Hold any real weather data

═══════════════════════════════════════════════════════════════════════════════
HOW TO CONNECT THE BACKEND
─────────────────────────────────────────────
Every place the backend needs to push data is marked with:

    # ── BACKEND HOOK ──

Search that tag to find every integration point in one go.

Each hook documents:
  - What data it expects (field names + types)
  - Which method to call
  - What the UI will do with the data

The general pattern everywhere is:
    tab.load_data( <your_dict_here> )

═══════════════════════════════════════════════════════════════════════════════
DEPENDENCIES
─────────────────────────────────────────────
    pip install PySide6 matplotlib numpy
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
from datetime import datetime

from PySide6.QtWidgets import *
from PySide6.QtCore    import Qt, QTimer
from PySide6.QtGui     import (QPainter, QColor, QFont, QLinearGradient,
                                QPen, QPainterPath, QRadialGradient)

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


# ═══════════════════════════════════════════════════════════════════════════════
#  PALETTE
#  All colours live here. Change a value once and it updates everywhere.
# ═══════════════════════════════════════════════════════════════════════════════
BG_CARD   = QColor(10, 22, 44, 165)   # semi-transparent navy  — card backgrounds
BORDER    = QColor(90, 170, 255, 40)  # subtle blue            — default card borders
BORDER_HI = QColor(110, 195, 255, 85) # brighter blue          — glowing card border
ACC       = "#4fc3f7"                 # sky blue               — accent / headings
TXT_PRI   = "#e8f4fd"                 # near-white             — primary text
TXT_SEC   = "#7bafd4"                 # muted blue             — secondary text
TXT_DIM   = "#2e5070"                 # dark blue              — labels / dimmed text
DANGER    = "#ef5350"                 # red                    — error / extreme heat
WARN      = "#ffb74d"                 # amber                  — warnings / sunrise
FONT      = "Segoe UI"               # global font family


# ═══════════════════════════════════════════════════════════════════════════════
#  DESIGN PRIMITIVES
#  Small reusable building blocks used throughout all tabs.
#  Backend: you don't need to touch any of these.
# ═══════════════════════════════════════════════════════════════════════════════

def L(text="", size=12, bold=False, color=TXT_PRI,
      align=Qt.AlignmentFlag.AlignLeft):
    """
    Shorthand factory for a styled QLabel.
    Used everywhere to avoid repeating font/colour setup for every label.
    """
    l = QLabel(text)
    f = QFont(FONT, size)
    f.setBold(bold)
    l.setFont(f)
    l.setAlignment(align)
    l.setStyleSheet(f"color:{color}; background:transparent;")
    return l


class Frost(QWidget):
    """
    Custom-painted frosted glass card widget.

    Draws a semi-transparent navy rounded rectangle with a subtle top highlight
    and an optional outer glow ring (used on the hero weather card).

    Parameters
    ----------
    r    : corner radius in pixels (default 18)
    glow : if True, draws a second outer ring to make the card pop
    """
    def __init__(self, parent=None, r=18, glow=False):
        super().__init__(parent)
        self._r    = r
        self._glow = glow
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # rounded rect filled with the semi-transparent navy colour
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._r, self._r)
        p.fillPath(path, BG_CARD)

        # top highlight — very faint white gradient so it reads as "glass"
        hi = QLinearGradient(0, 0, 0, 55)
        hi.setColorAt(0, QColor(255, 255, 255, 16))
        hi.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(path, hi)

        # border
        p.setPen(QPen(BORDER_HI if self._glow else BORDER, 1))
        p.drawPath(path)

        # outer glow ring (hero card only)
        if self._glow:
            gp = QPainterPath()
            gp.addRoundedRect(-2, -2, self.width()+4, self.height()+4,
                               self._r+2, self._r+2)
            p.setPen(QPen(QColor(79, 195, 247, 28), 3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(gp)


# ── Shared stylesheet strings ──────────────────────────────────────────────────
# Defined once and applied to every QLineEdit / QPushButton / QComboBox
# so they all look consistent without duplicating CSS everywhere.

SS = (                                        # QLineEdit style
    f"QLineEdit{{background:rgba(6,16,34,210);"
    f"border:1px solid rgba(90,170,255,38);border-radius:12px;"
    f"padding:0 16px;color:{TXT_PRI};}}"
    f"QLineEdit:focus{{border:1.5px solid rgba(79,195,247,110);}}"
)

BSS = (                                       # QPushButton style
    f"QPushButton{{background:rgba(79,195,247,20);"
    f"border:1px solid rgba(79,195,247,55);border-radius:12px;"
    f"color:{ACC};font-family:{FONT};}}"
    f"QPushButton:hover{{background:rgba(79,195,247,38);}}"
    f"QPushButton:pressed{{background:rgba(79,195,247,12);}}"
)

CSS = (                                       # QComboBox style
    f"QComboBox{{background:rgba(6,16,34,210);"
    f"border:1px solid rgba(90,170,255,38);border-radius:10px;"
    f"padding:0 12px;color:{TXT_PRI};font-family:{FONT};}}"
    f"QComboBox::drop-down{{border:none;width:24px;}}"
    f"QComboBox QAbstractItemView{{background:#060f1e;color:{TXT_PRI};"
    f"border:1px solid rgba(79,195,247,45);"
    f"selection-background-color:rgba(79,195,247,28);}}"
)


class Pill(Frost):
    """
    Small stat card used in the 2x2 grid on the Current tab
    and the 4-pill stats row on the Trends tab.

    Displays an emoji icon, a dim label, and a bold value.
    Call pill.set("new value") to update the displayed value at runtime.
    """
    def __init__(self, emoji, label, value):
        super().__init__(r=14)
        self.setFixedHeight(72)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(2)
        top = QHBoxLayout()
        el  = QLabel(emoji)
        el.setFont(QFont(FONT, 14))
        el.setStyleSheet("background:transparent;")
        top.addWidget(el)
        top.addWidget(L(label, 9, color=TXT_DIM))
        top.addStretch()
        self._v = L(value, 15, bold=True)
        lay.addLayout(top)
        lay.addWidget(self._v)

    def set(self, v):
        """Update the displayed value text."""
        self._v.setText(v)


class HChip(Frost):
    """
    Small hourly forecast chip (time / weather icon / temperature).
    Rendered inside a horizontal scroll area on the Current tab.
    One chip is created per hour entry in the hourly list.
    """
    def __init__(self, time, icon, temp):
        super().__init__(r=14)
        self.setFixedSize(82, 108)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 8, 4, 8)
        lay.setSpacing(3)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(L(time, 9, color=ACC, align=Qt.AlignmentFlag.AlignCenter))
        ic = QLabel(icon)
        ic.setFont(QFont(FONT, 20))
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet("background:transparent;")
        lay.addWidget(ic)
        lay.addWidget(L(f"{temp}°", 11, bold=True,
                        align=Qt.AlignmentFlag.AlignCenter))


class FRow(Frost):
    """
    Single row in the 7-day forecast card on the Current tab.
    Shows day name, weather icon, rain probability, and high/low temps.
    One FRow is created per entry in the forecast list.
    """
    def __init__(self, day, icon, high, low, rain):
        super().__init__(r=12)
        self.setFixedHeight(52)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 18, 0)
        dl = L(day, 12, bold=True)
        dl.setFixedWidth(40)
        ic = QLabel(icon)
        ic.setFont(QFont(FONT, 18))
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet("background:transparent;")
        ic.setFixedWidth(34)
        rl = L(f"💧{rain}%", 10, color=ACC)
        rl.setFixedWidth(56)
        lay.addWidget(dl)
        lay.addWidget(ic)
        lay.addWidget(rl)
        lay.addStretch()
        lay.addWidget(L(f"{low}°", 12, color=TXT_SEC,
                        align=Qt.AlignmentFlag.AlignRight))
        lay.addSpacing(6)
        lay.addWidget(L("·····", 9, color=TXT_DIM,
                        align=Qt.AlignmentFlag.AlignCenter))
        lay.addSpacing(6)
        lay.addWidget(L(f"{high}°", 13, bold=True,
                        align=Qt.AlignmentFlag.AlignRight))


# ═══════════════════════════════════════════════════════════════════════════════
#  AURORA BACKGROUND
#  Animated deep-navy gradient with two drifting colour blobs and a star field.
#  This is the central widget of the main window — all tabs sit on top of it.
#  Backend: no interaction needed here.
# ═══════════════════════════════════════════════════════════════════════════════
class Aurora(QWidget):
    """
    Custom-painted animated background.

    Repaints at ~20 fps via a QTimer. Each frame advances a time counter (_t)
    which drives two sine/cosine blob positions, creating the drifting aurora
    effect. The star field uses a fixed random seed so stars never move.
    """
    def __init__(self):
        super().__init__()
        self._t = 0.0
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(50)   # 50 ms = 20 fps — smooth without hammering the CPU

    def _tick(self):
        """Advance the animation clock and schedule a repaint."""
        self._t += 0.8
        self.update()

    def paintEvent(self, e):
        import math, random
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # ── base sky gradient (top to bottom, three dark navy stops) ─────────
        base = QLinearGradient(0, 0, 0, h)
        base.setColorAt(0.0, QColor("#010a15"))
        base.setColorAt(0.5, QColor("#020e1c"))
        base.setColorAt(1.0, QColor("#010b17"))
        p.fillRect(self.rect(), base)

        # ── blob 1: blue, drifts around upper-right quadrant ─────────────────
        bx = w*0.72 + math.sin(math.radians(self._t*0.55)) * 130
        by = h*0.20 + math.cos(math.radians(self._t*0.38)) * 65
        g  = QRadialGradient(bx, by, 370)
        g.setColorAt(0.0,  QColor(18,  85, 200, 42))
        g.setColorAt(0.55, QColor(10,  55, 150, 18))
        g.setColorAt(1.0,  QColor(0,    0,   0,  0))
        pp = QPainterPath()
        pp.addEllipse(bx-370, by-280, 740, 560)
        p.fillPath(pp, g)

        # ── blob 2: teal, drifts around lower-left quadrant ──────────────────
        bx2 = w*0.20 + math.cos(math.radians(self._t*0.45)) * 110
        by2 = h*0.62 + math.sin(math.radians(self._t*0.32)) * 75
        g2  = QRadialGradient(bx2, by2, 290)
        g2.setColorAt(0.0, QColor(0, 130, 165, 30))
        g2.setColorAt(0.6, QColor(0,  80, 120, 12))
        g2.setColorAt(1.0, QColor(0,   0,   0,  0))
        pp2 = QPainterPath()
        pp2.addEllipse(bx2-290, by2-230, 580, 460)
        p.fillPath(pp2, g2)

        # ── star field (seed=42 keeps positions identical every frame) ────────
        rng = random.Random(42)
        p.setPen(QPen(QColor(255, 255, 255, 28), 1))
        for _ in range(55):
            p.drawPoint(rng.randint(0, w), rng.randint(0, h))


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — CURRENT WEATHER
# ═══════════════════════════════════════════════════════════════════════════════
class CurrentTab(QWidget):
    """
    Displays current weather conditions for a searched city.

    Layout (top to bottom inside a scroll area):
      • Search bar + button
      • Status / error label
      • Hero card  (city, date, icon, temperature, feels-like, UV, sunrise/sunset)
      • 2x2 stat pills  (humidity, wind, pressure, visibility)
      • Alert banner  (hidden unless extreme conditions detected)
      • Hourly forecast horizontal scroll  (HChip widgets)
      • 7-day forecast card  (FRow widgets)

    ── BACKEND HOOK ──────────────────────────────────────────────────────────
    Call  CurrentTab.load_data(data)  with this dict:

        {
            "city":       str,          # e.g. "Mumbai"
            "country":    str,          # ISO code e.g. "IN"
            "temp":       float,        # current temperature in Celsius
            "feels_like": float,        # apparent temperature in Celsius
            "humidity":   int,          # relative humidity 0-100
            "pressure":   int,          # surface pressure in hPa
            "wind":       float,        # wind speed in km/h
            "visibility": float,        # visibility in km
            "condition":  str,          # human-readable e.g. "Partly Cloudy"
            "icon":       str,          # weather emoji e.g. "⛅"
            "uv_index":   float,        # UV index value
            "sunrise":    str,          # local time string "HH:MM"
            "sunset":     str,          # local time string "HH:MM"

            "hourly": [                 # list of up to 8 upcoming hourly slots
                {
                    "time": str,        # "Now" for current slot, else "HH:MM"
                    "icon": str,        # weather emoji
                    "temp": float,      # temperature in Celsius
                },
                ...
            ],

            "forecast": [               # list of 7 daily entries
                {
                    "day":  str,        # short day name e.g. "Mon"
                    "icon": str,        # weather emoji
                    "high": float,      # daily high in Celsius
                    "low":  float,      # daily low in Celsius
                    "rain": int,        # precipitation probability 0-100
                },
                ...
            ],
        }

    The search bar calls _fetch() — replace that method's body with your
    actual API/thread call, then call self.load_data(result) when done.
    ──────────────────────────────────────────────────────────────────────────
    """

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build()

    def _build(self):
        """Construct and lay out all widgets. Called once at init."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Wrap everything in a scroll area so it works on small screens
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setStyleSheet("background:transparent; border:none;")
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(sc)

        body = QWidget()
        body.setStyleSheet("background:transparent;")
        sc.setWidget(body)
        lay = QVBoxLayout(body)
        lay.setSpacing(14)
        lay.setContentsMargins(20, 20, 20, 28)

        # ── Search bar ────────────────────────────────────────────────────────
        # returnPressed and the button both call _fetch()
        row = QHBoxLayout(); row.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search any city in the world…")
        self.search.setFixedHeight(46)
        self.search.setFont(QFont(FONT, 12))
        self.search.setStyleSheet(SS)
        self.search.returnPressed.connect(self._fetch)
        btn = QPushButton("Search")
        btn.setFixedSize(100, 46)
        btn.setFont(QFont(FONT, 12))
        btn.setStyleSheet(BSS)
        btn.clicked.connect(self._fetch)
        row.addWidget(self.search)
        row.addWidget(btn)
        lay.addLayout(row)

        # Status / error label — hidden when empty, shown on fetch or error
        self.status = L("", 10, color=DANGER, align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.status)

        # ── Hero card ─────────────────────────────────────────────────────────
        # The main weather display: city, large icon + temperature, sub-details
        hero = Frost(r=22, glow=True)
        hero.setMinimumHeight(228)
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(24, 18, 24, 18)
        hl.setSpacing(8)

        # Row: city name (left) + date (right)
        cr = QHBoxLayout()
        self.city_lbl = L("—", 20, bold=True)
        self.date_lbl = L("", 10, color=TXT_DIM)
        cr.addWidget(self.city_lbl)
        cr.addStretch()
        cr.addWidget(self.date_lbl)
        hl.addLayout(cr)

        # Condition text below city name
        self.cond_lbl = L("Enter a city to get live weather", 11, color=TXT_SEC)
        hl.addWidget(self.cond_lbl)
        hl.addSpacing(4)

        # Row: large emoji icon + large temperature + feels/UV on the right
        mid = QHBoxLayout()
        self.icon_lbl = QLabel("🌐")
        self.icon_lbl.setFont(QFont(FONT, 56))
        self.icon_lbl.setStyleSheet("background:transparent;")
        self.temp_lbl = L("—", 56, bold=True)
        mid.addWidget(self.icon_lbl)
        mid.addWidget(self.temp_lbl)
        mid.addStretch()
        rhs = QVBoxLayout()
        rhs.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        rhs.setSpacing(6)
        self.feels_lbl = L("Feels like —", 11, color=TXT_SEC)
        self.uv_lbl    = L("UV Index  —", 11, color=TXT_SEC)
        rhs.addWidget(self.feels_lbl)
        rhs.addWidget(self.uv_lbl)
        mid.addLayout(rhs)
        hl.addLayout(mid)
        hl.addStretch()

        # Row: sunrise (left) + sunset (right)
        sun = QHBoxLayout()
        self.sr_lbl = L("🌅  —", 11, color=WARN)
        self.ss_lbl = L("—  🌇", 11, color="#ff8a65",
                        align=Qt.AlignmentFlag.AlignRight)
        sun.addWidget(self.sr_lbl)
        sun.addStretch()
        sun.addWidget(self.ss_lbl)
        hl.addLayout(sun)
        lay.addWidget(hero)

        # ── Stat pills 2x2 grid ───────────────────────────────────────────────
        # humidity | wind
        # pressure | visibility
        grid = QGridLayout()
        grid.setSpacing(10)
        self.pills = {
            "humidity":   Pill("💧", "Humidity",   "—"),
            "wind":       Pill("💨", "Wind",        "—"),
            "pressure":   Pill("🌡", "Pressure",   "—"),
            "visibility": Pill("👁", "Visibility", "—"),
        }
        for i, w in enumerate(self.pills.values()):
            grid.addWidget(w, i // 2, i % 2)
        lay.addLayout(grid)

        # ── Alert banner ──────────────────────────────────────────────────────
        # Hidden by default. Shown automatically by load_data() when any
        # threshold is exceeded (temp >= 40C, wind >= 50 km/h, etc.)
        self.alert = Frost(r=12)
        al = QHBoxLayout(self.alert)
        al.setContentsMargins(16, 10, 16, 10)
        al.setSpacing(10)
        warn_icon = L("⚠️", 14)
        warn_icon.setFixedWidth(24)
        al.addWidget(warn_icon)
        self.alert_lbl = L("", 11, color="#ff8a80")
        self.alert_lbl.setWordWrap(True)
        al.addWidget(self.alert_lbl, 1)
        self.alert.hide()   # starts hidden
        lay.addWidget(self.alert)

        # ── Hourly forecast horizontal scroll ─────────────────────────────────
        # HChip widgets are added dynamically in load_data() — not built here
        lay.addWidget(L("  Hourly Forecast", 12, bold=True, color=ACC))
        hs = QScrollArea()
        hs.setMinimumHeight(125)
        hs.setMaximumHeight(125)
        hs.setFrameShape(QFrame.Shape.NoFrame)
        hs.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        hs.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        hs.setStyleSheet("background:transparent; border:none;")
        hs.horizontalScrollBar().setStyleSheet(
            "QScrollBar:horizontal{background:transparent;height:4px;}"
            "QScrollBar::handle:horizontal{background:rgba(79,195,247,40);border-radius:2px;}"
            "QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{width:0px;}"
        )
        hw = QWidget()
        hw.setStyleSheet("background:transparent;")
        hw.setFixedHeight(112)
        self._hrow = QHBoxLayout(hw)   # chips are inserted here at runtime
        self._hrow.setSpacing(8)
        self._hrow.setContentsMargins(4, 2, 4, 2)
        hs.setWidget(hw)
        hs.setWidgetResizable(False)
        lay.addWidget(hs)
        self._hs = hs  # kept as reference to read its width in load_data()

        # ── 7-day forecast card ───────────────────────────────────────────────
        # FRow widgets are added dynamically in load_data() — not built here
        lay.addWidget(L("  7-Day Forecast", 12, bold=True, color=ACC))
        self._fc = Frost(r=18)
        self._fl = QVBoxLayout(self._fc)   # rows are inserted here at runtime
        self._fl.setContentsMargins(8, 10, 8, 10)
        self._fl.setSpacing(4)
        lay.addWidget(self._fc)
        lay.addStretch()

    # ── BACKEND HOOK ──────────────────────────────────────────────────────────
    def _fetch(self):
        """
        Triggered when the user presses Search or hits Enter.

        BACKEND TEAM: Replace the body of this method with your API call.
        When the data is ready, call:

            self.load_data(data)        # data dict — see class docstring
            self.show_error("message")  # on failure

        If using a background thread (recommended for network calls), emit
        a signal from the thread and connect it to self.load_data here.

        Example skeleton:
            city = self.search.text().strip()
            if not city:
                return
            self.show_loading()
            thread = WeatherFetcher(city)
            thread.success.connect(self.load_data)
            thread.failure.connect(self.show_error)
            thread.start()
        """
        city = self.search.text().strip()
        if not city:
            return
        self.show_loading()
        # TODO: replace with real backend call
        # self.load_data( <data_from_backend> )

    def show_loading(self):
        """Show a fetching indicator. Call before starting a backend request."""
        self.status.setStyleSheet(f"color:{ACC};")
        self.status.setText("Fetching weather data…")

    def show_error(self, message: str):
        """Display an error message under the search bar."""
        self.status.setStyleSheet(f"color:{DANGER};")
        self.status.setText(message)

    # ── BACKEND HOOK ──────────────────────────────────────────────────────────
    def load_data(self, data: dict):
        """
        Populate every widget with live data from the backend.

        This is the single entry point for all data on this tab.
        See the class docstring for the full expected dict schema.
        Called by the backend (or its signal) once data is available.
        """
        # clear status
        self.status.setText("")

        # ── hero card ─────────────────────────────────────────────────────────
        self.city_lbl.setText(f"📍 {data['city']}, {data['country']}")
        self.date_lbl.setText(datetime.now().strftime("%a %d %b %Y"))
        self.cond_lbl.setText(data["condition"])
        self.icon_lbl.setText(data["icon"])
        self.temp_lbl.setText(f"{data['temp']}°C")
        self.feels_lbl.setText(f"Feels like  {data['feels_like']}°C")
        self.uv_lbl.setText(f"UV Index  {data['uv_index']}")
        self.sr_lbl.setText(f"🌅  {data['sunrise']}")
        self.ss_lbl.setText(f"{data['sunset']}  🌇")

        # ── stat pills ────────────────────────────────────────────────────────
        self.pills["humidity"].set(f"{data['humidity']}%")
        self.pills["wind"].set(f"{data['wind']} km/h")
        self.pills["pressure"].set(f"{data['pressure']} hPa")
        self.pills["visibility"].set(f"{data['visibility']} km")

        # ── hourly chips — clear old widgets then rebuild from fresh data ──────
        while self._hrow.count():
            item = self._hrow.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for h in data.get("hourly", []):
            self._hrow.addWidget(HChip(h["time"], h["icon"], h["temp"]))
        # expand the inner container so the scroll area can actually scroll
        chip_w  = 82; gap = 8
        count   = len(data.get("hourly", []))
        total_w = count * (chip_w + gap) + 8
        self._hrow.parentWidget().setFixedWidth(max(total_w, self._hs.width()))

        # ── forecast rows — clear old widgets then rebuild from fresh data ─────
        while self._fl.count():
            item = self._fl.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for i, f in enumerate(data.get("forecast", [])):
            self._fl.addWidget(
                FRow(f["day"], f["icon"], f["high"], f["low"], f["rain"]))
            if i < len(data["forecast"]) - 1:
                # thin divider line between rows
                ln = QFrame()
                ln.setFrameShape(QFrame.Shape.HLine)
                ln.setStyleSheet("color:rgba(79,195,247,14);")
                self._fl.addWidget(ln)

        # ── alert banner — auto-shown when any threshold is exceeded ──────────
        alerts = []
        if data["temp"]     >= 40: alerts.append("🔥 Extreme heat")
        if data["wind"]     >= 50: alerts.append("💨 High winds")
        if data["humidity"] >= 90: alerts.append("💧 Very high humidity")
        if data["uv_index"] >= 8:  alerts.append("☀️  High UV")
        if alerts:
            self.alert_lbl.setText("  ·  ".join(alerts))
            self.alert.show()
        else:
            self.alert.hide()


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — COMPARE
# ═══════════════════════════════════════════════════════════════════════════════
class CompareTab(QWidget):
    """
    Side-by-side comparison of two cities with a bar chart.

    Layout:
      • Two city inputs + Compare button
      • Two city cards  (name, icon, temp, condition, stats)
      • VS label between the cards
      • Matplotlib bar chart  (temp, humidity, wind, UV)
      • Summary banner  (who is hotter / windier / more humid)

    ── BACKEND HOOK ──────────────────────────────────────────────────────────
    Call  CompareTab.load_city1(city_name, data)
    and   CompareTab.load_city2(city_name, data)

    Each data dict uses the same schema as CurrentTab.load_data() but only
    these fields are required here:

        {
            "temp":       float,
            "feels_like": float,
            "humidity":   int,
            "pressure":   int,
            "wind":       float,
            "visibility": float,
            "condition":  str,
            "icon":       str,
            "uv_index":   float,
        }

    The chart and summary banner draw automatically once both cities are loaded.
    You can call them in any order — the draw only fires when both are ready.
    Replace the body of _compare() with your two backend calls.
    ──────────────────────────────────────────────────────────────────────────
    """

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Store city data tuples — both must be set before the chart draws
        self._d1 = None   # (city_name, data_dict) for city 1
        self._d2 = None   # (city_name, data_dict) for city 2
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)
        lay.addWidget(L("Compare Two Cities", 16, bold=True, color=ACC,
                        align=Qt.AlignmentFlag.AlignCenter))

        # ── Search inputs ─────────────────────────────────────────────────────
        row = QHBoxLayout(); row.setSpacing(8)
        self.c1 = QLineEdit(); self.c1.setPlaceholderText("City 1")
        self.c2 = QLineEdit(); self.c2.setPlaceholderText("City 2")
        for e in (self.c1, self.c2):
            e.setFixedHeight(42); e.setFont(QFont(FONT, 12)); e.setStyleSheet(SS)
        btn = QPushButton("Compare")
        btn.setFixedHeight(42); btn.setFont(QFont(FONT, 12)); btn.setStyleSheet(BSS)
        btn.clicked.connect(self._compare)
        row.addWidget(self.c1); row.addWidget(self.c2); row.addWidget(btn)
        lay.addLayout(row)

        self.status = L("", 10, color=DANGER, align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.status)

        # ── City cards ────────────────────────────────────────────────────────
        cards = QHBoxLayout(); cards.setSpacing(12)
        self.cd1 = self._mk_card()   # left card — filled by load_city1()
        self.cd2 = self._mk_card()   # right card — filled by load_city2()
        vs = L("VS", 20, bold=True, color=TXT_DIM,
               align=Qt.AlignmentFlag.AlignCenter)
        vs.setFixedWidth(38)
        cards.addWidget(self.cd1); cards.addWidget(vs); cards.addWidget(self.cd2)
        lay.addLayout(cards)

        # ── Bar chart ─────────────────────────────────────────────────────────
        # FigureCanvas renders a matplotlib Figure inline as a Qt widget.
        # The chart is redrawn from scratch every time both cities are loaded.
        self.fig    = Figure(figsize=(6, 2.8), facecolor="none")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background:transparent;")
        self.canvas.setMinimumHeight(200)
        lay.addWidget(self.canvas)

        # ── Summary banner (hidden until both cities are loaded) ──────────────
        self.banner = Frost(r=12)
        bl = QHBoxLayout(self.banner)
        bl.setContentsMargins(16, 10, 16, 10)
        self.blbl = L("", 11, color=TXT_SEC, align=Qt.AlignmentFlag.AlignCenter)
        self.blbl.setWordWrap(True)
        bl.addWidget(self.blbl)
        self.banner.hide()
        lay.addWidget(self.banner)
        lay.addStretch()

    def _mk_card(self):
        """Build an empty city card. Internal helper — not a backend hook."""
        c  = Frost(r=16)
        cl = QVBoxLayout(c)
        cl.setContentsMargins(14, 14, 14, 14)
        cl.setSpacing(6)
        c._n = L("—", 13, bold=True, align=Qt.AlignmentFlag.AlignCenter)
        c._i = QLabel("🌐")
        c._i.setFont(QFont(FONT, 38))
        c._i.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c._i.setStyleSheet("background:transparent;")
        c._t = L("—°C", 26, bold=True, align=Qt.AlignmentFlag.AlignCenter)
        c._c = L("—", 10, color=TXT_SEC, align=Qt.AlignmentFlag.AlignCenter)
        c._s = L("", 10, color=TXT_DIM,  align=Qt.AlignmentFlag.AlignCenter)
        c._s.setWordWrap(True)
        for w in (c._n, c._i, c._t, c._c, c._s):
            cl.addWidget(w)
        return c

    def _fill_card(self, card, city: str, data: dict):
        """Populate a city card with data. Internal helper."""
        card._n.setText(city)
        card._i.setText(data["icon"])
        card._t.setText(f"{data['temp']}°C")
        card._c.setText(data["condition"])
        card._s.setText(
            f"💧{data['humidity']}%  💨{data['wind']} km/h\n"
            f"🌡{data['pressure']} hPa  👁{data['visibility']} km"
        )

    # ── BACKEND HOOK ──────────────────────────────────────────────────────────
    def _compare(self):
        """
        Triggered when the user clicks Compare.

        BACKEND TEAM: Replace the body with two backend calls, one per city.
        When each call finishes, call the corresponding load method:

            self.load_city1(city_name, data_dict)
            self.load_city2(city_name, data_dict)

        Both calls can run in parallel (threads) — order does not matter.
        The chart only draws once both are set.

        Example skeleton:
            c1 = self.c1.text().strip()
            c2 = self.c2.text().strip()
            if not c1 or not c2:
                self.status.setText("Enter both cities.")
                return
            self.show_loading()
            thread1 = WeatherFetcher(c1)
            thread1.success.connect(lambda d, n: self.load_city1(n, d))
            thread2 = WeatherFetcher(c2)
            thread2.success.connect(lambda d, n: self.load_city2(n, d))
            thread1.start(); thread2.start()
        """
        c1 = self.c1.text().strip()
        c2 = self.c2.text().strip()
        if not c1 or not c2:
            self.status.setText("Enter both cities.")
            return
        self.show_loading()
        # Reset previous results so stale data is not shown while fetching
        self._d1 = None
        self._d2 = None
        # TODO: replace with real backend calls
        # self.load_city1(c1, <data_from_backend>)
        # self.load_city2(c2, <data_from_backend>)

    def show_loading(self):
        """Show a fetching indicator."""
        self.status.setStyleSheet(f"color:{ACC};")
        self.status.setText("Fetching…")

    def show_error(self, message: str):
        """Display an error under the inputs."""
        self.status.setStyleSheet(f"color:{DANGER};")
        self.status.setText(message)

    # ── BACKEND HOOK ──────────────────────────────────────────────────────────
    def load_city1(self, city: str, data: dict):
        """
        Load data for the left city card.
        See class docstring for the required data dict fields.
        The chart redraws automatically once both cities are loaded.
        """
        self._d1 = (city, data)
        self._fill_card(self.cd1, city, data)
        self._try_draw()

    # ── BACKEND HOOK ──────────────────────────────────────────────────────────
    def load_city2(self, city: str, data: dict):
        """
        Load data for the right city card.
        See class docstring for the required data dict fields.
        The chart redraws automatically once both cities are loaded.
        """
        self._d2 = (city, data)
        self._fill_card(self.cd2, city, data)
        self._try_draw()

    def _try_draw(self):
        """Draw chart only when both cities have been loaded. Internal."""
        if not (self._d1 and self._d2):
            return   # still waiting for the other city
        self.status.setText("")
        c1, d1 = self._d1
        c2, d2 = self._d2

        # ── bar chart: 4 metrics side by side ─────────────────────────────────
        metrics = ["Temp °C", "Humidity", "Wind", "UV"]
        v1 = [d1["temp"], d1["humidity"], d1["wind"], d1["uv_index"]]
        v2 = [d2["temp"], d2["humidity"], d2["wind"], d2["uv_index"]]
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.fig.patch.set_alpha(0)
        ax.set_facecolor("#ffffff04")
        x  = np.arange(len(metrics)); bw = 0.32
        b1 = ax.bar(x - bw/2, v1, bw, label=c1, color="#4fc3f7", alpha=0.82, zorder=3)
        b2 = ax.bar(x + bw/2, v2, bw, label=c2, color="#26c6da", alpha=0.82, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, color=TXT_SEC, fontsize=9)
        ax.tick_params(axis="y", colors=TXT_SEC, labelsize=8)
        ax.spines[:].set_visible(False)
        ax.yaxis.grid(True, color="#ffffff0c", zorder=0)
        ax.legend(facecolor="#060f1e", edgecolor="#1a3a5a",
                  labelcolor=TXT_PRI, fontsize=9)
        # value labels sitting on top of each bar
        for b in (*b1, *b2):
            h = b.get_height()
            ax.text(b.get_x() + b.get_width()/2, h + .3, f"{h:.0f}",
                    ha="center", va="bottom", color=TXT_SEC, fontsize=8)
        self.canvas.draw()

        # ── summary banner ────────────────────────────────────────────────────
        ht = c1 if d1["temp"]     > d2["temp"]     else c2
        wd = c1 if d1["wind"]     > d2["wind"]     else c2
        hm = c1 if d1["humidity"] > d2["humidity"] else c2
        self.blbl.setText(
            f"🌡 Hotter: {ht} ({max(d1['temp'], d2['temp'])}°C)   "
            f"·   💨 Windier: {wd}   ·   💧 More humid: {hm}"
        )
        self.banner.show()


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
class HistoryTab(QWidget):
    """
    30-day historical weather table for a selected city.

    Layout:
      • City dropdown + Load button
      • Hottest / Coldest day cards
      • Scrollable table  (date, temp, humidity, pressure, wind, condition)
      • Export to CSV button

    ── BACKEND HOOK ──────────────────────────────────────────────────────────
    Two entry points:

    1.  HistoryTab.set_cities(["City A", "City B", ...])
        Call at startup (or after any search) to populate the dropdown.

    2.  HistoryTab.load_history(rows)
        Call when the user clicks Load. Pass a list of row tuples:

            rows = [
                (date_str, temp, humidity, pressure, wind, condition),
                ...
            ]
            # date_str : "YYYY-MM-DD"
            # temp     : float  (Celsius)
            # humidity : int    (%)
            # pressure : int    (hPa)
            # wind     : float  (km/h)
            # condition: str

        Rows can be in any order. Hottest/coldest are computed automatically.
    ──────────────────────────────────────────────────────────────────────────
    """

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)
        lay.addWidget(L("Weather History", 16, bold=True, color=ACC,
                        align=Qt.AlignmentFlag.AlignCenter))

        # ── City selector ─────────────────────────────────────────────────────
        row = QHBoxLayout(); row.setSpacing(8)
        self.combo = QComboBox()
        self.combo.setFixedHeight(38)
        self.combo.setFont(QFont(FONT, 11))
        self.combo.setStyleSheet(CSS)
        btn = QPushButton("Load")
        btn.setFixedHeight(38); btn.setFont(QFont(FONT, 11)); btn.setStyleSheet(BSS)
        btn.clicked.connect(self._load)
        row.addWidget(L("City:", 11)); row.addWidget(self.combo); row.addWidget(btn)
        lay.addLayout(row)

        # ── Hottest / Coldest summary cards ───────────────────────────────────
        hc = QHBoxLayout(); hc.setSpacing(12)
        self.hot  = self._mk_extreme_card("🔥", "Hottest Day", DANGER)
        self.cold = self._mk_extreme_card("🧊", "Coldest Day", ACC)
        hc.addWidget(self.hot); hc.addWidget(self.cold)
        lay.addLayout(hc)

        # ── History table ─────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Temp °C", "Humidity", "Pressure", "Wind", "Condition"])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background:rgba(5,13,26,175);
                border:1px solid rgba(79,195,247,28);
                border-radius:12px; color:{TXT_PRI};
                gridline-color:rgba(79,195,247,10);
            }}
            QHeaderView::section {{
                background:rgba(79,195,247,16); color:{ACC};
                border:none; padding:6px;
                font-size:10px; font-weight:bold;
            }}
            QTableWidget::item:alternate {{background:rgba(79,195,247,5);}}
            QScrollBar:vertical {{background:transparent; width:6px;}}
            QScrollBar::handle:vertical {{
                background:rgba(79,195,247,38); border-radius:3px;}}
        """)
        lay.addWidget(self.table)

        # ── Export button ─────────────────────────────────────────────────────
        # Exports whatever is currently shown in the table to CSV
        exp = QPushButton("📥  Export to CSV")
        exp.setFixedHeight(36); exp.setFont(QFont(FONT, 11)); exp.setStyleSheet(BSS)
        exp.clicked.connect(self._export)
        lay.addWidget(exp, alignment=Qt.AlignmentFlag.AlignRight)

    def _mk_extreme_card(self, emoji, title, color):
        """Build a hottest/coldest summary card. Internal helper."""
        c  = Frost(r=14)
        cl = QVBoxLayout(c)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(4)
        hr = QHBoxLayout()
        el = QLabel(emoji)
        el.setFont(QFont(FONT, 16))
        el.setStyleSheet("background:transparent;")
        hr.addWidget(el)
        hr.addWidget(L(title, 11, color=color))
        hr.addStretch()
        c._t = L("—", 22, bold=True, color=color)  # temperature value
        c._d = L("—", 9,  color=TXT_DIM)            # date
        c._c = L("—", 10, color=TXT_SEC)            # condition string
        cl.addLayout(hr)
        cl.addWidget(c._t)
        cl.addWidget(c._d)
        cl.addWidget(c._c)
        return c

    # ── BACKEND HOOK ──────────────────────────────────────────────────────────
    def set_cities(self, cities: list):
        """
        Populate the city dropdown.

        Call once at startup with the list of cities that have stored history,
        then again whenever a new city is searched on the Current tab.

            main_window.th.set_cities(["Mumbai", "London", "Tokyo"])
        """
        self.combo.clear()
        for city in cities:
            self.combo.addItem(city)

    # ── BACKEND HOOK ──────────────────────────────────────────────────────────
    def _load(self):
        """
        Triggered when the user clicks Load.

        BACKEND TEAM: Replace the body with a DB/API call for the selected city.
        When data arrives, call:

            self.load_history(rows)

        Example skeleton:
            city = self.combo.currentText()
            if not city: return
            rows = db.get_history(city, days=30)
            self.load_history(rows)
        """
        city = self.combo.currentText()
        if not city:
            return
        # TODO: replace with real backend call
        # rows = backend.get_history(city)
        # self.load_history(rows)

    # ── BACKEND HOOK ──────────────────────────────────────────────────────────
    def load_history(self, rows: list):
        """
        Populate the table and extreme-day cards.

        rows: list of tuples —
            (date_str, temp, humidity, pressure, wind, condition)

        Hottest and coldest cards are derived automatically from the rows.
        """
        # fill table
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)

        # derive and fill hottest / coldest cards
        if rows:
            hot  = max(rows, key=lambda x: x[1])
            cold = min(rows, key=lambda x: x[1])
            self.hot._t.setText(f"{hot[1]}°C")
            self.hot._d.setText(hot[0])
            self.hot._c.setText(hot[5])
            self.cold._t.setText(f"{cold[1]}°C")
            self.cold._d.setText(cold[0])
            self.cold._c.setText(cold[5])

    def _export(self):
        """Export the current table contents to a user-chosen CSV file."""
        city = self.combo.currentText()
        if not city:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", f"{city}_weather.csv", "CSV files (*.csv)")
        if not path:
            return
        import csv
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Temp", "Humidity", "Pressure", "Wind", "Condition"])
            # read from the table widget so export always matches what the user sees
            for r in range(self.table.rowCount()):
                writer.writerow([
                    self.table.item(r, c).text()
                    for c in range(self.table.columnCount())
                ])
        QMessageBox.information(self, "Done", f"Saved:\n{path}")


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 4 — TRENDS
# ═══════════════════════════════════════════════════════════════════════════════
class TrendsTab(QWidget):
    """
    Line chart of a chosen weather metric over the last 30 days.

    Layout:
      • City dropdown + Metric dropdown + Plot button
      • Matplotlib line chart  (shaded area + linear trend line)
      • 4 stat pills  (30-day avg, max, min, trend slope per day)

    ── BACKEND HOOK ──────────────────────────────────────────────────────────
    Two entry points:

    1.  TrendsTab.set_cities(["City A", "City B", ...])
        Populate the city dropdown. Call at startup and after each new search.

    2.  TrendsTab.load_trends(rows)
        Call when the user clicks Plot. Pass rows in oldest-first order:

            rows = [
                (date_str, temp, humidity, pressure, wind, condition),
                ...
            ]

        The tab reads the column matching the selected metric automatically —
        always pass all columns regardless of which metric is selected.

    Replace the body of _plot() with your backend call.
    ──────────────────────────────────────────────────────────────────────────
    """

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._rows = []   # cached rows — reused when only the metric changes
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)
        lay.addWidget(L("Trend Analysis", 16, bold=True, color=ACC,
                        align=Qt.AlignmentFlag.AlignCenter))

        # ── Controls row ──────────────────────────────────────────────────────
        ctrl = QHBoxLayout(); ctrl.setSpacing(8)
        self.cc = QComboBox()   # city selector — populated by set_cities()
        self.cc.setFixedHeight(36); self.cc.setStyleSheet(CSS); self.cc.setFont(QFont(FONT, 11))
        self.mc = QComboBox()   # metric selector — static options
        self.mc.addItems(["Temperature", "Humidity", "Pressure", "Wind Speed"])
        self.mc.setFixedHeight(36); self.mc.setStyleSheet(CSS); self.mc.setFont(QFont(FONT, 11))
        btn = QPushButton("Plot")
        btn.setFixedHeight(36); btn.setStyleSheet(BSS); btn.setFont(QFont(FONT, 11))
        btn.clicked.connect(self._plot)
        ctrl.addWidget(L("City:", 11)); ctrl.addWidget(self.cc)
        ctrl.addWidget(L("Metric:", 11)); ctrl.addWidget(self.mc)
        ctrl.addWidget(btn)
        lay.addLayout(ctrl)

        # ── Matplotlib chart ──────────────────────────────────────────────────
        # FigureCanvas renders inline as a Qt widget.
        # Redrawn from scratch on every Plot click.
        self.fig    = Figure(figsize=(7, 3.2), facecolor="none")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background:transparent;")
        lay.addWidget(self.canvas)

        # ── Stat pills row ────────────────────────────────────────────────────
        pr = QHBoxLayout(); pr.setSpacing(10)
        self.pa  = Pill("📊", "30-Day Avg", "—")
        self.pmx = Pill("⬆️",  "Max",        "—")
        self.pmn = Pill("⬇️",  "Min",        "—")
        self.pt  = Pill("📈", "Trend",      "—")
        for p in (self.pa, self.pmx, self.pmn, self.pt):
            pr.addWidget(p)
        lay.addLayout(pr)
        lay.addStretch()

    # ── BACKEND HOOK ──────────────────────────────────────────────────────────
    def set_cities(self, cities: list):
        """
        Populate the city dropdown.
        Call alongside HistoryTab.set_cities() — they share the same city list.

            main_window.tt.set_cities(["Mumbai", "London", "Tokyo"])
        """
        self.cc.clear()
        for city in cities:
            self.cc.addItem(city)

    # ── BACKEND HOOK ──────────────────────────────────────────────────────────
    def _plot(self):
        """
        Triggered when the user clicks Plot.

        BACKEND TEAM: Replace the body with a DB/API call for the selected city.
        When data arrives, call:

            self.load_trends(rows)

        Optimisation tip: if the user only changed the metric dropdown
        (not the city), you can skip the network call entirely and just
        call self._render() directly — the rows are already cached in self._rows.

        Example skeleton:
            city = self.cc.currentText()
            if not city: return
            rows = db.get_history(city, days=30)   # oldest first
            self.load_trends(rows)
        """
        city = self.cc.currentText()
        if not city:
            return
        # If we already have rows cached, just re-render with the new metric
        if self._rows:
            self._render()
        # TODO: otherwise fetch from backend and call self.load_trends(rows)

    # ── BACKEND HOOK ──────────────────────────────────────────────────────────
    def load_trends(self, rows: list):
        """
        Cache the rows and render the chart immediately.

        rows: list of tuples, oldest first —
            (date_str, temp, humidity, pressure, wind, condition)
        """
        self._rows = rows
        self._render()

    def _render(self):
        """
        Draw the line chart for the currently selected metric.
        Called internally — do not call this directly from the backend.
        Use load_trends() instead.
        """
        rows = self._rows
        if not rows:
            return

        metric = self.mc.currentText()

        # Maps metric name to: (column index in tuple, unit string, line colour)
        cm = {
            "Temperature": (1, "°C",    "#4fc3f7"),
            "Humidity":    (2, "%",     "#26c6da"),
            "Pressure":    (3, " hPa",  "#ffb74d"),
            "Wind Speed":  (4, " km/h", "#66bb6a"),
        }
        col, unit, color = cm[metric]
        dates  = [r[0][-5:] for r in rows]   # slice to "MM-DD" for x-axis labels
        values = [r[col]    for r in rows]

        # ── draw chart ────────────────────────────────────────────────────────
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.fig.patch.set_alpha(0)
        ax.set_facecolor("#ffffff04")

        # shaded area under the line for visual depth
        ax.fill_between(range(len(values)), values, alpha=0.14, color=color)

        # main line with small dot markers at each data point
        ax.plot(range(len(values)), values, color=color,
                linewidth=2, marker="o", markersize=3.5, zorder=4)

        # dashed linear trend line — only when we have enough data points
        if len(values) > 2:
            z = np.polyfit(range(len(values)), values, 1)
            poly = np.poly1d(z)
            ax.plot(range(len(values)), poly(range(len(values))),
                    "--", color="#ffffff28", linewidth=1.2, zorder=3)
            slope = z[0]   # positive = rising trend, negative = falling
            trend = f"↑ +{slope:.2f}{unit}/day" if slope > 0 else f"↓ {slope:.2f}{unit}/day"
        else:
            trend = "N/A"

        # x-axis: show at most 6 date labels to avoid crowding
        step  = max(1, len(dates) // 6)
        ticks = list(range(0, len(dates), step))
        ax.set_xticks(ticks)
        ax.set_xticklabels([dates[i] for i in ticks],
                           color=TXT_SEC, fontsize=8, rotation=30)
        ax.tick_params(axis="y", colors=TXT_SEC, labelsize=8)
        ax.spines[:].set_visible(False)
        ax.yaxis.grid(True, color="#ffffff0c", zorder=0)
        ax.set_title(
            f"{self.cc.currentText()} — {metric} (last {len(values)} days)",
            color=ACC, fontsize=10, pad=8)
        self.canvas.draw()

        # ── update stat pills below the chart ─────────────────────────────────
        avg_ = sum(values) / len(values)
        self.pa.set(f"{avg_:.1f}{unit}")
        self.pmx.set(f"{max(values):.1f}{unit}")
        self.pmn.set(f"{min(values):.1f}{unit}")
        self.pt.set(trend)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    """
    Application shell. Owns the Aurora background and the QTabWidget.

    ── BACKEND HOOK ──────────────────────────────────────────────────────────
    All four tab instances are public attributes so the backend/controller
    layer can reach any hook without subclassing:

        main_window.tc   — CurrentTab
        main_window.tcm  — CompareTab
        main_window.th   — HistoryTab
        main_window.tt   — TrendsTab

    After a city is successfully fetched on the Current tab, refresh the
    History and Trends dropdowns so the new city appears there immediately:

        cities = backend.get_all_cities()
        main_window.th.set_cities(cities)
        main_window.tt.set_cities(cities)
    ──────────────────────────────────────────────────────────────────────────
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather Forecast")
        self.setMinimumSize(800, 860)

        # Aurora is the central widget; all tabs are layered on top of it
        bg = Aurora()
        self.setCentralWidget(bg)
        outer = QVBoxLayout(bg)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Tab widget ────────────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ background:transparent; border:none; }}
            QTabBar {{ background:transparent; }}
            QTabBar::tab {{
                background:rgba(5,13,26,165); color:{TXT_DIM};
                border:1px solid rgba(79,195,247,18); border-radius:10px;
                padding:9px 20px; margin:6px 3px 0 3px; font:12px '{FONT}';
            }}
            QTabBar::tab:selected {{
                background:rgba(79,195,247,18); color:{ACC};
                border:1px solid rgba(79,195,247,65);
            }}
            QTabBar::tab:hover {{ background:rgba(79,195,247,10); color:{TXT_SEC}; }}
            QScrollBar:vertical {{ background:transparent; width:6px; }}
            QScrollBar::handle:vertical {{
                background:rgba(79,195,247,35); border-radius:3px; }}
        """)
        outer.addWidget(tabs)

        # Instantiate tabs — stored as public attributes for backend access
        self.tc  = CurrentTab()
        self.tcm = CompareTab()
        self.th  = HistoryTab()
        self.tt  = TrendsTab()

        tabs.addTab(self.tc,  "🌤  Current")
        tabs.addTab(self.tcm, "🔀  Compare")
        tabs.addTab(self.th,  "📋  History")
        tabs.addTab(self.tt,  "📈  Trends")


# ═══════════════════════════════════════════════════════════════════════════════
#  SPLASH SCREEN
#  Shown first when the app launches. Clicking "Get Started" opens MainWindow.
# ═══════════════════════════════════════════════════════════════════════════════
class SplashBg(QWidget):
    """
    Animated warm sunset background for the splash screen.

    Draws a gradient that shifts between deep purple, warm rose, and
    soft amber — mimicking the golden-hour cloudy sky in the design.
    Two soft radial blobs drift slowly to add depth, similar to Aurora
    but in warm tones instead of cool blues.
    """

    def __init__(self):
        super().__init__()
        self._t = 0.0
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(50)   # 20 fps — same rhythm as Aurora

    def _tick(self):
        self._t += 0.5
        self.update()

    def paintEvent(self, e):
        import math
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # ── base sunset gradient (top: deep purple → mid: rose → bottom: amber)
        base = QLinearGradient(0, 0, 0, h)
        base.setColorAt(0.00, QColor(72,  40,  90))   # deep purple top
        base.setColorAt(0.35, QColor(160,  70,  90))  # dusty rose
        base.setColorAt(0.65, QColor(210, 110,  70))  # warm orange
        base.setColorAt(1.00, QColor(180,  80,  60))  # burnt sienna bottom
        p.fillRect(self.rect(), base)

        # ── blob 1: golden glow, drifts upper-centre ──────────────────────────
        bx = w * 0.55 + math.sin(math.radians(self._t * 0.4)) * 80
        by = h * 0.25 + math.cos(math.radians(self._t * 0.3)) * 40
        g  = QRadialGradient(bx, by, 420)
        g.setColorAt(0.00, QColor(240, 160,  60, 55))
        g.setColorAt(0.50, QColor(200, 100,  50, 22))
        g.setColorAt(1.00, QColor(0,     0,   0,  0))
        pp = QPainterPath()
        pp.addEllipse(bx - 420, by - 300, 840, 600)
        p.fillPath(pp, g)

        # ── blob 2: soft pink, drifts lower-left ──────────────────────────────
        bx2 = w * 0.25 + math.cos(math.radians(self._t * 0.35)) * 70
        by2 = h * 0.70 + math.sin(math.radians(self._t * 0.28)) * 50
        g2  = QRadialGradient(bx2, by2, 320)
        g2.setColorAt(0.00, QColor(180,  80, 120, 45))
        g2.setColorAt(0.55, QColor(130,  50,  90, 18))
        g2.setColorAt(1.00, QColor(0,     0,   0,  0))
        pp2 = QPainterPath()
        pp2.addEllipse(bx2 - 320, by2 - 240, 640, 480)
        p.fillPath(pp2, g2)

        # ── soft vignette overlay (darkens edges for depth) ───────────────────
        vig = QRadialGradient(w / 2, h / 2, max(w, h) * 0.75)
        vig.setColorAt(0.0, QColor(0, 0, 0,   0))
        vig.setColorAt(1.0, QColor(0, 0, 0,  90))
        pp3 = QPainterPath()
        pp3.addRect(0, 0, w, h)
        p.fillPath(pp3, vig)


class SplashScreen(QMainWindow):
    """
    Welcome screen shown before the main app.

    Layout (vertically centred over the sunset background):
      • App name  "Mausam"  in large elegant serif
      • Tagline subtitle
      • "Get Started" button  → hides splash, opens MainWindow

    The name "Mausam" means "weather" / "season" in Hindi/Urdu.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mausam")
        self.setMinimumSize(860, 500)
        self.setFixedSize(860, 500)   # splash is fixed size — not resizable

        # ── background ────────────────────────────────────────────────────────
        bg = SplashBg()
        self.setCentralWidget(bg)

        # ── content layer centred over the background ─────────────────────────
        outer = QVBoxLayout(bg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(2)   # push content toward vertical centre

        # ── App name ──────────────────────────────────────────────────────────
        name = QLabel("Mausam")
        name_font = QFont("Georgia", 58)   # serif — elegant, close to the design
        name_font.setBold(True)
        name_font.setItalic(True)
        name.setFont(name_font)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("""
            color: white;
            background: transparent;
            letter-spacing: 3px;
        """)
        outer.addWidget(name)

        outer.addSpacing(18)

        # ── Tagline ───────────────────────────────────────────────────────────
        tagline = QLabel(
            "Welcome to Mausam — a platform to get the real-time\n"
            "weather updates of any location of your choice, anytime!"
        )
        tag_font = QFont("Georgia", 12)
        tagline.setFont(tag_font)
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet("""
            color: rgba(255, 240, 230, 210);
            background: transparent;
            line-height: 1.6;
        """)
        outer.addWidget(tagline)

        outer.addSpacing(42)

        # ── Get Started button ────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn = QPushButton("Get Started")
        self.btn.setFixedSize(160, 44)
        self.btn.setFont(QFont("Georgia", 12))
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setStyleSheet("""
            QPushButton {
                background: rgba(40, 30, 60, 200);
                color: white;
                border: 1.5px solid rgba(255, 255, 255, 80);
                border-radius: 6px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(60, 45, 85, 220);
                border: 1.5px solid rgba(255, 255, 255, 140);
            }
            QPushButton:pressed {
                background: rgba(25, 18, 45, 220);
            }
        """)
        self.btn.clicked.connect(self._launch)
        btn_row.addWidget(self.btn)
        btn_row.addStretch()
        outer.addLayout(btn_row)

        outer.addStretch(3)   # slightly more space below for visual balance

        # ── subtle footer ─────────────────────────────────────────────────────
        footer = QLabel("Real-time weather · Trends · History · Compare")
        footer.setFont(QFont("Segoe UI", 8))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: rgba(255,220,200,100); background:transparent;")
        outer.addWidget(footer)
        outer.addSpacing(14)

    def _launch(self):
        """
        Called when the user clicks Get Started.
        Opens the main weather app window and closes the splash.
        """
        self._main = MainWindow()   # keep a reference so it isn't garbage collected
        self._main.show()
        self.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
app = QApplication(sys.argv)
app.setStyle("Fusion")
splash = SplashScreen()
splash.show()
sys.exit(app.exec())
