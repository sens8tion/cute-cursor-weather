import tkinter as tk
from tkinter import ttk
import json
import requests
from PIL import Image, ImageTk
import io
import urllib.request
import time
from weather_visualizer import calculate_statistics, get_llm_response, visualize_weather_data
from weather_collector import WeatherCollector
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import tempfile
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

class CuteWeatherUI:
    def __init__(self, root):
        self.root = root
        self.collector = WeatherCollector()
        self.location = self.get_location()
        
        # Configure root window
        self.root.title(f"☀️ Cute Weather Report 🌧️ - {self.location}")
        self.root.geometry("1200x800")  # Larger initial size
        self.root.configure(bg="#FFE4E1")  # Misty Rose background
        
        # Set up styles
        self.setup_styles()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, style="Cute.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create left panel for weather info and characters
        self.left_panel = ttk.Frame(self.main_frame, style="Cute.TFrame")
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Create right panel for graphs
        self.right_panel = ttk.Frame(self.main_frame, style="Cute.TFrame")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Initialize character tracking
        self.characters = ["sunny", "rainy", "windy", "snowy"]
        self.character_frames = {}
        self.character_labels = {}
        self.character_dialogues = {}
        
        # Create UI elements in order
        self.create_weather_info()  # Weather info at the top of left panel
        self.create_character_frames()  # Characters below weather info
        self.create_dialogue_box()  # Dialogue box below characters
        self.create_graph_display()  # Graphs in right panel
        
        # Start animations and updates
        self.start_animations()
        self.update_weather_data()
        
        # Set up periodic updates
        self.root.after(300000, self.update_weather)  # Update every 5 minutes

    def setup_styles(self):
        """Set up ttk styles for the UI"""
        self.cute_font = ("Comic Sans MS", 12)
        self.title_font = ("Comic Sans MS", 16, "bold")
        
        style = ttk.Style()
        style.configure("Cute.TFrame", background="#FFE4E1")
        style.configure("Cute.TLabel", 
                       background="#FFE4E1",
                       font=self.cute_font,
                       foreground="#FF69B4")  # Hot Pink text
        style.configure("Cute.TLabelframe", 
                       background="#FFE4E1",
                       font=self.cute_font)
        style.configure("Cute.TLabelframe.Label", 
                       background="#FFE4E1",
                       font=self.cute_font,
                       foreground="#FF69B4")

    def get_location(self):
        """Get the weather station's location."""
        return self.collector.get_location_string()
        
    def create_character_frames(self):
        # Character container in left panel
        self.character_container = ttk.LabelFrame(self.left_panel, text="Weather Friends", style="Cute.TLabelframe")
        self.character_container.pack(fill=tk.X, pady=10, padx=5)
        
        character_configs = {
            "sunny": ("🌄 Moorland Mary", "🐑"),
            "rainy": ("🌧️ Valley Val", "☔"),
            "windy": ("💨 Windy Wendy", "🍃"),
            "snowy": ("❄️ Snowy Sarah", "⛄")
        }
        
        for character, (base_text, _) in character_configs.items():
            frame = ttk.Frame(self.character_container, style="Cute.TFrame")
            frame.pack(pady=5)
            self.character_frames[character] = frame
            
            label = ttk.Label(frame, text=base_text, style="Cute.TLabel")
            label.pack()
            self.character_labels[character] = label
            
            dialogue = ttk.Label(frame, text="", style="Cute.TLabel", wraplength=300)
            dialogue.pack()
            self.character_dialogues[character] = dialogue

    def bounce(self, i=0):
        try:
            sunny_label = self.character_labels.get("sunny")
            if sunny_label and sunny_label.winfo_exists():
                sunny_label.config(text="🌄 Moorland Mary " + "🐑" * i)  # Yorkshire moorland sheep
                
            rainy_label = self.character_labels.get("rainy")
            if rainy_label and rainy_label.winfo_exists():
                rainy_label.config(text="🌧️ Valley Val " + "☔" * i)  # Valley character
                
            windy_label = self.character_labels.get("windy")
            if windy_label and windy_label.winfo_exists():
                windy_label.config(text="💨 Windy Wendy " + "🍃" * i)  # Windy character
                
            snowy_label = self.character_labels.get("snowy")
            if snowy_label and snowy_label.winfo_exists():
                snowy_label.config(text="❄️ Snowy Sarah " + "⛄" * i)  # Snowy character
                
            self.root.after(500, lambda: self.bounce((i + 1) % 4))
        except Exception as e:
            print(f"Animation error: {e}")

    def start_animations(self):
        try:
            self.bounce()
        except Exception as e:
            print(f"Failed to start animations: {e}")

    def create_weather_info(self):
        # Weather data frame in left panel
        self.weather_frame = ttk.LabelFrame(self.left_panel, text="Current Weather", style="Cute.TLabelframe")
        self.weather_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Get weather data
        self.update_weather_data()
        
    def create_graph_display(self):
        # Graph frame in right panel
        self.graph_frame = ttk.LabelFrame(self.right_panel, text="Weather Trends", style="Cute.TLabelframe")
        self.graph_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        
        # Create a canvas for the graph
        self.graph_canvas = tk.Canvas(self.graph_frame, bg="#FFE4E1", highlightthickness=0)
        self.graph_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create a scrollbar for the canvas
        scrollbar = ttk.Scrollbar(self.graph_frame, orient="vertical", command=self.graph_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.graph_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create a frame inside the canvas
        self.graph_inner_frame = ttk.Frame(self.graph_canvas, style="Cute.TFrame")
        self.graph_canvas.create_window((0, 0), window=self.graph_inner_frame, anchor="nw")
        
        # Configure the canvas to expand with the window
        self.graph_inner_frame.bind("<Configure>", 
            lambda e: self.graph_canvas.configure(scrollregion=self.graph_canvas.bbox("all")))
        
        # Initial graph update
        try:
            if os.path.exists('weather_data.csv'):
                df = pd.read_csv('weather_data.csv')
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                self.update_graphs(df)
        except Exception as e:
            print(f"Error creating initial graph: {str(e)}")

    def update_weather_data(self):
        try:
            # Get current weather data
            weather_data = self.collector.get_current_weather()
            
            # Update weather display
            self.update_weather_display(weather_data)
            
            # Update graphs
            if os.path.exists('weather_data.csv'):
                df = pd.read_csv('weather_data.csv')
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                self.update_graphs(df)
            
            # Update dialogue with LLM summary
            self.update_dialogue(weather_data)
            
        except Exception as e:
            print(f"Error updating weather data: {str(e)}")

    def update_graphs(self, df):
        try:
            # Clear existing graphs
            for widget in self.graph_inner_frame.winfo_children():
                widget.destroy()
            
            # Create a figure with subplots
            fig, axes = plt.subplots(4, 2, figsize=(10, 12))
            fig.suptitle('Weather Data Analysis', fontsize=16, color='#FF69B4')
            
            # Set the background color to match the UI
            fig.patch.set_facecolor('#FFE4E1')
            
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
                ax = axes[i]
                
                # Set the background color for each subplot
                ax.set_facecolor('#FFF0F5')
                
                # Check if column exists and has data
                if metric not in df.columns:
                    print(f"Warning: Column '{metric}' not found in data!")
                    continue
                    
                if df[metric].isna().all():
                    print(f"Warning: No data available for {metric}")
                    continue
                    
                # Plot the data with cute styling
                ax.plot(df['timestamp'], df[metric], marker='o', linestyle='-', linewidth=2, color='#FF69B4')
                
                # Format the x-axis
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, color='#FF69B4')
                
                # Set labels and title with cute styling
                ax.set_xlabel('Time', color='#FF69B4')
                ax.set_ylabel(ylabel, color='#FF69B4')
                ax.set_title(f'{ylabel} Over Time', color='#FF69B4')
                
                # Add grid
                ax.grid(True, linestyle='--', alpha=0.7, color='#FFB6C1')
                
                # Format y-axis to show all values
                ax.tick_params(axis='y', which='both', labelleft=True, colors='#FF69B4')
                ax.tick_params(axis='x', which='both', colors='#FF69B4')
                
                # Set the color of the spines
                for spine in ax.spines.values():
                    spine.set_color('#FF69B4')
            
            # Adjust layout to prevent label cutoff
            plt.tight_layout()
            
            # Convert the figure to a Tkinter-compatible format
            canvas = FigureCanvasTkAgg(fig, master=self.graph_inner_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Add a toolbar with cute styling
            toolbar = NavigationToolbar2Tk(canvas, self.graph_inner_frame)
            toolbar.update()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            print(f"Error updating graphs: {str(e)}")

    def create_dialogue_box(self):
        # Dialogue frame in left panel
        self.dialogue_frame = ttk.LabelFrame(self.left_panel, text="Weather Report", style="Cute.TLabelframe")
        self.dialogue_frame.pack(fill=tk.X, pady=10, padx=5)
        
        self.dialogue_text = tk.Text(
            self.dialogue_frame,
            wrap=tk.WORD,
            font=self.cute_font,
            bg="#FFF0F5",
            fg="#FF69B4",
            padx=10,
            pady=10,
            height=5
        )
        self.dialogue_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.dialogue_text.config(state=tk.DISABLED)

    def update_dialogue(self, weather_data):
        try:
            # Get LLM response for the weather data
            dialogue = get_llm_response(weather_data)
            
            # Update dialogue text
            self.dialogue_text.config(state=tk.NORMAL)
            self.dialogue_text.delete(1.0, tk.END)
            self.dialogue_text.insert(tk.END, dialogue)
            self.dialogue_text.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"Error updating dialogue: {str(e)}")
            self.dialogue_text.config(state=tk.NORMAL)
            self.dialogue_text.delete(1.0, tk.END)
            self.dialogue_text.insert(tk.END, "Sorry, I couldn't generate a weather summary right now. 🌧️")
            self.dialogue_text.config(state=tk.DISABLED)

    def update_weather(self):
        self.update_weather_data()
        self.root.after(300000, self.update_weather)  # Schedule next update

    def update_weather_display(self, weather_data):
        """Update the weather information display"""
        try:
            if not weather_data:
                print("No weather data available")
                return
                
            # Clear existing widgets
            for widget in self.weather_frame.winfo_children():
                widget.destroy()
                
            # Create location label
            location_text = f"📍 {self.location}"
            if self.collector.station_metadata and self.collector.station_metadata['elevation']:
                location_text += f"\nElevation: {self.collector.station_metadata['elevation']}m"
            
            ttk.Label(
                self.weather_frame,
                text=location_text,
                style="Cute.TLabel"
            ).pack(pady=5)
            
            # Format weather metrics with cute emojis
            metrics = [
                f"🌡️ Temperature: {weather_data['temperature']:.1f}°C",
                f"💧 Humidity: {weather_data['humidity']:.0f}%",
                f"💨 Wind: {weather_data['wind_speed']:.1f} km/h from {weather_data['wind_direction']}°",
                f"🎈 Pressure: {weather_data['pressure']:.1f} hPa",
                f"☔ Rain Rate: {weather_data['precipitation_rate']:.1f} mm/hr",
                f"☀️ UV Index: {weather_data['uv_index']}",
                f"🌞 Solar Radiation: {weather_data['solar_radiation']:.0f} W/m²"
            ]
            
            # Add each metric with cute styling
            for metric in metrics:
                label = ttk.Label(
                    self.weather_frame,
                    text=metric,
                    style="Cute.TLabel"
                )
                label.pack(pady=2)
                
        except Exception as e:
            print(f"Error updating weather display: {str(e)}")

def main():
    root = tk.Tk()
    app = CuteWeatherUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 