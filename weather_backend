"""
Weather Monitoring Backend Module
Uses Open-Meteo API (FREE, no API key needed!)
Handles API calls, displays weather, compares cities
"""

import requests
from datetime import datetime
from typing import Dict, List
import logging
from telemetry_storage_engine import TelemetryStorageEngine
import pandas as pd
from pathlib import Path

# Then add this class INSIDE your WeatherBackend class or as a separate integration

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class WeatherProcessor:
    #Weather monitoring backend - uses Open-Meteo API
    
    def __init__(self, file_path: str = None):
        self.base_url = "https://geocoding-api.open-meteo.com/v1/search"  # For city search
        self.weather_url = "https://api.open-meteo.com/v1/forecast"        # For weather data

         # Load the 'Bus' (Data) into RAM
        self.df = pd.read_csv(file_path)
    # Convert timestamp to a format the computer understands
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
    
        # Create the storage engine
        self.storage = TelemetryStorageEngine()
        logging.info("✅ WeatherBackend initialized with Open-Meteo (free API)")

    # ============ Helper: Find City Coordinates ============
    #For 1st feature 
    def _find_city_coordinates(self, city: str) -> Dict:
        """
        Convert city name to latitude and longitude
        Open-Meteo needs coordinates, not city names
        """
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
            
            # Get the first result
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
    #For 2nd feature
    def description(self, weather_code: int) -> str:
        """
        Convert WMO weather codes to human-readable descriptions
        Based on WMO code standards
        """
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
    #for saving data in a folder 
    def _save_weather_data(self, weather_data: Dict) -> None:
        """
        Internal function to save weather data to CSV
        This matches the format your friend's storage expects
        """
        # Format data for the storage engine
        telemetry_data = {
            'location_id': f"{weather_data['city']}, {weather_data['country']}",
            'temp_c': weather_data['temperature'],
            'humidity_pct': weather_data['humidity'],
            'wind_kph': weather_data['wind_speed'] * 3.6,  # Convert m/s to km/h
            'condition': weather_data['condition']
        }
        
        # Add pressure if available
        if weather_data['pressure'] != 'N/A':
            telemetry_data['pressure_hpa'] = weather_data['pressure']
        
        # Save it!
        success = self.storage.log_reading(telemetry_data)
        if success:
            logging.info(f"📊 Saved weather data for {weather_data['city']}")
        else:
            logging.warning(f"⚠️ Failed to save weather data for {weather_data['city']}")
    #Dont need display functions once we have UI/UX
    def display_weather(self, city: str) -> None:
        """
        Display weather in a nice readable format
        This is the "show to user" function
        """
        print("\n" + "=" * 50)
        print(f"🌤️  WEATHER REPORT: {city.upper()}")
        print("=" * 50)
        
        result = self.get_current_weather(city)
        
        if result['success']:
            # Show all the weather data
            print(f"📍 Location: {result['city']}, {result['country']}")
            print(f"🌡️  Temperature: {result['temperature']}°C")
            print(f"🤔 Feels like: {result['feels_like']}°C")
            print(f"💧 Humidity: {result['humidity']}%")
            
            if result['pressure'] != 'N/A':
                print(f"📊 Pressure: {result['pressure']} hPa")
            else:
                print(f"📊 Pressure: Not available")
                
            print(f"☁️  Condition: {result['condition']}")
            print(f"💨 Wind Speed: {result['wind_speed']} m/s ({result['wind_speed'] * 3.6:.1f} km/h)")
            print(f"🕐 Time: {result['timestamp']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        print("=" * 50)
       
    def display_comparison(self, city1: str, city2: str) -> None:
        """
        Display comparison in a nice readable format
        """
        print("\n" + "=" * 60)
        print(f"🆚 WEATHER COMPARISON: {city1.upper()} vs {city2.upper()}")
        print("=" * 60)
        
        result = self.compare_cities(city1, city2)
        
        if not result['success']:
            print(f"❌ {result['error']}")
            return
        
        # Show side-by-side comparison
        c1 = result['city1']
        c2 = result['city2']
        comp = result['comparison']
        
        # Table format
        print(f"\n{'Metric':<20} {c1['name']:<20} {c2['name']:<20}")
        print("-" * 60)
        print(f"{'Temperature':<20} {c1['temp']:>6}°C{' ':<12} {c2['temp']:>6}°C")
        print(f"{'Humidity':<20} {c1['humidity']:>6}%{' ':<12} {c2['humidity']:>6}%")
        
        # Handle pressure display
        pressure1_str = f"{c1['pressure']:.0f}hPa" if c1['pressure'] != 'N/A' else 'N/A'
        pressure2_str = f"{c2['pressure']:.0f}hPa" if c2['pressure'] != 'N/A' else 'N/A'
        print(f"{'Pressure':<20} {pressure1_str:>10}{' ':<8} {pressure2_str:>10}")
        
        print(f"{'Condition':<20} {c1['condition']:<20} {c2['condition']:<20}")
        
        # Show differences
        print("\n" + "=" * 60)
        print("📊 COMPARISON SUMMARY")
        print("=" * 60)
        
        print(f"🔥 {comp['warmer_city']} is warmer by {comp['temperature_gap']:.1f}°C")
        print(f"💧 {comp['more_humid_city']} is more humid by {comp['humidity_gap']:.1f}%")
        
        if comp['pressure_difference']:
            if comp['pressure_difference'] > 0:
                print(f"📊 {c1['name']} has higher pressure by {abs(comp['pressure_difference']):.0f} hPa")
            else:
                print(f"📊 {c2['name']} has higher pressure by {abs(comp['pressure_difference']):.0f} hPa")
        
        print("=" * 60)
    #Dont need display functions once we have UI/UX


    # ============ FEATURE 1: Get Weather ============
    def get_current_weather(self, city: str) -> Dict:
        """
        Fetch current weather for ONE city using Open-Meteo
        Returns: Dictionary with weather data or error
        """
        # Step 1: Find city coordinates
        location = self._find_city_coordinates(city)
        
        if not location['success']:
            return {
                'success': False,
                'error': location['error']
            }
        
        # Step 2: Get weather using coordinates
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
            
            #Convert weather code to description
            weather_description = self.description(current['weather_code'])
            
            #Build weather info
            weather_info = {
                'success': True,
                'city': location['name'],
                'country': location['country'],
                'temperature': current['temperature_2m'],
                'feels_like': current['apparent_temperature'],
                'humidity': current['relative_humidity_2m'],
                'pressure': current.get('pressure_msl', 'N/A'),  # Some locations may not have pressure
                'condition': weather_description,
                'wind_speed': current['wind_speed_10m'],
                'timestamp': datetime.now().isoformat()
            }
            
            # 🆕 SAVE to CSV using friend's storage engine
            self._save_weather_data(weather_info)
            
            return weather_info
            
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': "Network error - please check your internet connection"
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': "Request timed out - API took too long to respond"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    # ============ FEATURE 2: Compare Two Cities ============
    def compare_cities(self, city1: str, city2: str) -> Dict:
        """
        Compare weather between two cities
        Returns comparison dictionary
        """
        # Get weather for both cities
        weather1 = self.get_current_weather(city1)
        weather2 = self.get_current_weather(city2)
        
        # Check if both succeeded
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
        
        # Calculate comparisons
        temp_diff = weather1['temperature'] - weather2['temperature']
        humidity_diff = weather1['humidity'] - weather2['humidity']
        
        # Handle pressure (if available)
        pressure1 = weather1['pressure'] if weather1['pressure'] != 'N/A' else None
        pressure2 = weather2['pressure'] if weather2['pressure'] != 'N/A' else None
        pressure_diff = pressure1 - pressure2 if (pressure1 and pressure2) else None
        
        # Determine which is warmer
        warmer = city1 if temp_diff > 0 else city2
        temp_diff_abs = abs(temp_diff)
        
        # Determine which is more humid
        more_humid = city1 if humidity_diff > 0 else city2
        humidity_diff_abs = abs(humidity_diff)
        
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
                'temperature_difference': temp_diff,
                'warmer_city': warmer,
                'temperature_gap': temp_diff_abs,
                'humidity_difference': humidity_diff,
                'more_humid_city': more_humid,
                'humidity_gap': humidity_diff_abs,
                'pressure_difference': pressure_diff
            }
        }

    #============FEATURE 3: ============
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

    #============FEATURE 4: ============
    def calculate_trends(self, limit:int = 5):
        """Task: Weather trend analysis."""
        # DISCRETE DERIVATIVE: Calculate Delta Temp between readings
        self.df['temp_slope'] = self.df['temp_c'].diff()

        # SIGNAL SMOOTHING: 3-hour moving average to remove 'noise'
        self.df['smooth_signal'] = self.df['temp_c'].rolling(window=3).mean()

        print("--- TREND ANALYSIS (Last 5 Samples) ---")
        # Showing the Timestamp, Temp, the Slope, and the Smoothed Signal
        print(self.df[['timestamp', 'temp_c', 'temp_slope', 'smooth_signal']].tail())


        # Check if we have data
        if self.df is None or len(self.df) < 2:
            return {
                'success': False,
                'error': 'Not enough data for trend analysis'
            }
        
        try:
            last_entries = self.df.tail(limit)
        except Exception as e:
            return {
                'success': False,
                'error': f'Error accessing data: {str(e)}'
            }
            
        # Build list of trends for UI
        trends = []
        for _, row in last_entries.iterrows():
            trends.append({
                'timestamp': str(row['timestamp']),
                'temperature': float(row['temp_c']),
                'slope': float(row['temp_slope']) if not pd.isna(row['temp_slope']) else 0,
                'smooth_signal': float(row['smooth_signal']) if not pd.isna(row['smooth_signal']) else float(row['temp_c'])
            })

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
        
        # Return data for UI
        return {
            'success': True,
            'trends': trends,
            'overall_trend': overall_trend,
            'temperature_change': overall_change,
            'total_records': len(self.df),
            'last_updated': str(self.df['timestamp'].max()) if len(self.df) > 0 else None
        }



