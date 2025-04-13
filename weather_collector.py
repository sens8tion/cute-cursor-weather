import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class WeatherCollector:
    def __init__(self):
        self.api_key = os.getenv('WUNDERGROUND_API_KEY')
        self.station_id = os.getenv('STATION_ID')
        self.base_url = "https://api.weather.com/v2/pws/history/all"
        self.station_metadata = self.get_station_metadata()
        
    def get_station_metadata(self):
        """Fetch metadata about the weather station"""
        try:
            metadata_url = "https://api.weather.com/v2/pws/observations/current"
            params = {
                'stationId': self.station_id,
                'format': 'json',
                'units': 'e',
                'apiKey': self.api_key,
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(metadata_url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if 'observations' in data and len(data['observations']) > 0:
                station = data['observations'][0]
                return {
                    'name': station.get('neighborhood', 'Unknown Location'),
                    'city': station.get('city', 'Unknown City'),
                    'country': station.get('country', 'Unknown Country'),
                    'latitude': station.get('lat'),
                    'longitude': station.get('lon'),
                    'elevation': station.get('elevation')
                }
            return None
            
        except Exception as e:
            print(f"Error fetching station metadata: {e}")
            return None
            
    def get_location_string(self):
        """Get a formatted location string for the weather station"""
        if self.station_metadata:
            return f"{self.station_metadata['name']}, {self.station_metadata['city']}, {self.station_metadata['country']}"
        return "Marsden, West Yorkshire, UK"  # Default location
        
    def get_weather_data(self, hours=2):
        """Fetch historical weather data for the specified hours"""
        try:
            # Calculate start and end times
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Format dates in YYYYMMDD format
            start_date = start_time.strftime('%Y%m%d')
            end_date = end_time.strftime('%Y%m%d')
            
            params = {
                'stationId': self.station_id,
                'format': 'json',
                'units': 'e',
                'apiKey': self.api_key,
                'numericPrecision': 'decimal',
                'date': start_date
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            print(f"Fetching data from {start_time} to {end_time}")
            print(f"Using station ID: {self.station_id}")
            
            response = requests.get(self.base_url, params=params, headers=headers)
            
            if response.status_code != 200:
                print(f"\nError Response ({response.status_code}):")
                print("Headers:", response.headers)
                print("Content:", response.text)
                response.raise_for_status()
            
            data = response.json()
            
            # Print the full API response structure for debugging
            print("\nFull API Response Structure:")
            print(json.dumps(data, indent=2))
            
            return self._process_data(data)
            
        except requests.exceptions.RequestException as e:
            print(f"\nError fetching weather data: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status code: {e.response.status_code}")
                print("Response headers:", e.response.headers)
                print("Response content:", e.response.text)
            return None
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            return None
            
    def _process_data(self, data):
        """Process the raw weather data into a more usable format"""
        if not data or 'observations' not in data:
            print("No observations found in response")
            if data:
                print("Response data:", data)
            return None
            
        processed_data = []
        for observation in data['observations']:
            try:
                # Print the raw observation data for debugging
                print("\nRaw observation data:")
                print(json.dumps(observation, indent=2))
                
                # Extract values with better error handling
                imperial = observation.get('imperial', {})
                
                # Convert timestamp to string for JSON serialization
                timestamp_str = datetime.fromtimestamp(observation['epoch']).strftime('%Y-%m-%d %H:%M:%S')
                
                weather_data = {
                    'timestamp': timestamp_str,
                    'temperature': imperial.get('tempAvg'),  # Will convert to Celsius
                    'humidity': observation.get('humidityAvg'),
                    'wind_speed': imperial.get('windspeedAvg'),  # Will convert to km/h
                    'wind_direction': observation.get('winddirAvg'),
                    'pressure': imperial.get('pressureMax'),  # Will convert to hPa
                    'precipitation_rate': imperial.get('precipRate'),  # Will convert to mm/hr
                    'uv_index': observation.get('uvHigh'),
                    'solar_radiation': observation.get('solarRadiationHigh')
                }
                
                # Convert imperial units to metric
                if weather_data['temperature'] is not None:
                    weather_data['temperature'] = (weather_data['temperature'] - 32) * 5/9  # F to C
                if weather_data['wind_speed'] is not None:
                    weather_data['wind_speed'] = weather_data['wind_speed'] * 1.60934  # mph to km/h
                if weather_data['pressure'] is not None:
                    weather_data['pressure'] = weather_data['pressure'] * 33.8639  # inHg to hPa
                if weather_data['precipitation_rate'] is not None:
                    weather_data['precipitation_rate'] = weather_data['precipitation_rate'] * 25.4  # in/hr to mm/hr
                
                # Print the extracted data for verification
                print("\nExtracted weather data:")
                print(json.dumps(weather_data, indent=2))
                
                processed_data.append(weather_data)
            except KeyError as e:
                print(f"Missing key in observation data: {e}")
                print("Observation data:", observation)
                continue
            
        return processed_data
        
    def save_to_csv(self, data, filename='weather_data.csv'):
        """Save weather data to a CSV file"""
        if data:
            # Convert the data to a DataFrame
            df = pd.DataFrame(data)
            
            # Save new data
            df.to_csv(filename, index=False)
            
            print(f"Weather data saved to {filename}")
        else:
            print("No data to save")

    def get_current_weather(self):
        """Get the most recent weather data"""
        try:
            # Fetch the last hour of data
            data = self.get_weather_data(hours=1)
            
            if data and len(data) > 0:
                # Return the most recent observation
                return data[-1]
            else:
                print("No recent weather data available")
                return None
                
        except Exception as e:
            print(f"Error getting current weather: {e}")
            return None

def main():
    collector = WeatherCollector()
    weather_data = collector.get_weather_data(hours=2)
    
    if weather_data:
        print(f"Collected {len(weather_data)} weather observations:")
        for observation in weather_data:
            print(f"\nObservation at {observation['timestamp']}:")
            for key, value in observation.items():
                if key != 'timestamp':
                    print(f"{key}: {value}")
            
        collector.save_to_csv(weather_data)
    else:
        print("Failed to fetch weather data")

if __name__ == "__main__":
    main() 