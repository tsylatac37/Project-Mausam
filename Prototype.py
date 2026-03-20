import sys
from datetime import datetime

from PySide6.QtWidgets import *
from PySide6.QtCore    import Qt
from PySide6.QtGui     import (QPainter, QColor, QFont, QLinearGradient,
                                QPen, QPainterPath, QRadialGradient, QTimer)

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
#  PALETTE
# ─────────────────────────────────────────────────────────────────────────────
BG_CARD   = QColor(10, 22, 44, 165)
BORDER    = QColor(90, 170, 255, 40)
BORDER_HI = QColor(110, 195, 255, 85)
ACC       = "#4fc3f7"
TXT_PRI   = "#e8f4fd"
TXT_SEC   = "#7bafd4"
TXT_DIM   = "#2e5070"
DANGER    = "#ef5350"
WARN      = "#ffb74d"
FONT      = "Segoe UI"

# ─────────────────────────────────────────────────────────────────────────────
#  MOCK DATA  (replaces API + DB entirely)
# ─────────────────────────────────────────────────────────────────────────────
MOCK_CITIES = ["Mumbai", "London", "New York", "Tokyo", "Sydney"]

MOCK_CURRENT = {
    "city":       "Mumbai",
    "country":    "IN",
    "temp":       34.2,
    "feels_like": 38.5,
    "humidity":   82,
    "pressure":   1008,
    "wind":       18.4,
    "visibility": 6.2,
    "condition":  "Partly Cloudy",
    "icon":       "⛅",
    "uv_index":   7.3,
    "sunrise":    "06:32",
    "sunset":     "19:05",
    "forecast": [
        {"day": "Mon", "icon": "⛅", "high": 34, "low": 27, "rain": 20},
        {"day": "Tue", "icon": "🌧️", "high": 31, "low": 26, "rain": 75},
        {"day": "Wed", "icon": "🌦️", "high": 30, "low": 25, "rain": 60},
        {"day": "Thu", "icon": "☁️", "high": 32, "low": 26, "rain": 35},
        {"day": "Fri", "icon": "🌤️", "high": 35, "low": 28, "rain": 10},
        {"day": "Sat", "icon": "☀️", "high": 37, "low": 29, "rain":  5},
        {"day": "Sun", "icon": "☀️", "high": 36, "low": 28, "rain":  8},
    ],
    "hourly": [
        {"time": "Now",   "icon": "⛅", "temp": 34.2},
        {"time": "13:00", "icon": "⛅", "temp": 35.1},
        {"time": "14:00", "icon": "🌦️", "temp": 34.8},
        {"time": "15:00", "icon": "🌧️", "temp": 33.5},
        {"time": "16:00", "icon": "🌧️", "temp": 32.1},
        {"time": "17:00", "icon": "🌦️", "temp": 31.4},
        {"time": "18:00", "icon": "☁️", "temp": 30.9},
        {"time": "19:00", "icon": "🌤️", "temp": 29.8},
    ],
}

# 30-day mock history  (date, temp, humidity, pressure, wind, condition)
import random as _rnd
_rnd.seed(99)
MOCK_HISTORY = {
    city: [
        (
            (datetime.now().replace(day=1) if False else
             datetime(2025, 2, 19 - i % 28 + 1).strftime("%Y-%m-%d")),
            round(28 + _rnd.uniform(-6, 8), 1),
            _rnd.randint(55, 92),
            _rnd.randint(1004, 1016),
            round(_rnd.uniform(5, 35), 1),
            _rnd.choice(["Clear Sky","Partly Cloudy","Rain","Overcast","Thunderstorm"]),
        )
        for i in range(30)
    ]
    for city in MOCK_CITIES
}

