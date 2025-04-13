import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
import os
import json
import requests
from typing import Dict, Any
import numpy as np

# LLM configuration
LLM_CONFIG = {
    "endpoint": "http://localhost:1234/v1/chat/completions",
    "model": "local-model",
    "temperature": 0.7,
    "max_tokens": 150,
    "timeout": 300,
    "stream": False
}

def get_llm_response(weather_data: Dict[str, Any]) -> str:
    """Get a natural language summary from the LLM."""
    try:
        prompt = f"""You are a group of cute Yorkshire weather characters reporting on the local weather. The characters are:
1. 🌄 Moorland Mary - A cheerful sheep farmer who loves sunny days and counting her sheep
2. 🌧️ Valley Val - A bit gloomy but cozy character who enjoys rainy weather and carrying umbrellas
3. 💨 Windy Wendy - An energetic character who gets excited about strong winds and flying kites
4. ❄️ Snowy Sarah - A calm, cool character who loves cold weather and making snowmen

Current weather conditions:
Temperature: {weather_data['temperature']:.1f}°C
Humidity: {weather_data['humidity']:.0f}%
Wind: {weather_data['wind_speed']:.1f} km/h from {weather_data['wind_direction']}°
Pressure: {weather_data['pressure']:.1f} hPa
UV Index: {weather_data['uv_index']}
Solar Radiation: {weather_data['solar_radiation']:.0f} W/m²
Rain Rate: {weather_data['precipitation_rate']:.1f} mm/hr

Please provide a cute and sarcastic weather report from the perspective of these Yorkshire characters, with each one commenting on their favorite weather conditions. Keep it brief but make it entertaining!"""

        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": LLM_CONFIG["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": LLM_CONFIG["temperature"],
            "max_tokens": LLM_CONFIG["max_tokens"],
            "stream": LLM_CONFIG["stream"]
        }

        response = requests.post(
            LLM_CONFIG["endpoint"],
            headers=headers,
            json=payload,
            timeout=LLM_CONFIG["timeout"]
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return "Error: Unexpected response format from LLM"
        else:
            return f"Error: Failed to get response from LLM (Status code: {response.status_code})"
            
    except Exception as e:
        return f"Error: {str(e)}"

def calculate_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate weather statistics from the DataFrame."""
    if df.empty:
        return {}
    
    # Get the most recent data point for current conditions
    current = df.iloc[-1]
    
    # Calculate time period
    start_time = df['timestamp'].min()
    end_time = df['timestamp'].max()
    duration_hours = (end_time - start_time).total_seconds() / 3600
    
    # Calculate statistics
    stats = {
        "data_period": {
            "start": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_hours": duration_hours
        },
        "current_conditions": {
            "temperature": f"{current['temperature']:.1f}°C",
            "humidity": f"{current['humidity']:.0f}%",
            "wind_speed": f"{current['wind_speed']:.1f} km/h",
            "wind_direction": f"{current['wind_direction']}°",
            "pressure": f"{current['pressure']:.1f} hPa",
            "precipitation_rate": f"{current['precipitation_rate']:.1f} mm/hr",
            "uv_index": current['uv_index'],
            "solar_radiation": f"{current['solar_radiation']:.0f} W/m²"
        },
        "statistics": {
            "temperature": {
                "min": f"{df['temperature'].min():.1f}°C",
                "max": f"{df['temperature'].max():.1f}°C",
                "average": f"{df['temperature'].mean():.1f}°C",
                "trend": "warming" if df['temperature'].iloc[-1] > df['temperature'].iloc[0] else "cooling"
            },
            "humidity": {
                "min": f"{df['humidity'].min():.0f}%",
                "max": f"{df['humidity'].max():.0f}%",
                "average": f"{df['humidity'].mean():.0f}%"
            },
            "wind": {
                "max_speed": f"{df['wind_speed'].max():.1f} km/h",
                "average_speed": f"{df['wind_speed'].mean():.1f} km/h"
            },
            "pressure": {
                "min": f"{df['pressure'].min():.1f} hPa",
                "max": f"{df['pressure'].max():.1f} hPa",
                "trend": "rising" if df['pressure'].iloc[-1] > df['pressure'].iloc[0] else "falling"
            },
            "precipitation": {
                "max_rate": f"{df['precipitation_rate'].max():.1f} mm/hr",
                "average_rate": f"{df['precipitation_rate'].mean():.1f} mm/hr"
            },
            "uv": {
                "max": df['uv_index'].max(),
                "average": f"{df['uv_index'].mean():.1f}"
            },
            "solar": {
                "max": f"{df['solar_radiation'].max():.0f} W/m²",
                "average": f"{df['solar_radiation'].mean():.0f} W/m²"
            }
        }
    }
    return stats

def visualize_weather_data(csv_file='weather_data.csv'):
    try:
        # Check if file exists
        if not os.path.exists(csv_file):
            print(f"Error: File '{csv_file}' not found!")
            return
        
        # Read the CSV file
        print(f"Reading data from {csv_file}...")
        df = pd.read_csv(csv_file)
        
        # Print data info for debugging
        print("\nDataFrame Info:")
        print(df.info())
        print("\nFirst few rows of data:")
        print(df.head())
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Drop rows where all values are NaN except timestamp and precipitation_rate
        df = df.dropna(subset=['temperature', 'humidity', 'wind_speed', 'wind_direction', 
                              'pressure', 'uv_index', 'solar_radiation'], how='all')
        
        if len(df) == 0:
            print("\nNo valid data points found after cleaning NaN values!")
            return
            
        print(f"\nFound {len(df)} valid data points after cleaning")
        
        # Calculate statistics for LLM summary
        stats = calculate_statistics(df)
        
        # Get LLM summary
        print("\nGenerating weather summary...")
        summary = get_llm_response(stats)
        print("\nWeather Summary:")
        print(summary)
        
        # Create a figure with subplots
        print("\nCreating plots...")
        fig, axes = plt.subplots(4, 2, figsize=(15, 15))
        fig.suptitle('Weather Data Analysis', fontsize=16)
        
        # Flatten the axes array for easier iteration
        axes = axes.flatten()
        
        # Define metrics and their units
        metrics = [
            ('temperature', 'Temperature (°C)'),
            ('humidity', 'Humidity (%)'),
            ('wind_speed', 'Wind Speed (km/h)'),
            ('wind_direction', 'Wind Direction (degrees)'),
            ('pressure', 'Pressure (hPa)'),
            ('precipitation_rate', 'Precipitation Rate (mm/hr)'),
            ('uv_index', 'UV Index'),
            ('solar_radiation', 'Solar Radiation (W/m²)')
        ]
        
        # Create plots for each metric
        for i, (metric, ylabel) in enumerate(metrics):
            print(f"Plotting {metric}...")
            ax = axes[i]
            
            # Check if column exists and has data
            if metric not in df.columns:
                print(f"Warning: Column '{metric}' not found in data!")
                continue
                
            if df[metric].isna().all():
                print(f"Warning: No data available for {metric}")
                continue
                
            # Plot the data
            ax.plot(df['timestamp'], df[metric], marker='o', linestyle='-', linewidth=1)
            
            # Format the x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Set labels and title
            ax.set_xlabel('Time')
            ax.set_ylabel(ylabel)
            ax.set_title(f'{ylabel} Over Time')
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Format y-axis to show all values
            ax.tick_params(axis='y', which='both', labelleft=True)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save the plot
        print("\nSaving plot to 'weather_analysis.png'...")
        plt.savefig('weather_analysis.png', dpi=300, bbox_inches='tight')
        print("Plot saved successfully!")
        
        # Show the plot
        print("\nDisplaying plot...")
        plt.show()
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("\nPlease check if you have matplotlib installed:")
        print("pip install matplotlib")

if __name__ == "__main__":
    visualize_weather_data() 