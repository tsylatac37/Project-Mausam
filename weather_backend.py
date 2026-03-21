"""
Weather Monitoring Backend Module
Uses Open-Meteo API (FREE, no API key needed!)
Handles API calls, displays weather, compares cities
"""

import requests
from datetime import datetime
from typing import Dict, List
import logging
import pandas as pd
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class TelemetryStorageEngine:
    """Mock storage engine - replace with your actual implementation"""
    def __init__(self):
        pass
    
    def log_reading(self, data: Dict) -> bool:
        """Mock save function"""
        try:
            # In real implementation, you'd save to CSV/database here
            logging.info(f"📊 Saved weather data for {data.get('location_id', 'unknown')}")
            return True
        except Exception as e:
            logging.error(f"Failed to save: {e}")
            return False

class WeatherProcessor:
    """Weather monitoring backend - uses Open-Meteo API"""
    
    def __init__(self, file_path: str = 'test_logs/daily_telemetry.csv'):
        self.base_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
        self.file_path = file_path
        
        # SAFELY load the CSV file
        if os.path.exists(file_path):
            self.df = pd.read_csv(file_path)
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        else:
            # Create empty DataFrame if file doesn't exist
            self.df = pd.DataFrame(columns=[
                "timestamp", "location_id", "temp_c", "humidity_pct", 
                "wind_kph", "condition", "pressure_hpa"
            ])
            logging.warning(f"⚠️ File {file_path} not found. Created empty DataFrame.")
        
        self.storage = TelemetryStorageEngine()
        logging.info("✅ WeatherBackend initialized with Open-Meteo (free API)")

    def _find_city_coordinates(self, city: str) -> Dict:
        """Convert city name to latitude and longitude"""
        params = {
            'name': city,
            'count': 1,
            'language': 'en',
            'format': 'json'
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return {'success': False, 'error': "Geocoding service error"}
            
            data = response.json()
            
            if not data.get('results'):
                return {'success': False, 'error': f"City '{city}' not found"}
            
            result = data['results'][0]
            
            return {
                'success': True,
                'name': result['name'],
                'country': result.get('country', 'Unknown'),
                'latitude': result['latitude'],
                'longitude': result['longitude']
            }
            
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': "Network error - check internet"}
        except Exception as e:
            return {'success': False, 'error': f"Error: {str(e)}"}

    def description(self, weather_code: int) -> str:
        """Convert WMO weather codes to human-readable descriptions"""
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        
        return weather_codes.get(weather_code, f"Unknown ({weather_code})")

    def _save_weather_data(self, weather_data: Dict) -> None:
        """Save weather data to CSV using storage engine"""
        telemetry_data = {
            'location_id': f"{weather_data['city']}, {weather_data['country']}",
            'temp_c': weather_data['temperature'],
            'humidity_pct': weather_data['humidity'],
            'wind_kph': weather_data['wind_speed'] * 3.6,
            'condition': weather_data['condition']
        }
        
        if weather_data.get('pressure') != 'N/A':
            telemetry_data['pressure_hpa'] = weather_data['pressure']
        
        success = self.storage.log_reading(telemetry_data)
        if success:
            logging.info(f"📊 Saved weather data for {weather_data['city']}")

    def get_current_weather(self, city: str) -> Dict:
        """Fetch current weather for ONE city using Open-Meteo"""
        location = self._find_city_coordinates(city)
        
        if not location['success']:
            return {
                'success': False,
                'error': location['error']
            }
        
        params = {
            'latitude': location['latitude'],
            'longitude': location['longitude'],
            'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,pressure_msl',
            'timezone': 'auto'
        }
        
        try:
            response = requests.get(self.weather_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            current = data['current']
            
            weather_description = self.description(current['weather_code'])
            
            weather_info = {
                'success': True,
                'city': location['name'],
                'country': location['country'],
                'temperature': current['temperature_2m'],
                'feels_like': current['apparent_temperature'],
                'humidity': current['relative_humidity_2m'],
                'pressure': current.get('pressure_msl', 'N/A'),
                'condition': weather_description,
                'wind_speed': current['wind_speed_10m'],
                'timestamp': datetime.now().isoformat()
            }
            
            self._save_weather_data(weather_info)
            return weather_info
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }

    def compare_cities(self, city1: str, city2: str) -> Dict:
        """Compare weather between two cities"""
        weather1 = self.get_current_weather(city1)
        weather2 = self.get_current_weather(city2)
        
        if not weather1['success']:
            return {
                'success': False,
                'error': f"Couldn't get data for {city1}: {weather1['error']}"
            }
        
        if not weather2['success']:
            return {
                'success': False,
                'error': f"Couldn't get data for {city2}: {weather2['error']}"
            }
        
        temp_diff = weather1['temperature'] - weather2['temperature']
        humidity_diff = weather1['humidity'] - weather2['humidity']
        
        pressure1 = weather1['pressure'] if weather1['pressure'] != 'N/A' else None
        pressure2 = weather2['pressure'] if weather2['pressure'] != 'N/A' else None
        pressure_diff = pressure1 - pressure2 if (pressure1 and pressure2) else None
        
        warmer = weather1['city'] if temp_diff > 0 else weather2['city']
        more_humid = weather1['city'] if humidity_diff > 0 else weather2['city']
        
        return {
            'success': True,
            'city1': {
                'name': weather1['city'],
                'temp': weather1['temperature'],
                'humidity': weather1['humidity'],
                'pressure': weather1['pressure'],
                'condition': weather1['condition']
            },
            'city2': {
                'name': weather2['city'],
                'temp': weather2['temperature'],
                'humidity': weather2['humidity'],
                'pressure': weather2['pressure'],
                'condition': weather2['condition']
            },
            'comparison': {
                'warmer_city': warmer,
                'temperature_gap': abs(temp_diff),
                'more_humid_city': more_humid,
                'humidity_gap': abs(humidity_diff),
                'pressure_difference': pressure_diff
            }
        }

    def find_extremes(self):
        """Show hottest/coldest day from stored data."""
        if len(self.df) == 0:
            print("No data available for extreme analysis")
            return {'success': False, 'error': 'No data available'}
        
        hottest_idx = self.df['temp_c'].idxmax()
        coldest_idx = self.df['temp_c'].idxmin()
        
        hottest = self.df.iloc[hottest_idx]
        coldest = self.df.iloc[coldest_idx]
        
        print("--- PEAK DETECTION (Extremes) ---")
        print(f"Hottest: {hottest['temp_c']}°C at {hottest['timestamp']} ({hottest['location_id']})")
        print(f"Coldest: {coldest['temp_c']}°C at {coldest['timestamp']} ({coldest['location_id']})\n")
        
        return {
            'success': True,
            'hottest': {
                'temperature': hottest['temp_c'],
                'city': hottest['location_id'],
                'timestamp': str(hottest['timestamp'])
            },
            'coldest': {
                'temperature': coldest['temp_c'],
                'city': coldest['location_id'],
                'timestamp': str(coldest['timestamp'])
            }
        }

    def calculate_trends(self, limit: int = 5):
        """Weather trend analysis."""
        if len(self.df) < 2:
            print("Not enough data for trend analysis")
            return {
                'success': False,
                'error': 'Not enough data for trend analysis'
            }
        
        # Create a copy to avoid modifying original
        df_copy = self.df.copy()
        df_copy['temp_slope'] = df_copy['temp_c'].diff()
        df_copy['smooth_signal'] = df_copy['temp_c'].rolling(window=min(3, len(df_copy))).mean()
        
        print("--- TREND ANALYSIS ---")
        print(df_copy[['timestamp', 'temp_c', 'temp_slope', 'smooth_signal']].tail(limit))
        
        last_entries = df_copy.tail(limit)
        trends = []
        
        for _, row in last_entries.iterrows():
            trends.append({
                'timestamp': str(row['timestamp']),
                'temperature': float(row['temp_c']),
                'slope': float(row['temp_slope']) if not pd.isna(row['temp_slope']) else 0,
                'smooth_signal': float(row['smooth_signal']) if not pd.isna(row['smooth_signal']) else float(row['temp_c'])
            })
        
        # Calculate overall trend
        if len(trends) >= 2:
            first_temp = trends[0]['temperature']
            last_temp = trends[-1]['temperature']
            overall_change = last_temp - first_temp
            
            if overall_change > 0:
                overall_trend = 'increasing'
            elif overall_change < 0:
                overall_trend = 'decreasing'
            else:
                overall_trend = 'stable'
        else:
            overall_trend = 'insufficient_data'
            overall_change = 0
        
        return {
            'success': True,
            'trends': trends,
            'overall_trend': overall_trend,
            'temperature_change': overall_change,
            'total_records': len(self.df),
            'last_updated': str(self.df['timestamp'].max()) if len(self.df) > 0 else None
        }

def main():
    """Main menu function"""
    processor = WeatherProcessor('test_logs/daily_telemetry.csv')
    
    while True:
        print("\n" + "=" * 60)
        print("🎯 WEATHER MONITORING SYSTEM")
        print("=" * 60)
        print("1. Show Weather Report")
        print("2. Compare Two Cities")
        print("3. Show Hottest/Coldest Days")
        print("4. Weather Trend Analysis")
        print("5. Exit")
        print("-" * 60)
        
        try:
            choice = int(input("Choose an option (1-5): "))
            
            if choice == 1:
                city = input("Enter city name: ").strip()
                if city:
                    result = processor.get_current_weather(city)
                    if result['success']:
                        print(f"\n📍 {result['city']}, {result['country']}")
                        print(f"🌡️ Temperature: {result['temperature']}°C")
                        print(f"💧 Humidity: {result['humidity']}%")
                        print(f"☁️ Condition: {result['condition']}")
                    else:
                        print(f"❌ Error: {result['error']}")
                else:
                    print("❌ Please enter a valid city name")
                    
            elif choice == 2:
                city1 = input("Enter first city: ").strip()
                city2 = input("Enter second city: ").strip()
                if city1 and city2:
                    result = processor.compare_cities(city1, city2)
                    if result['success']:
                        print(f"\n🆚 COMPARISON: {city1.upper()} vs {city2.upper()}")
                        print(f"📍 {result['city1']['name']}: {result['city1']['temp']}°C")
                        print(f"📍 {result['city2']['name']}: {result['city2']['temp']}°C")
                        print(f"🔥 {result['comparison']['warmer_city']} is warmer by {result['comparison']['temperature_gap']:.1f}°C")
                    else:
                        print(f"❌ Error: {result['error']}")
                else:
                    print("❌ Please enter valid city names")
                    
            elif choice == 3:
                processor.find_extremes()
                
            elif choice == 4:
                try:
                    limit = int(input("How many trend entries to show? (default 5): ") or 5)
                    processor.calculate_trends(limit=limit)
                except ValueError:
                    print("❌ Please enter a valid number")
                    
            elif choice == 5:
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-5")
                
        except ValueError:
            print("❌ Please enter a valid number")

if __name__ == "__main__":
    main()