MOCK_COMPARE = {
    "London": {
        "temp": 14.3, "feels_like": 12.1, "humidity": 68,
        "pressure": 1018, "wind": 22.0, "visibility": 12.5,
        "condition": "Overcast", "icon": "☁️", "uv_index": 2.1,
    },
    "New York": {
        "temp": 8.7, "feels_like": 6.2, "humidity": 55,
        "pressure": 1022, "wind": 15.3, "visibility": 18.0,
        "condition": "Mainly Clear", "icon": "🌤️", "uv_index": 3.4,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
#  DESIGN PRIMITIVES
# ─────────────────────────────────────────────────────────────────────────────
def L(text="", size=12, bold=False, color=TXT_PRI,
      align=Qt.AlignmentFlag.AlignLeft):
    l = QLabel(text)
    f = QFont(FONT, size)
    f.setBold(bold)
    l.setFont(f)
    l.setAlignment(align)
    l.setStyleSheet(f"color:{color}; background:transparent;")
    return l


class Frost(QWidget):
    """Deep navy frosted glass card."""
    def __init__(self, parent=None, r=18, glow=False):
        super().__init__(parent)
        self._r = r
        self._glow = glow
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._r, self._r)
        p.fillPath(path, BG_CARD)
        hi = QLinearGradient(0, 0, 0, 55)
        hi.setColorAt(0, QColor(255, 255, 255, 16))
        hi.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(path, hi)
        p.setPen(QPen(BORDER_HI if self._glow else BORDER, 1))
        p.drawPath(path)
        if self._glow:
            gp = QPainterPath()
            gp.addRoundedRect(-2, -2, self.width()+4, self.height()+4,
                               self._r+2, self._r+2)
            p.setPen(QPen(QColor(79, 195, 247, 28), 3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(gp)


SS  = (f"QLineEdit{{background:rgba(6,16,34,210);"
       f"border:1px solid rgba(90,170,255,38);border-radius:12px;"
       f"padding:0 16px;color:{TXT_PRI};}}"
       f"QLineEdit:focus{{border:1.5px solid rgba(79,195,247,110);}}")

BSS = (f"QPushButton{{background:rgba(79,195,247,20);"
       f"border:1px solid rgba(79,195,247,55);border-radius:12px;"
       f"color:{ACC};font-family:{FONT};}}"
       f"QPushButton:hover{{background:rgba(79,195,247,38);}}"
       f"QPushButton:pressed{{background:rgba(79,195,247,12);}}")

CSS = (f"QComboBox{{background:rgba(6,16,34,210);"
       f"border:1px solid rgba(90,170,255,38);border-radius:10px;"
       f"padding:0 12px;color:{TXT_PRI};font-family:{FONT};}}"
       f"QComboBox::drop-down{{border:none;width:24px;}}"
       f"QComboBox QAbstractItemView{{background:#060f1e;color:{TXT_PRI};"
       f"border:1px solid rgba(79,195,247,45);"
       f"selection-background-color:rgba(79,195,247,28);}}")


class Pill(Frost):
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
        self._v.setText(v)


class HChip(Frost):
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


# ─────────────────────────────────────────────────────────────────────────────
#  AURORA BACKGROUND
# ─────────────────────────────────────────────────────────────────────────────
class Aurora(QWidget):
    def __init__(self):
        super().__init__()
        self._t = 0.0
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(50)

    def _tick(self):
        self._t += 0.8
        self.update()

    def paintEvent(self, e):
        import math, random
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        base = QLinearGradient(0, 0, 0, h)
        base.setColorAt(0.0, QColor("#010a15"))
        base.setColorAt(0.5, QColor("#020e1c"))
        base.setColorAt(1.0, QColor("#010b17"))
        p.fillRect(self.rect(), base)

        bx = w*0.72 + math.sin(math.radians(self._t*0.55)) * 130
        by = h*0.20 + math.cos(math.radians(self._t*0.38)) * 65
        g  = QRadialGradient(bx, by, 370)
        g.setColorAt(0.0, QColor(18, 85, 200, 42))
        g.setColorAt(0.55, QColor(10, 55, 150, 18))
        g.setColorAt(1.0, QColor(0, 0, 0, 0))
        pp = QPainterPath()
        pp.addEllipse(bx-370, by-280, 740, 560)
        p.fillPath(pp, g)

        bx2 = w*0.20 + math.cos(math.radians(self._t*0.45)) * 110
        by2 = h*0.62 + math.sin(math.radians(self._t*0.32)) * 75
        g2  = QRadialGradient(bx2, by2, 290)
        g2.setColorAt(0.0, QColor(0, 130, 165, 30))
        g2.setColorAt(0.6, QColor(0, 80, 120, 12))
        g2.setColorAt(1.0, QColor(0, 0, 0, 0))
        pp2 = QPainterPath()
        pp2.addEllipse(bx2-290, by2-230, 580, 460)
        p.fillPath(pp2, g2)

        rng = random.Random(42)
        p.setPen(QPen(QColor(255, 255, 255, 28), 1))
        for _ in range(55):
            p.drawPoint(rng.randint(0, w), rng.randint(0, h))


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 1 — CURRENT WEATHER
# ─────────────────────────────────────────────────────────────────────────────
class CurrentTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build()
        # Load mock data on startup
        self._on_data(MOCK_CURRENT)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
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

        # search bar (wired to mock data — no network call)
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
        row.addWidget(self.search); row.addWidget(btn)
        lay.addLayout(row)
        self.status = L("", 10, color=DANGER,
                        align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.status)

        # hero card
        hero = Frost(r=22, glow=True)
        hero.setMinimumHeight(228)
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(24, 18, 24, 18)
        hl.setSpacing(8)
        cr = QHBoxLayout()
        self.city_lbl = L("—", 20, bold=True)
        self.date_lbl = L("", 10, color=TXT_DIM)
        cr.addWidget(self.city_lbl); cr.addStretch(); cr.addWidget(self.date_lbl)
        hl.addLayout(cr)
        self.cond_lbl = L("Enter a city to get live weather", 11, color=TXT_SEC)
        hl.addWidget(self.cond_lbl)
        hl.addSpacing(4)
        mid = QHBoxLayout()
        self.icon_lbl = QLabel("🌐")
        self.icon_lbl.setFont(QFont(FONT, 56))
        self.icon_lbl.setStyleSheet("background:transparent;")
        self.temp_lbl = L("—", 56, bold=True)
        mid.addWidget(self.icon_lbl); mid.addWidget(self.temp_lbl)
        mid.addStretch()
        rhs = QVBoxLayout()
        rhs.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        rhs.setSpacing(6)
        self.feels_lbl = L("Feels like —", 11, color=TXT_SEC)
        self.uv_lbl    = L("UV Index  —", 11, color=TXT_SEC)
        rhs.addWidget(self.feels_lbl); rhs.addWidget(self.uv_lbl)
        mid.addLayout(rhs)
        hl.addLayout(mid)
        hl.addStretch()
        sun = QHBoxLayout()
        self.sr_lbl = L("🌅  —", 11, color=WARN)
        self.ss_lbl = L("—  🌇", 11, color="#ff8a65",
                        align=Qt.AlignmentFlag.AlignRight)
        sun.addWidget(self.sr_lbl); sun.addStretch(); sun.addWidget(self.ss_lbl)
        hl.addLayout(sun)
        lay.addWidget(hero)

        # stat pills
        grid = QGridLayout(); grid.setSpacing(10)
        self.pills = {
            "humidity":   Pill("💧", "Humidity",   "—"),
            "wind":       Pill("💨", "Wind",        "—"),
            "pressure":   Pill("🌡", "Pressure",   "—"),
            "visibility": Pill("👁", "Visibility", "—"),
        }
        for i, w in enumerate(self.pills.values()):
            grid.addWidget(w, i // 2, i % 2)
        lay.addLayout(grid)

        # alert banner
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
        self.alert.hide()
        lay.addWidget(self.alert)

        # hourly
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
        self._hrow = QHBoxLayout(hw)
        self._hrow.setSpacing(8)
        self._hrow.setContentsMargins(4, 2, 4, 2)
        hs.setWidget(hw)
        hs.setWidgetResizable(False)
        lay.addWidget(hs)
        self._hs = hs

        # 7-day forecast
        lay.addWidget(L("  7-Day Forecast", 12, bold=True, color=ACC))
        self._fc = Frost(r=18)
        self._fl = QVBoxLayout(self._fc)
        self._fl.setContentsMargins(8, 10, 8, 10)
        self._fl.setSpacing(4)
        lay.addWidget(self._fc)
        lay.addStretch()

    def _fetch(self):
        """Stub: loads mock data regardless of input city."""
        city = self.search.text().strip()
        if not city:
            return
        # Show a fake "loading" state briefly, then populate with mock
        self.status.setStyleSheet(f"color:{ACC};")
        self.status.setText("Loading mock data…")
        mock = dict(MOCK_CURRENT)
        mock["city"] = city
        QTimer.singleShot(400, lambda: self._on_data(mock))

    def _on_data(self, data):
        self.status.setText("")
        self.city_lbl.setText(f"📍 {data['city']}, {data['country']}")
        self.date_lbl.setText(datetime.now().strftime("%a %d %b %Y"))
        self.cond_lbl.setText(data["condition"])
        self.icon_lbl.setText(data["icon"])
        self.temp_lbl.setText(f"{data['temp']}°C")
        self.feels_lbl.setText(f"Feels like  {data['feels_like']}°C")
        self.uv_lbl.setText(f"UV Index  {data['uv_index']}")
        self.sr_lbl.setText(f"🌅  {data['sunrise']}")
        self.ss_lbl.setText(f"{data['sunset']}  🌇")
        self.pills["humidity"].set(f"{data['humidity']}%")
        self.pills["wind"].set(f"{data['wind']} km/h")
        self.pills["pressure"].set(f"{data['pressure']} hPa")
        self.pills["visibility"].set(f"{data['visibility']} km")

        # hourly chips
        while self._hrow.count():
            item = self._hrow.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for h in data.get("hourly", []):
            self._hrow.addWidget(HChip(h["time"], h["icon"], h["temp"]))
        chip_w = 82; gap = 8
        count  = len(data.get("hourly", []))
        total_w = count * (chip_w + gap) + 8
        self._hrow.parentWidget().setFixedWidth(max(total_w, self._hs.width()))

        # forecast rows
        while self._fl.count():
            item = self._fl.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for i, f in enumerate(data.get("forecast", [])):
            self._fl.addWidget(
                FRow(f["day"], f["icon"], f["high"], f["low"], f["rain"]))
            if i < len(data["forecast"]) - 1:
                ln = QFrame()
                ln.setFrameShape(QFrame.Shape.HLine)
                ln.setStyleSheet("color:rgba(79,195,247,14);")
                self._fl.addWidget(ln)

        # alerts
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


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 2 — COMPARE
# ─────────────────────────────────────────────────────────────────────────────
class CompareTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._d1 = self._d2 = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)
        lay.addWidget(L("Compare Two Cities", 16, bold=True, color=ACC,
                        align=Qt.AlignmentFlag.AlignCenter))
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
        self.status = L("", 10, color=DANGER,
                        align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.status)

        cards = QHBoxLayout(); cards.setSpacing(12)
        self.cd1 = self._mk(); self.cd2 = self._mk()
        vs = L("VS", 20, bold=True, color=TXT_DIM,
               align=Qt.AlignmentFlag.AlignCenter)
        vs.setFixedWidth(38)
        cards.addWidget(self.cd1); cards.addWidget(vs); cards.addWidget(self.cd2)
        lay.addLayout(cards)

        self.fig    = Figure(figsize=(6, 2.8), facecolor="none")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background:transparent;")
        self.canvas.setMinimumHeight(200)
        lay.addWidget(self.canvas)

        self.banner = Frost(r=12)
        bl = QHBoxLayout(self.banner); bl.setContentsMargins(16, 10, 16, 10)
        self.blbl = L("", 11, color=TXT_SEC,
                      align=Qt.AlignmentFlag.AlignCenter)
        self.blbl.setWordWrap(True); bl.addWidget(self.blbl)
        self.banner.hide(); lay.addWidget(self.banner)
        lay.addStretch()

    def _mk(self):
        c  = Frost(r=16)
        cl = QVBoxLayout(c); cl.setContentsMargins(14, 14, 14, 14); cl.setSpacing(6)
        c._n = L("—", 13, bold=True, align=Qt.AlignmentFlag.AlignCenter)
        c._i = QLabel("🌐"); c._i.setFont(QFont(FONT, 38))
        c._i.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c._i.setStyleSheet("background:transparent;")
        c._t = L("—°C", 26, bold=True, align=Qt.AlignmentFlag.AlignCenter)
        c._c = L("—", 10, color=TXT_SEC, align=Qt.AlignmentFlag.AlignCenter)
        c._s = L("", 10, color=TXT_DIM,  align=Qt.AlignmentFlag.AlignCenter)
        c._s.setWordWrap(True)
        for w in (c._n, c._i, c._t, c._c, c._s): cl.addWidget(w)
        return c

    def _fill(self, c, city, d):
        c._n.setText(city); c._i.setText(d["icon"])
        c._t.setText(f"{d['temp']}°C"); c._c.setText(d["condition"])
        c._s.setText(f"💧{d['humidity']}%  💨{d['wind']} km/h\n"
                     f"🌡{d['pressure']} hPa  👁{d['visibility']} km")

    def _compare(self):
        """Stub: uses MOCK_COMPARE or generates values from MOCK_CURRENT."""
        c1_name = self.c1.text().strip() or "London"
        c2_name = self.c2.text().strip() or "New York"
        if not c1_name or not c2_name:
            self.status.setText("Enter both cities."); return
        self.status.setStyleSheet(f"color:{ACC};")
        self.status.setText("Loading mock data…")

        # Reuse known mock entries or fall back to MOCK_CURRENT values
        d1 = MOCK_COMPARE.get(c1_name, dict(MOCK_CURRENT))
        d2 = MOCK_COMPARE.get(c2_name, {
            "temp": 22.5, "feels_like": 21.0, "humidity": 60,
            "pressure": 1013, "wind": 12.0, "visibility": 15.0,
            "condition": "Clear Sky", "icon": "☀️", "uv_index": 5.2,
        })
        self._d1 = (c1_name, d1)
        self._d2 = (c2_name, d2)
        self._fill(self.cd1, c1_name, d1)
        self._fill(self.cd2, c2_name, d2)
        QTimer.singleShot(300, self._draw)

    def _draw(self):
        if not (self._d1 and self._d2): return
        self.status.setText("")
        c1, d1 = self._d1; c2, d2 = self._d2
        metrics = ["Temp °C", "Humidity", "Wind", "UV"]
        v1 = [d1["temp"], d1["humidity"], d1["wind"], d1["uv_index"]]
        v2 = [d2["temp"], d2["humidity"], d2["wind"], d2["uv_index"]]
        self.fig.clear(); ax = self.fig.add_subplot(111)
        self.fig.patch.set_alpha(0); ax.set_facecolor("#ffffff04")
        x  = np.arange(len(metrics)); w = 0.32
        b1 = ax.bar(x-w/2, v1, w, label=c1, color="#4fc3f7", alpha=0.82, zorder=3)
        b2 = ax.bar(x+w/2, v2, w, label=c2, color="#26c6da", alpha=0.82, zorder=3)
        ax.set_xticks(x); ax.set_xticklabels(metrics, color=TXT_SEC, fontsize=9)
        ax.tick_params(axis="y", colors=TXT_SEC, labelsize=8)
        ax.spines[:].set_visible(False)
        ax.yaxis.grid(True, color="#ffffff0c", zorder=0)
        ax.legend(facecolor="#060f1e", edgecolor="#1a3a5a",
                  labelcolor=TXT_PRI, fontsize=9)
        for b in (*b1, *b2):
            h = b.get_height()
            ax.text(b.get_x()+b.get_width()/2, h+.3, f"{h:.0f}",
                    ha="center", va="bottom", color=TXT_SEC, fontsize=8)
        self.canvas.draw()
        ht = c1 if d1["temp"]     > d2["temp"]     else c2
        wd = c1 if d1["wind"]     > d2["wind"]     else c2
        hm = c1 if d1["humidity"] > d2["humidity"] else c2
        self.blbl.setText(
            f"🌡 Hotter: {ht} ({max(d1['temp'],d2['temp'])}°C)   "
            f"·   💨 Windier: {wd}   ·   💧 More humid: {hm}")
        self.banner.show()


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 3 — HISTORY
# ─────────────────────────────────────────────────────────────────────────────
class HistoryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20); lay.setSpacing(12)
        lay.addWidget(L("Weather History", 16, bold=True, color=ACC,
                        align=Qt.AlignmentFlag.AlignCenter))
        row = QHBoxLayout(); row.setSpacing(8)
        self.combo = QComboBox()
        self.combo.setFixedHeight(38); self.combo.setFont(QFont(FONT, 11))
        self.combo.setStyleSheet(CSS)
        btn = QPushButton("Load")
        btn.setFixedHeight(38); btn.setFont(QFont(FONT, 11)); btn.setStyleSheet(BSS)
        btn.clicked.connect(self._load)
        row.addWidget(L("City:", 11)); row.addWidget(self.combo); row.addWidget(btn)
        lay.addLayout(row)

        hc = QHBoxLayout(); hc.setSpacing(12)
        self.hot  = self._hc("🔥", "Hottest Day", DANGER)
        self.cold = self._hc("🧊", "Coldest Day", ACC)
        hc.addWidget(self.hot); hc.addWidget(self.cold)
        lay.addLayout(hc)

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

        exp = QPushButton("📥  Export to CSV")
        exp.setFixedHeight(36); exp.setFont(QFont(FONT, 11)); exp.setStyleSheet(BSS)
        exp.clicked.connect(self._export)
        lay.addWidget(exp, alignment=Qt.AlignmentFlag.AlignRight)

        self._populate_combo()
        if self.combo.count(): self._load()

    def _hc(self, em, title, color):
        c  = Frost(r=14)
        cl = QVBoxLayout(c); cl.setContentsMargins(16, 12, 16, 12); cl.setSpacing(4)
        hr = QHBoxLayout()
        el = QLabel(em); el.setFont(QFont(FONT, 16)); el.setStyleSheet("background:transparent;")
        hr.addWidget(el); hr.addWidget(L(title, 11, color=color)); hr.addStretch()
        c._t = L("—", 22, bold=True, color=color)
        c._d = L("—", 9, color=TXT_DIM)
        c._c = L("—", 10, color=TXT_SEC)
        cl.addLayout(hr); cl.addWidget(c._t); cl.addWidget(c._d); cl.addWidget(c._c)
        return c

    def _populate_combo(self):
        self.combo.clear()
        for c in MOCK_CITIES:
            self.combo.addItem(c)

    def _load(self):
        city = self.combo.currentText()
        if not city: return
        rows = MOCK_HISTORY.get(city, [])
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)
        # hottest / coldest from mock
        if rows:
            hot  = max(rows, key=lambda x: x[1])
            cold = min(rows, key=lambda x: x[1])
            self.hot._t.setText(f"{hot[1]}°C")
            self.hot._d.setText(hot[0]); self.hot._c.setText(hot[5])
            self.cold._t.setText(f"{cold[1]}°C")
            self.cold._d.setText(cold[0]); self.cold._c.setText(cold[5])

    def _export(self):
        city = self.combo.currentText()
        if not city: return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", f"{city}_weather.csv", "CSV files (*.csv)")
        if not path: return
        import csv
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Date","Temp","Humidity","Pressure","Wind","Condition"])
            w.writerows(MOCK_HISTORY.get(city, []))
        QMessageBox.information(self, "Done", f"Saved:\n{path}")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 4 — TRENDS
# ─────────────────────────────────────────────────────────────────────────────
class TrendsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20); lay.setSpacing(12)
        lay.addWidget(L("Trend Analysis", 16, bold=True, color=ACC,
                        align=Qt.AlignmentFlag.AlignCenter))
        ctrl = QHBoxLayout(); ctrl.setSpacing(8)
        self.cc = QComboBox()
        self.cc.setFixedHeight(36); self.cc.setStyleSheet(CSS); self.cc.setFont(QFont(FONT, 11))
        self.mc = QComboBox()
        self.mc.addItems(["Temperature", "Humidity", "Pressure", "Wind Speed"])
        self.mc.setFixedHeight(36); self.mc.setStyleSheet(CSS); self.mc.setFont(QFont(FONT, 11))
        btn = QPushButton("Plot")
        btn.setFixedHeight(36); btn.setStyleSheet(BSS); btn.setFont(QFont(FONT, 11))
        btn.clicked.connect(self._plot)
        ctrl.addWidget(L("City:", 11)); ctrl.addWidget(self.cc)
        ctrl.addWidget(L("Metric:", 11)); ctrl.addWidget(self.mc); ctrl.addWidget(btn)
        lay.addLayout(ctrl)

        self.fig    = Figure(figsize=(7, 3.2), facecolor="none")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background:transparent;")
        lay.addWidget(self.canvas)

        pr = QHBoxLayout(); pr.setSpacing(10)
        self.pa  = Pill("📊", "30-Day Avg", "—")
        self.pmx = Pill("⬆️",  "Max",        "—")
        self.pmn = Pill("⬇️",  "Min",        "—")
        self.pt  = Pill("📈", "Trend",      "—")
        for p in (self.pa, self.pmx, self.pmn, self.pt): pr.addWidget(p)
        lay.addLayout(pr); lay.addStretch()

        for c in MOCK_CITIES: self.cc.addItem(c)
        if self.cc.count(): self._plot()

    def _plot(self):
        city   = self.cc.currentText()
        metric = self.mc.currentText()
        if not city: return
        rows = list(reversed(MOCK_HISTORY.get(city, [])))
        if not rows: return
        cm = {
            "Temperature": (1, "°C",    "#4fc3f7"),
            "Humidity":    (2, "%",     "#26c6da"),
            "Pressure":    (3, " hPa",  "#ffb74d"),
            "Wind Speed":  (4, " km/h", "#66bb6a"),
        }
        col, unit, color = cm[metric]
        dates  = [r[0][-5:] for r in rows]
        values = [r[col] for r in rows]
        self.fig.clear(); ax = self.fig.add_subplot(111)
        self.fig.patch.set_alpha(0); ax.set_facecolor("#ffffff04")
        ax.fill_between(range(len(values)), values, alpha=0.14, color=color)
        ax.plot(range(len(values)), values, color=color,
                linewidth=2, marker="o", markersize=3.5, zorder=4)
        if len(values) > 2:
            z = np.polyfit(range(len(values)), values, 1)
            p = np.poly1d(z)
            ax.plot(range(len(values)), p(range(len(values))),
                    "--", color="#ffffff28", linewidth=1.2, zorder=3)
            s = z[0]
            trend = f"↑ +{s:.2f}{unit}/day" if s > 0 else f"↓ {s:.2f}{unit}/day"
        else:
            trend = "N/A"
        step  = max(1, len(dates) // 6)
        ticks = list(range(0, len(dates), step))
        ax.set_xticks(ticks)
        ax.set_xticklabels([dates[i] for i in ticks],
                           color=TXT_SEC, fontsize=8, rotation=30)
        ax.tick_params(axis="y", colors=TXT_SEC, labelsize=8)
        ax.spines[:].set_visible(False)
        ax.yaxis.grid(True, color="#ffffff0c", zorder=0)
        ax.set_title(f"{city} — {metric} (last {len(values)} days)",
                     color=ACC, fontsize=10, pad=8)
        self.canvas.draw()
        avg_ = sum(values) / len(values)
        self.pa.set(f"{avg_:.1f}{unit}"); self.pmx.set(f"{max(values):.1f}{unit}")
        self.pmn.set(f"{min(values):.1f}{unit}"); self.pt.set(trend)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather Forecast")
        self.setMinimumSize(800, 860)
        bg = Aurora(); self.setCentralWidget(bg)
        outer = QVBoxLayout(bg); outer.setContentsMargins(0, 0, 0, 0)

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

        self.tc  = CurrentTab()
        self.tcm = CompareTab()
        self.th  = HistoryTab()
        self.tt  = TrendsTab()

        tabs.addTab(self.tc,  "🌤  Current")
        tabs.addTab(self.tcm, "🔀  Compare")
        tabs.addTab(self.th,  "📋  History")
        tabs.addTab(self.tt,  "📈  Trends")


app = QApplication(sys.argv)
app.setStyle("Fusion")
w = MainWindow()
w.show()
sys.exit(app.exec())
