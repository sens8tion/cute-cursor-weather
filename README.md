# Weather Data Collection and Visualization

This project collects weather data from a Davis Vantage Pro2 weather station and visualizes it using Python. The system fetches real-time weather observations and creates comprehensive visualizations of various weather parameters.

## Features

- Real-time weather data collection from Davis Vantage Pro2
- Automatic data storage in CSV format
- Comprehensive weather visualizations including:
  - Temperature (°C)
  - Humidity (%)
  - Wind Speed (km/h)
  - Wind Direction (degrees)
  - Barometric Pressure (hPa)
  - Precipitation Rate (mm/hr)
  - UV Index
  - Solar Radiation (W/m²)
- Data cleaning and validation
- Time-series visualization of all parameters

## Requirements

- Python 3.x
- Required Python packages:
  - requests
  - pandas
  - matplotlib
  - numpy
  - datetime

## Installation

1. Clone this repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the weather collector:
   ```bash
   python weather_collector.py
   ```
   This will collect weather data and save it to `weather_data.csv`

2. Generate visualizations:
   ```bash
   python weather_visualizer.py
   ```
   This will create a comprehensive visualization saved as `weather_analysis.png`

## Weather Parameters

- **Temperature**: Air temperature in degrees Celsius (°C)
- **Humidity**: Relative humidity as a percentage (%)
- **Wind Speed**: Average wind speed in kilometers per hour (km/h)
- **Wind Direction**: Wind direction in degrees (0° = North, 90° = East, 180° = South, 270° = West)
- **Pressure**: Barometric pressure in hectopascals (hPa)
- **Precipitation Rate**: Rate of rainfall in millimeters per hour (mm/hr)
- **UV Index**: Measure of ultraviolet radiation intensity (0-11+ scale)
- **Solar Radiation**: Solar energy flux in watts per square meter (W/m²)

## Data Format

The collected data is stored in CSV format with the following columns:
- timestamp: ISO format datetime
- temperature: °C
- humidity: %
- wind_speed: km/h
- wind_direction: degrees
- pressure: hPa
- precipitation_rate: mm/hr
- uv_index: unitless
- solar_radiation: W/m²

## Visualization

The visualization script creates a multi-panel plot showing:
- Time series of all weather parameters
- Clear axis labels with metric units
- Proper scaling for each parameter
- Timestamp-based x-axis

## Notes

- The weather station must be properly configured and accessible
- Data collection interval is approximately 5 minutes
- All measurements are in metric units
- The visualization shows the last 2 hours of data by default

## Building and Testing

### Windows
Run the PowerShell build script:
```powershell
.\build.ps1
```