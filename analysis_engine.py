import pandas as pd

class WeatherProcessor:
    def __init__(self, file_path: str):
        # Load the CSV file into a data structure
        self.df = pd.read_csv(file_path)
        # Ensure the timestamp column is recognized as date/time
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])

    def find_extremes(self):
        """Finds and prints the highest and lowest temperatures in the data."""
        # Find the row positions for the maximum and minimum temperatures
        h_idx = self.df['temp_c'].idxmax()
        c_idx = self.df['temp_c'].idxmin()

        hottest = self.df.iloc[h_idx]
        coldest = self.df.iloc[c_idx]

        print("--- Temperature Extremes ---")
        print(f"Hottest: {hottest['temp_c']}°C at {hottest['timestamp']}")
        print(f"Coldest: {coldest['temp_c']}°C at {coldest['timestamp']}\n")

    def calculate_trends(self):
        """Calculates temperature changes and averages over time."""
        # Calculate the difference in temperature between current and previous rows
        self.df['temp_change'] = self.df['temp_c'].diff()

        # Calculate a 3-reading moving average to smooth out fluctuations
        self.df['average_trend'] = self.df['temp_c'].rolling(window=3).mean()

        print("--- Trend Analysis (Latest Data) ---")
        print(self.df[['timestamp', 'temp_c', 'temp_change', 'average_trend']].tail())

# Example usage
if __name__ == "__main__":
    processor = WeatherProcessor('test_logs/daily_telemetry.csv')
    processor.find_extremes()
    processor.calculate_trends()