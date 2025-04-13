import pandas as pd
import json
import requests
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any, List, Tuple
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Station configuration
STATION_CONFIG = {
    "name": "Davis Vantage Pro2",
    "location": "Test Location",
    "latitude": 0.0,  # Replace with actual latitude
    "longitude": 0.0,  # Replace with actual longitude
    "elevation": 0,    # Replace with actual elevation in meters
}

# LLM configuration
LLM_CONFIG = {
    "endpoint": "http://localhost:1234/v1/chat/completions",
    "model": "local-model",  # This will be ignored by LM Studio but is required
    "temperature": 0.7,
    "max_tokens": 150,  # Further reduced token count
    "timeout": 300,  # 5 minutes timeout
    "stream": False
}

def read_weather_data(file_path: str = "weather_data.csv") -> pd.DataFrame:
    """Read weather data from CSV file."""
    try:
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        print(f"Error reading weather data: {e}")
        return pd.DataFrame()

def calculate_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate weather statistics from the DataFrame."""
    if df.empty:
        return {}
    
    stats = {
        "time_period": {
            "start": df['timestamp'].min().strftime("%Y-%m-%d %H:%M:%S"),
            "end": df['timestamp'].max().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_hours": (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
        },
        "temperature": {
            "current": f"{df['temperature'].iloc[-1]:.1f}°C",
            "min": f"{df['temperature'].min():.1f}°C",
            "max": f"{df['temperature'].max():.1f}°C",
            "average": f"{df['temperature'].mean():.1f}°C",
            "trend": "warming" if df['temperature'].iloc[-1] > df['temperature'].iloc[0] else "cooling"
        },
        "humidity": {
            "current": f"{df['humidity'].iloc[-1]:.0f}%",
            "min": f"{df['humidity'].min():.0f}%",
            "max": f"{df['humidity'].max():.0f}%",
            "average": f"{df['humidity'].mean():.0f}%"
        },
        "wind": {
            "current_speed": f"{df['wind_speed'].iloc[-1]:.1f} km/h",
            "current_direction": f"{df['wind_direction'].iloc[-1]}°",
            "max_speed": f"{df['wind_speed'].max():.1f} km/h",
            "average_speed": f"{df['wind_speed'].mean():.1f} km/h"
        },
        "pressure": {
            "current": f"{df['pressure'].iloc[-1]:.1f} hPa",
            "min": f"{df['pressure'].min():.1f} hPa",
            "max": f"{df['pressure'].max():.1f} hPa",
            "trend": "rising" if df['pressure'].iloc[-1] > df['pressure'].iloc[0] else "falling"
        },
        "precipitation": {
            "current_rate": f"{df['precipitation_rate'].iloc[-1]:.1f} mm/hr",
            "max_rate": f"{df['precipitation_rate'].max():.1f} mm/hr",
            "average_rate": f"{df['precipitation_rate'].mean():.1f} mm/hr"
        },
        "uv": {
            "current": df['uv_index'].iloc[-1],
            "max": df['uv_index'].max(),
            "average": f"{df['uv_index'].mean():.1f}"
        },
        "solar": {
            "current": f"{df['solar_radiation'].iloc[-1]:.0f} W/m²",
            "max": f"{df['solar_radiation'].max():.0f} W/m²",
            "average": f"{df['solar_radiation'].mean():.0f} W/m²"
        }
    }
    return stats

def format_weather_data(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Format weather data into a structured report."""
    return {
        "station_info": STATION_CONFIG,
        "data_period": stats["time_period"],
        "current_conditions": {
            "temperature": stats["temperature"]["current"],
            "humidity": stats["humidity"]["current"],
            "wind_speed": stats["wind"]["current_speed"],
            "wind_direction": stats["wind"]["current_direction"],
            "pressure": stats["pressure"]["current"],
            "precipitation_rate": stats["precipitation"]["current_rate"],
            "uv_index": stats["uv"]["current"],
            "solar_radiation": stats["solar"]["current"]
        },
        "statistics": {
            "temperature": {k: v for k, v in stats["temperature"].items() if k != "current"},
            "humidity": {k: v for k, v in stats["humidity"].items() if k != "current"},
            "wind": {k: v for k, v in stats["wind"].items() if k not in ["current_speed", "current_direction"]},
            "pressure": {k: v for k, v in stats["pressure"].items() if k != "current"},
            "precipitation": {k: v for k, v in stats["precipitation"].items() if k != "current_rate"},
            "uv": {k: v for k, v in stats["uv"].items() if k != "current"},
            "solar": {k: v for k, v in stats["solar"].items() if k != "current"}
        }
    }

def test_llm_connection() -> bool:
    """Test if the LLM endpoint is available."""
    try:
        print(f"Testing connection to {LLM_CONFIG['endpoint']}...")
        response = requests.get(LLM_CONFIG["endpoint"].replace("/chat/completions", ""), timeout=5)
        print(f"Connection test response: {response.status_code}")
        if response.status_code == 200:
            print("Successfully connected to LM Studio!")
            # Try to get GPU info from LM Studio
            try:
                gpu_info = requests.get(LLM_CONFIG["endpoint"].replace("/chat/completions", "/gpu"), timeout=5)
                if gpu_info.status_code == 200:
                    print(f"GPU Info: {gpu_info.text}")
                else:
                    print("Note: Running on CPU - responses may be slower")
            except:
                print("Note: Running on CPU - responses may be slower")
            return True
        else:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection test failed: {str(e)}")
        return False

