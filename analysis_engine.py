import pandas as pd

class WeatherProcessor:
    def __init__(self, file_path: str):
        # Load the 'Bus' (Data) into RAM
        self.df = pd.read_csv(file_path)
        # Convert timestamp to a format the computer understands
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])

    def find_extremes(self):
        """Task: Show hottest/coldest day from stored data."""
        # PEAK DETECTION: Find the address (index) of the Max/Min values
        h_idx = self.df['temp_c'].idxmax()
        c_idx = self.df['temp_c'].idxmin()

        hottest = self.df.iloc[h_idx]
        coldest = self.df.iloc[c_idx]

        print("--- PEAK DETECTION (Extremes) ---")
        print(f"Hottest: {hottest['temp_c']}°C at {hottest['timestamp']}")
        print(f"Coldest: {coldest['temp_c']}°C at {coldest['timestamp']}\n")

    def calculate_trends(self):
        """Task: Weather trend analysis."""
        # DISCRETE DERIVATIVE: Calculate Delta Temp between readings
        self.df['temp_slope'] = self.df['temp_c'].diff()

        # SIGNAL SMOOTHING: 3-hour moving average to remove 'noise'
        self.df['smooth_signal'] = self.df['temp_c'].rolling(window=3).mean()

        print("--- TREND ANALYSIS (Last 5 Samples) ---")
        # Showing the Timestamp, Temp, the Slope, and the Smoothed Signal
        print(self.df[['timestamp', 'temp_c', 'temp_slope', 'smooth_signal']].tail())

# Power on the processor
processor = WeatherProcessor('test_logs/daily_telemetry.csv')
processor.find_extremes()
processor.calculate_trends()