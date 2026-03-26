# finalBackend.py - FIXED VERSION
"""
Weather Monitoring Backend Module
Uses Open-Meteo API (FREE, no API key needed!)
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List
import logging
import pandas as pd
import os

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

COLUMNS = ["timestamp", "location_id", "temp_c", "humidity_pct",
           "wind_kph", "condition", "pressure_hpa"]


def _load_df(file_path: str) -> pd.DataFrame:
    """Load CSV and always return a DataFrame with a proper datetime timestamp column."""
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, parse_dates=['timestamp'])
        # If parse_dates silently failed (column missing / bad data), coerce manually
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        # Drop rows with missing critical fields
        df = df.dropna(subset=['location_id', 'temp_c'])
        return df
    return pd.DataFrame(columns=COLUMNS)


# ============ TELEMETRY STORAGE ENGINE ============
class TelemetryStorageEngine:
    def __init__(self, file_path: str = 'test_logs/daily_telemetry.csv'):
        self.file_path = file_path
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        self.df = _load_df(file_path)

    def log_reading(self, data: Dict) -> bool:
        try:
            new_row = pd.DataFrame([{
                'timestamp':    datetime.now(),
                'location_id':  data['location_id'],
                'temp_c':       data['temp_c'],
                'humidity_pct': data['humidity_pct'],
                'wind_kph':     data['wind_kph'],
                'condition':    data['condition'],
                'pressure_hpa': data.get('pressure_hpa', None)
            }])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            self.df.to_csv(self.file_path, index=False)
            return True
        except Exception as e:
            logging.error(f"Failed to save: {e}")
            return False

    def log_reading_for_date(self, data: Dict, dt: 'datetime') -> bool:
        """Save a forecast row with a specific date (not now)."""
        try:
            # Only write if we do not already have a row for this city+date
            date_str = dt.strftime('%Y-%m-%d')
            location = data['location_id']
            if len(self.df) > 0 and 'location_id' in self.df.columns:
                self.df['_date'] = self.df['timestamp'].dt.strftime('%Y-%m-%d')
                already = self.df[
                    (self.df['location_id'] == location) &
                    (self.df['_date'] == date_str)
                ]
                self.df.drop(columns=['_date'], inplace=True)
                if len(already) > 0:
                    return True   # already have data for this day, skip
            new_row = pd.DataFrame([{
                'timestamp':    dt,
                'location_id':  location,
                'temp_c':       data['temp_c'],
                'humidity_pct': data['humidity_pct'],
                'wind_kph':     data['wind_kph'],
                'condition':    data['condition'],
                'pressure_hpa': data.get('pressure_hpa', None)
            }])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            self.df.to_csv(self.file_path, index=False)
            return True
        except Exception as e:
            logging.error(f"Failed to save forecast row: {e}")
            return False

    def get_history(self, city: str = None, days: int = 30) -> List:
        if len(self.df) == 0:
            return []

        df_filtered = self.df.copy()
        if city:
            df_filtered = df_filtered[
                df_filtered['location_id'].str.contains(city, case=False, na=False)
            ]

        cutoff = datetime.now() - timedelta(days=days)
        df_filtered = df_filtered[df_filtered['timestamp'] >= cutoff]
        df_filtered = df_filtered.sort_values('timestamp')

        # Add a date column and keep only the LAST reading per day
        df_filtered['date'] = df_filtered['timestamp'].dt.strftime('%Y-%m-%d')
        df_filtered = df_filtered.drop_duplicates(subset='date', keep='last')

        rows = []
        for _, row in df_filtered.iterrows():
            ts = row['timestamp']
            if pd.isna(ts):
                continue
            rows.append((
                str(row['date']),
                float(row['temp_c']),
                int(row['humidity_pct']),
                int(row['pressure_hpa']) if pd.notna(row.get('pressure_hpa')) else 1013,
                float(row['wind_kph']),
                str(row['condition'])
            ))
        return rows

    def get_all_cities(self) -> List[str]:
        if len(self.df) == 0:
            return []
        cities = self.df['location_id'].unique()
        city_names = [str(c).split(',')[0].strip() for c in cities if isinstance(c, str)]
        return sorted(list(set(city_names)))


# ============ WEATHER PROCESSOR ============
class WeatherProcessor:
    def __init__(self, file_path: str = 'test_logs/daily_telemetry.csv'):
        self.base_url    = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
        self.file_path   = file_path
        self.df          = _load_df(file_path)   # shared read — uses same fix
        self.storage     = TelemetryStorageEngine(file_path)
        logging.info("✅ WeatherBackend initialized with Open-Meteo (free API)")

    def _find_city_coordinates(self, city: str) -> Dict:
        params = {'name': city, 'count': 1, 'language': 'en', 'format': 'json'}
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            if response.status_code != 200:
                return {'success': False, 'error': "Geocoding service error"}
            data = response.json()
            if not data.get('results'):
                return {'success': False, 'error': f"City '{city}' not found"}
            result = data['results'][0]
            return {
                'success':   True,
                'name':      result['name'],
                'country':   result.get('country', 'Unknown'),
                'latitude':  result['latitude'],
                'longitude': result['longitude']
            }
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': "Network error - check internet"}
        except Exception as e:
            return {'success': False, 'error': f"Error: {str(e)}"}

    def description(self, weather_code: int) -> str:
        weather_codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            56: "Light freezing drizzle", 57: "Dense freezing drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            66: "Light freezing rain", 67: "Heavy freezing rain",
            71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
            77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
            82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return weather_codes.get(weather_code, "Unknown")

    def _get_weather_icon(self, weather_code: int) -> str:
        if weather_code in [0, 1]:           return "☀️"
        elif weather_code in [2, 3]:         return "⛅"
        elif weather_code in [45, 48]:       return "🌫️"
        elif weather_code in [51,53,55,56,57,61,63,65,66,67,80,81,82]: return "🌧️"
        elif weather_code in [71,73,75,77,85,86]: return "❄️"
        elif weather_code in [95,96,99]:     return "⛈️"
        else:                                return "🌤️"

    def _save_weather_data(self, weather_data: Dict) -> None:
        telemetry_data = {
            'location_id':  f"{weather_data['city']}, {weather_data['country']}",
            'temp_c':       weather_data['temperature'],
            'humidity_pct': weather_data['humidity'],
            'wind_kph':     weather_data['wind_speed'] * 3.6,
            'condition':    weather_data['condition']
        }
        if weather_data.get('pressure') != 'N/A':
            telemetry_data['pressure_hpa'] = weather_data['pressure']
        success = self.storage.log_reading(telemetry_data)
        if success:
            logging.info(f"📊 Saved weather data for {weather_data['city']}")
        else:
            logging.warning(f"⚠️ Failed to save weather data for {weather_data['city']}")

    def get_current_weather(self, city: str) -> Dict:
        location = self._find_city_coordinates(city)
        if not location['success']:
            return {'success': False, 'error': location['error']}

        params = {
            'latitude':  location['latitude'],
            'longitude': location['longitude'],
            'current':   'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,pressure_msl',
            'hourly':    'temperature_2m,weather_code',
            'daily':     'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max,relative_humidity_2m_mean,pressure_msl_mean',
            'timezone':  'auto'
        }

        try:
            response = requests.get(self.weather_url, params=params, timeout=10)
            response.raise_for_status()
            data    = response.json()
            current = data['current']

            # ── hourly forecast: next 8 hours ────────────────────────────────
            # Use the index into the hourly list, not the raw hour integer.
            # Find which index corresponds to "now" by matching the current time string.
            hourly_times = data['hourly']['time']   # list of "YYYY-MM-DDTHH:00"
            now_str = datetime.now().strftime('%Y-%m-%dT%H:00')

            # Find the closest matching index (fall back to 0 if not found)
            start_idx = 0
            for i, t in enumerate(hourly_times):
                if t >= now_str:
                    start_idx = i
                    break

            hourly_data = []
            for i in range(8):
                idx = start_idx + i
                if idx < len(hourly_times):
                    # Format the time string from the ISO timestamp, not the raw hour int
                    t_str   = hourly_times[idx]          # "2024-03-25T09:00"
                    t_label = 'Now' if i == 0 else datetime.fromisoformat(t_str).strftime('%H:%M')
                    hourly_data.append({
                        'time': t_label,
                        'icon': self._get_weather_icon(data['hourly']['weather_code'][idx]),
                        'temp': data['hourly']['temperature_2m'][idx]
                    })

            # ── 7-day forecast ───────────────────────────────────────────────
            daily_data = []
            for i in range(min(7, len(data['daily']['time']))):
                daily_data.append({
                    'day':  datetime.fromisoformat(data['daily']['time'][i]).strftime('%a'),
                    'icon': self._get_weather_icon(data['daily']['weather_code'][i]),
                    'high': data['daily']['temperature_2m_max'][i],
                    'low':  data['daily']['temperature_2m_min'][i],
                    'rain': data['daily']['precipitation_probability_max'][i]
                })

            weather_info = {
                'success':    True,
                'city':       location['name'],
                'country':    location['country'],
                'temp':       current['temperature_2m'],
                'feels_like': current['apparent_temperature'],
                'humidity':   current['relative_humidity_2m'],
                'pressure':   current.get('pressure_msl', 1013),
                'wind':       round(current['wind_speed_10m'] * 3.6, 1),
                'visibility': 10.0,
                'condition':  self.description(current['weather_code']),
                'icon':       self._get_weather_icon(current['weather_code']),
                'uv_index':   5.0,
                'sunrise':    "06:00",
                'sunset':     "18:00",
                'hourly':     hourly_data,
                'forecast':   daily_data
            }

            # Save today's actual reading
            self._save_weather_data({
                'city':        location['name'],
                'country':     location['country'],
                'temperature': current['temperature_2m'],
                'feels_like':  current['apparent_temperature'],
                'humidity':    current['relative_humidity_2m'],
                'pressure':    current.get('pressure_msl', 'N/A'),
                'condition':   self.description(current['weather_code']),
                'wind_speed':  current['wind_speed_10m']
            })

            # Also save each forecast day so history fills up with real dates
            daily = data['daily']
            for i in range(min(7, len(daily['time']))):
                # skip day 0 — that is today, already saved above
                if i == 0:
                    continue
                forecast_dt = datetime.fromisoformat(daily['time'][i])
                # use avg of high+low as the day temperature
                avg_temp = (daily['temperature_2m_max'][i] + daily['temperature_2m_min'][i]) / 2
                wind_kph  = daily.get('wind_speed_10m_max', [None]*8)[i]
                humidity  = daily.get('relative_humidity_2m_mean', [None]*8)[i]
                pressure  = daily.get('pressure_msl_mean', [None]*8)[i]
                self.storage.log_reading_for_date({
                    'location_id':  f"{location['name']}, {location['country']}",
                    'temp_c':       avg_temp,
                    'humidity_pct': int(humidity) if humidity is not None else 70,
                    'wind_kph':     float(wind_kph) if wind_kph is not None else 10.0,
                    'condition':    self.description(daily['weather_code'][i]),
                    'pressure_hpa': float(pressure) if pressure is not None else 1013.0,
                }, forecast_dt)

            return weather_info

        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': "Network error - please check your internet connection"}
        except requests.exceptions.Timeout:
            return {'success': False, 'error': "Request timed out - API took too long to respond"}
        except Exception as e:
            return {'success': False, 'error': f"Unexpected error: {str(e)}"}

    def compare_cities(self, city1: str, city2: str) -> Dict:
        weather1 = self.get_current_weather(city1)
        weather2 = self.get_current_weather(city2)
        if not weather1['success']:
            return {'success': False, 'error': f"Couldn't get data for {city1}: {weather1['error']}"}
        if not weather2['success']:
            return {'success': False, 'error': f"Couldn't get data for {city2}: {weather2['error']}"}
        return {'success': True, 'city1': weather1, 'city2': weather2}

    def get_history(self, city: str, days: int = 30) -> List:
        return self.storage.get_history(city, days)

    def get_all_cities(self) -> List[str]:
        return self.storage.get_all_cities()

    def find_extremes(self):
        if len(self.df) == 0:
            return {'success': False, 'error': 'No data available'}
        h_idx   = self.df['temp_c'].idxmax()
        c_idx   = self.df['temp_c'].idxmin()
        hottest = self.df.iloc[h_idx]
        coldest = self.df.iloc[c_idx]
        return {
            'success': True,
            'hottest': {'temperature': hottest['temp_c'], 'city': hottest['location_id'], 'timestamp': str(hottest['timestamp'])},
            'coldest': {'temperature': coldest['temp_c'], 'city': coldest['location_id'], 'timestamp': str(coldest['timestamp'])}
        }

    def calculate_trends(self, limit: int = 5):
        if len(self.df) < 2:
            return {'success': False, 'error': 'Not enough data for trend analysis'}
        self.df['temp_slope']     = self.df['temp_c'].diff()
        self.df['smooth_signal']  = self.df['temp_c'].rolling(window=min(3, len(self.df))).mean()
        last_entries = self.df.tail(limit)
        trends = []
        for _, row in last_entries.iterrows():
            trends.append({
                'timestamp':    str(row['timestamp']),
                'temperature':  float(row['temp_c']),
                'slope':        float(row['temp_slope']) if not pd.isna(row['temp_slope']) else 0,
                'smooth_signal':float(row['smooth_signal']) if not pd.isna(row['smooth_signal']) else float(row['temp_c'])
            })
        if len(trends) >= 2:
            overall_change = trends[-1]['temperature'] - trends[0]['temperature']
            overall_trend  = 'increasing' if overall_change > 0 else ('decreasing' if overall_change < 0 else 'stable')
        else:
            overall_trend  = 'insufficient_data'
            overall_change = 0
        return {
            'success':            True,
            'trends':             trends,
            'overall_trend':      overall_trend,
            'temperature_change': overall_change,
            'total_records':      len(self.df),
            'last_updated':       str(self.df['timestamp'].max()) if len(self.df) > 0 else None
        }


def get_current_weather(city: str) -> Dict:
    return WeatherProcessor().get_current_weather(city)


if __name__ == "__main__":
    processor = WeatherProcessor()
    print("Testing weather backend...")
    result = processor.get_current_weather("London")
    if result['success']:
        print(f"Got weather for {result['city']}: {result['temp']}C")
        print(f"Hourly sample: {result['hourly'][:3]}")
        print(f"Forecast sample: {result['forecast'][:2]}")
    else:
        print(f"Error: {result['error']}")