def get_llm_response(weather_data: Dict[str, Any]) -> str:
    """Get a natural language summary from the LLM."""
    if not test_llm_connection():
        return "Error: Could not connect to LM Studio. Please ensure it is running and the server is started."
    
    try:
        # Ultra-concise prompt for faster CPU processing
        prompt = f"""Weather at {weather_data['station_info']['location']}:
Now: {weather_data['current_conditions']['temperature']}, {weather_data['current_conditions']['humidity']} humidity
Wind: {weather_data['current_conditions']['wind_speed']} from {weather_data['current_conditions']['wind_direction']}°
Pressure: {weather_data['current_conditions']['pressure']} ({weather_data['statistics']['pressure']['trend']})
UV: {weather_data['current_conditions']['uv_index']}

Past {round(weather_data['data_period']['duration_hours'], 1)}h:
Temp: {weather_data['statistics']['temperature']['min']} to {weather_data['statistics']['temperature']['max']} ({weather_data['statistics']['temperature']['trend']})
Humidity: {weather_data['statistics']['humidity']['min']} to {weather_data['statistics']['humidity']['max']}
Wind: up to {weather_data['statistics']['wind']['max_speed']}

Brief summary please."""

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

        print("\nSending request to LM Studio...")
        print(f"Using endpoint: {LLM_CONFIG['endpoint']}")
        print("Note: This may take a while if running on CPU...")
        print("Processing", end="", flush=True)
        
        response = requests.post(
            LLM_CONFIG["endpoint"],
            headers=headers,
            json=payload,
            timeout=LLM_CONFIG["timeout"]
        )
        
        print("\nResponse received!")
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return f"Error: Unexpected response format from LLM. Response: {response.text}"
        else:
            error_msg = f"Error: Failed to get response from LLM (Status code: {response.status_code})"
            if response.text:
                error_msg += f"\nResponse: {response.text}"
            return error_msg
            
    except requests.exceptions.Timeout:
        return "Error: Request to LM Studio timed out. The model is running on CPU which is slower. Try:\n1. Using a smaller model in LM Studio\n2. Enabling GPU acceleration in LM Studio\n3. Increasing the timeout value"
    except requests.exceptions.RequestException as e:
        return f"Error: Failed to connect to LLM endpoint ({str(e)})"
    except Exception as e:
        return f"Error: Unexpected error occurred ({str(e)})"

class WeatherReporterUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Reporter")
        self.root.geometry("800x600")
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create weather data display
        self.create_weather_display()
        
        # Create summary section
        self.create_summary_section()
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Initialize data
        self.weather_data = None
        self.update_weather_data()
        
        # Set up periodic updates
        self.root.after(300000, self.periodic_update)  # Update every 5 minutes

    def create_weather_display(self):
        # Current conditions frame
        current_frame = ttk.LabelFrame(self.main_frame, text="Current Conditions", padding="5")
        current_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Create labels for current conditions
        self.current_labels = {}
        conditions = [
            ("Temperature", "temperature"),
            ("Humidity", "humidity"),
            ("Wind Speed", "wind_speed"),
            ("Wind Direction", "wind_direction"),
            ("Pressure", "pressure"),
            ("UV Index", "uv_index"),
            ("Solar Radiation", "solar_radiation")
        ]
        
        for i, (label, key) in enumerate(conditions):
            ttk.Label(current_frame, text=f"{label}:").grid(row=i//2, column=(i%2)*2, sticky=tk.W)
            self.current_labels[key] = ttk.Label(current_frame, text="")
            self.current_labels[key].grid(row=i//2, column=(i%2)*2+1, sticky=tk.W)

    def create_summary_section(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self.main_frame, text="Weather Summary", padding="5")
        summary_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Summary text area
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, height=10)
        self.summary_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Generate summary button
        self.generate_button = ttk.Button(summary_frame, text="Generate Summary", command=self.generate_summary)
        self.generate_button.grid(row=1, column=0, pady=5)
        
        # Configure grid weights
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)

    def update_weather_data(self):
        try:
            # Read the raw data
            df = read_weather_data()
            if df.empty:
                self.status_var.set("No weather data available")
                return
                
            # Calculate statistics and format the data
            stats = calculate_statistics(df)
            self.weather_data = format_weather_data(stats)
            
            # Update the UI
            self.update_current_conditions()
            self.status_var.set("Data updated successfully")
        except Exception as e:
            self.status_var.set(f"Error updating data: {str(e)}")

    def update_current_conditions(self):
        if self.weather_data:
            current = self.weather_data['current_conditions']
            for key, label in self.current_labels.items():
                if key in current:
                    label.config(text=str(current[key]))

    def generate_summary(self):
        if not self.weather_data:
            self.status_var.set("No weather data available")
            return
            
        self.generate_button.config(state='disabled')
        self.status_var.set("Generating summary...")
        
        # Create a queue for the result
        result_queue = queue.Queue()
        
        # Start the summary generation in a separate thread
        def generate_summary_thread():
            try:
                summary = get_llm_response(self.weather_data)
                result_queue.put(summary)
            except Exception as e:
                result_queue.put(f"Error generating summary: {str(e)}")
        
        threading.Thread(target=generate_summary_thread, daemon=True).start()
        
        # Check for the result periodically
        def check_result():
            try:
                summary = result_queue.get_nowait()
                self.summary_text.delete(1.0, tk.END)
                self.summary_text.insert(tk.END, summary)
                self.generate_button.config(state='normal')
                self.status_var.set("Summary generated successfully")
            except queue.Empty:
                self.root.after(100, check_result)
        
        check_result()

    def periodic_update(self):
        self.update_weather_data()
        self.root.after(300000, self.periodic_update)  # Schedule next update

def main():
    root = tk.Tk()
    app = WeatherReporterUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 