# ============ TEST YOUR CODE ============
#Dont need mainMenu and Input Function once we have UI/UX
def mainMenu():
        print("1.Show Weather Report:")
        print("2.Compare two cities weather report")
        print("3.Show hottest/coldest day from stored data")
        print("4.Weather trend analysis ")
        print("5.END")
        choose = int(input("Choose between 1-4"))
        return choose

def INPUT():
        while True:
            choose = mainMenu()
            if(choose == 1):
                City1 = input("Enter City name")
                City1 = City1.strip()
                if City1:
                    # Test Feature 1: Display weather
                    print("\n📋 TEST 1: Display Weather")
                    print("-" * 30)
                    processor.display_weather(City1)
            if(choose == 2):
                City2 = input("Enter first City to compare")
                City2 = City2.strip()
                City3 = input("Enter other City to compare")
                City3 = City3.strip()
                    
                if City2 and City3:
                        # Test Feature 2: Compare cities
                    print("\n📋 TEST 2: Compare Cities")
                    print("-" * 30)
                    processor.display_comparison(City2,City3)
            if(choose == 3):
                processor.find_extremes()
            if(choose == 4):
                x = int(input("How many trends"))
                processor.calculate_trends(limit=x)
            if(choose == 5):
                break
if __name__ == "__main__":
    # Power on the processor
    processor = WeatherProcessor('test_logs/daily_telemetry.csv')
    print("\n" + "🎯 WEATHER BACKEND TEST (Open-Meteo - FREE)".center(60))
    print("=" * 60)
    INPUT()
