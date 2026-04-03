import sys
import os
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QApplication, QPushButton
import finalBackend
from design_ai import MainWindow, SplashScreen

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

# Make all file paths relative to THIS script's directory, not cwd
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("WEATHER APP BRIDGE")
print("=" * 60)


class WeatherFetcher(QThread):
    success = Signal(dict)
    failure = Signal(str)

    def __init__(self, city):
        super().__init__()
        self.city = city

    def run(self):
        try:
            print(f"Fetching {self.city}...")
            csv_path = os.path.join(SCRIPT_DIR, 'test_logs', 'daily_telemetry.csv')
            processor = finalBackend.WeatherProcessor(file_path=csv_path)
            result = processor.get_current_weather(self.city)
            if result.get('success'):
                print(f"Got {result['city']}: {result['temp']}C")
                self.success.emit(result)
            else:
                error = result.get('error', 'Unknown error')
                print(f"Error: {error}")
                self.failure.emit(error)
        except Exception as e:
            print(f"Exception: {e}")
            import traceback; traceback.print_exc()
            self.failure.emit(str(e))


def _make_processor():
    """Always use the same absolute CSV path regardless of cwd."""
    csv_path = os.path.join(SCRIPT_DIR, 'test_logs', 'daily_telemetry.csv')
    return finalBackend.WeatherProcessor(file_path=csv_path)


def main():
    print("Starting application...")
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    splash = SplashScreen()
    splash.show()

    _threads = []

    def _cleanup(thread):
        thread.quit()
        thread.wait(200)
        if thread in _threads:
            _threads.remove(thread)

    def _update_city_lists(w):
        """Reload cities from disk and repopulate both dropdowns."""
        try:
            processor = _make_processor()
            cities = processor.get_all_cities()
            print(f"Cities in dropdown: {cities}")
            w.th.set_cities(cities)
            w.tt.set_cities(cities)
        except Exception as e:
            print(f"City list error: {e}")

    def launch_main():
        splash.close()

        w = MainWindow()
        w.showMaximized()

        # ── CURRENT TAB ───────────────────────────────────────────────────────
        def on_current_search():
            city = w.tc.search.text().strip()
            if not city:
                return
            print(f"Search: '{city}'")
            w.tc.show_loading()
            t = WeatherFetcher(city)
            _threads.append(t)

            def on_ok(data):
                w.tc.load_data(data)
                _update_city_lists(w)   # refresh dropdowns after every successful search
                _cleanup(t)

            def on_err(msg):
                w.tc.show_error(msg)
                _cleanup(t)

            t.success.connect(on_ok, Qt.ConnectionType.QueuedConnection)
            t.failure.connect(on_err, Qt.ConnectionType.QueuedConnection)
            t.start()

        try:
            w.tc.search.returnPressed.disconnect()
        except RuntimeError:
            pass
        w.tc.search.returnPressed.connect(on_current_search)

        for btn in w.tc.findChildren(QPushButton):
            if btn.text() == "Search":
                try:
                    btn.clicked.disconnect()
                except RuntimeError:
                    pass
                btn.clicked.connect(on_current_search)
                break

        w.tc._fetch = on_current_search

        # ── COMPARE TAB ───────────────────────────────────────────────────────
        def on_compare():
            city1 = w.tcm.c1.text().strip()
            city2 = w.tcm.c2.text().strip()
            if not city1 or not city2:
                w.tcm.show_error("Enter both cities.")
                return
            print(f"Compare: '{city1}' vs '{city2}'")
            w.tcm.show_loading()
            w.tcm._d1 = None
            w.tcm._d2 = None

            t1 = WeatherFetcher(city1)
            t2 = WeatherFetcher(city2)
            _threads.extend([t1, t2])

            def ok1(data):
                w.tcm.load_city1(data['city'], data)
                _cleanup(t1)

            def err1(msg):
                w.tcm.show_error(f"{city1}: {msg}")
                _cleanup(t1)

            def ok2(data):
                w.tcm.load_city2(data['city'], data)
                _cleanup(t2)

            def err2(msg):
                w.tcm.show_error(f"{city2}: {msg}")
                _cleanup(t2)

            t1.success.connect(ok1, Qt.ConnectionType.QueuedConnection)
            t1.failure.connect(err1, Qt.ConnectionType.QueuedConnection)
            t2.success.connect(ok2, Qt.ConnectionType.QueuedConnection)
            t2.failure.connect(err2, Qt.ConnectionType.QueuedConnection)
            t1.start()
            t2.start()

        for btn in w.tcm.findChildren(QPushButton):
            if btn.text() == "Compare":
                try:
                    btn.clicked.disconnect()
                except RuntimeError:
                    pass
                btn.clicked.connect(on_compare)
                break

        w.tcm._compare = on_compare

        # ── HISTORY TAB ───────────────────────────────────────────────────────
        def on_load_history():
            city = w.th.combo.currentText()
            print(f"Load history clicked, city='{city}'")
            if not city:
                print("No city selected in dropdown")
                return
            try:
                processor = _make_processor()
                rows = processor.get_history(city, days=30)
                print(f"Found {len(rows)} history records for {city}")
                w.th.load_history(rows)
            except Exception as e:
                print(f"History error: {e}")
                import traceback; traceback.print_exc()

        # Disconnect whatever the frontend wired up and connect our real handler
        for btn in w.th.findChildren(QPushButton):
            if btn.text() == "Load":
                try:
                    btn.clicked.disconnect()
                except RuntimeError:
                    pass
                btn.clicked.connect(on_load_history)
                print("Connected Load button")
                break

        w.th._load = on_load_history

        # ── TRENDS TAB ────────────────────────────────────────────────────────
        def on_plot():
            city = w.tt.cc.currentText()
            print(f"Plot clicked, city='{city}'")
            if not city:
                print("No city selected in trends dropdown")
                return
            try:
                processor = _make_processor()
                rows = processor.get_history(city, days=30)
                print(f"Found {len(rows)} trend records for {city}")
                w.tt.load_trends(rows)
            except Exception as e:
                print(f"Trends error: {e}")
                import traceback; traceback.print_exc()

        for btn in w.tt.findChildren(QPushButton):
            if btn.text() == "Plot":
                try:
                    btn.clicked.disconnect()
                except RuntimeError:
                    pass
                btn.clicked.connect(on_plot)
                print("Connected Plot button")
                break

        w.tt._plot = on_plot

        # ── Refresh dropdowns when the user switches to History or Trends tab ─
        # This ensures cities searched earlier in the session always appear.
        tab_widget = w.centralWidget().findChild(
            __import__('PySide6.QtWidgets', fromlist=['QTabWidget']).QTabWidget
        )
        if tab_widget:
            def on_tab_changed(index):
                # Tab 2 = History, Tab 3 = Trends
                if index in (2, 3):
                    _update_city_lists(w)
            tab_widget.currentChanged.connect(on_tab_changed)

        # Populate on startup (catches cities from previous sessions)
        _update_city_lists(w)

    try:
        splash.btn.clicked.disconnect()
    except RuntimeError:
        pass
    splash.btn.clicked.connect(launch_main)

    print("App ready! Click Get Started.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()