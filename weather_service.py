import os
import requests
from datetime import datetime

class WeatherService:
    def __init__(self):
        self.api_key = 'ea4dfd2c058b4a52bb964427252302'  # WeatherAPI.com key
        self.base_url = "http://api.weatherapi.com/v1"

    def get_forecast(self, city, country_code="US"):
        """
        Get 3-day weather forecast for a given city
        Returns weather data in metric units
        """
        try:
            params = {
                'q': f"{city},{country_code}",
                'key': self.api_key,
                'days': 3,  # Get 3 days of forecast
                'aqi': 'no'  # We don't need air quality data
            }

            response = requests.get(f"{self.base_url}/forecast.json", params=params)
            response.raise_for_status()

            data = response.json()
            forecast = []

            for day in data['forecast']['forecastday']:
                forecast.append({
                    'date': day['date'],
                    'temperature': {
                        'min': round(day['day']['mintemp_c'], 2),
                        'max': round(day['day']['maxtemp_c'], 2)
                    },
                    'humidity': day['day']['avghumidity'],
                    'description': day['day']['condition']['text'],
                    'icon': day['day']['condition']['icon'],
                    'rainfall': day['day']['totalprecip_mm']  # Total precipitation in mm
                })

            return forecast
        except Exception as e:
            raise Exception(f"Error fetching weather data: {str(e)}")