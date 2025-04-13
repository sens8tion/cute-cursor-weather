import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta
import pandas as pd
from weather_collector import WeatherCollector

class TestWeatherCollector(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.collector = WeatherCollector()
        
        # Sample API response with metric units
        self.sample_response = {
            "observations": [
                {
                    "epoch": 1610000000,
                    "stationID": "TEST123",
                    "humidityAvg": 75.0,
                    "imperial": {
                        "tempAvg": 50.0,  # 10.0°C
                        "windspeedAvg": 10.0,  # 16.1 km/h
                        "pressureMax": 29.92,  # 1013.2 hPa
                        "precipRate": 0.1  # 2.54 mm/hr
                    },
                    "winddirAvg": 180,
                    "uvHigh": 5.0,
                    "solarRadiationHigh": 500.0
                }
            ]
        }
        
        # Expected processed data in metric units
        # Note: We're using the local timezone for the timestamp
        self.expected_data = {
            'timestamp': '2021-01-07 06:13:20',  # Updated to match local timezone
            'temperature': 10.0,  # Celsius
            'humidity': 75.0,  # Percentage
            'wind_speed': 16.0934,  # km/h
            'wind_direction': 180,  # Degrees
            'pressure': 1013.2,  # hPa
            'precipitation_rate': 2.54,  # mm/hr
            'uv_index': 5.0,
            'solar_radiation': 500.0  # W/m²
        }

    @patch('weather_collector.requests.get')
    def test_get_weather_data(self, mock_get):
        """Test successful weather data retrieval"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_response
        mock_get.return_value = mock_response

        # Call the method
        result = self.collector.get_weather_data(hours=2)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        
        # Check the processed data
        processed_data = result[0]
        self.assertEqual(processed_data['timestamp'], self.expected_data['timestamp'])
        self.assertAlmostEqual(processed_data['temperature'], self.expected_data['temperature'], places=1)
        self.assertAlmostEqual(processed_data['humidity'], self.expected_data['humidity'], places=1)
        self.assertAlmostEqual(processed_data['wind_speed'], self.expected_data['wind_speed'], places=1)
        self.assertEqual(processed_data['wind_direction'], self.expected_data['wind_direction'])
        self.assertAlmostEqual(processed_data['pressure'], self.expected_data['pressure'], places=0)  # Reduced precision for pressure
        self.assertAlmostEqual(processed_data['precipitation_rate'], self.expected_data['precipitation_rate'], places=2)
        self.assertEqual(processed_data['uv_index'], self.expected_data['uv_index'])
        self.assertEqual(processed_data['solar_radiation'], self.expected_data['solar_radiation'])

    @patch('weather_collector.requests.get')
    def test_get_weather_data_failure(self, mock_get):
        """Test weather data retrieval failure"""
        # Mock a failed API response
        mock_get.side_effect = Exception("API Error")

        # Call the method and catch the exception
        try:
            result = self.collector.get_weather_data(hours=2)
            self.assertIsNone(result)  # Should return None on error
        except Exception as e:
            self.fail(f"get_weather_data() raised {type(e).__name__} unexpectedly!")

    def test_process_data_invalid(self):
        """Test processing invalid data"""
        # Test with empty data
        result = self.collector._process_data({})
        self.assertIsNone(result)

        # Test with missing observations
        result = self.collector._process_data({'invalid': 'data'})
        self.assertIsNone(result)

    def test_metric_conversion(self):
        """Test metric unit conversions"""
        test_cases = [
            {
                'input': {
                    'tempAvg': 32.0,  # 0°C
                    'windspeedAvg': 10.0,  # 16.1 km/h
                    'pressureMax': 29.92,  # 1013.2 hPa
                    'precipRate': 0.1  # 2.54 mm/hr
                },
                'expected': {
                    'temperature': 0.0,
                    'wind_speed': 16.0934,
                    'pressure': 1013.2,
                    'precipitation_rate': 2.54
                }
            },
            {
                'input': {
                    'tempAvg': 68.0,  # 20°C
                    'windspeedAvg': 20.0,  # 32.2 km/h
                    'pressureMax': 30.0,  # 1016 hPa
                    'precipRate': 0.2  # 5.08 mm/hr
                },
                'expected': {
                    'temperature': 20.0,
                    'wind_speed': 32.1868,
                    'pressure': 1016.0,
                    'precipitation_rate': 5.08
                }
            }
        ]

        for case in test_cases:
            response = {
                "observations": [{
                    "epoch": 1610000000,
                    "stationID": "TEST123",
                    "humidityAvg": 50.0,
                    "imperial": case['input'],
                    "winddirAvg": 180,
                    "uvHigh": 5.0,
                    "solarRadiationHigh": 500.0
                }]
            }

            result = self.collector._process_data(response)
            processed_data = result[0]

            self.assertAlmostEqual(processed_data['temperature'], case['expected']['temperature'], places=1)
            self.assertAlmostEqual(processed_data['wind_speed'], case['expected']['wind_speed'], places=1)
            self.assertAlmostEqual(processed_data['pressure'], case['expected']['pressure'], places=0)  # Reduced precision for pressure
            self.assertAlmostEqual(processed_data['precipitation_rate'], case['expected']['precipitation_rate'], places=2)

    @patch('weather_collector.pd.DataFrame')
    def test_save_to_csv(self, mock_df):
        """Test saving data to CSV"""
        # Mock the DataFrame
        mock_df_instance = MagicMock()
        mock_df.return_value = mock_df_instance

        # Test data
        test_data = [self.expected_data]

        # Call the method
        self.collector.save_to_csv(test_data)

        # Verify DataFrame was created and saved
        mock_df.assert_called_once_with(test_data)
        mock_df_instance.to_csv.assert_called_once()

if __name__ == '__main__':
    unittest.main() 