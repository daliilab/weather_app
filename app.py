from flask import Flask, render_template, request, redirect
import requests
from datetime import datetime, timedelta
import pytz
from pytz import timezone
from timezonefinder import TimezoneFinder
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd

app = Flask(__name__)

def configure():
    load_dotenv()

CURRENT_WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather?'
icon_mapping = {
    '01d': 'clear_skyD.png',
    '01n': 'clear_skyN.png',
    '02d': 'few_cloudsD.png',
    '02n': 'few_cloudsN.png',
    '03d': 'scatteredD.png',
    '03n': 'scatteredN.png',
    '04d': 'brokenDN.png',
    '04n': 'brokenDN.png',
    '09d': 'shower_rainD.png',
    '09n': 'shower_rainN.png',
    '10d': 'rainD.png',
    '10n': 'rainN.png',
    '11d': 'thunderstormD.png',
    '11n': 'thunderstormN.png',
    '13d': 'snowD.png',
    '13n': 'snowN.png',
    '50d': 'mistDN.png',
    '50n': 'mistDN.png'
}

def get_weather(city, units):
    weather_url = f"{CURRENT_WEATHER_URL}appid={os.getenv('API_KEY')}&q={city}&units={units}"
    response = requests.get(weather_url)
    return response.json()

def get_forecast(city, units):
    forecast_url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={os.getenv('API_KEY')}&units={units}'
    response = requests.get(forecast_url)
    return response.json()

def get_time_zone(lat, lon):
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    return tz_name

def convert_to_local_time(utc_time, tz_name):
    local_tz = pytz.timezone(tz_name)
    utc_dt = datetime.utcfromtimestamp(utc_time).replace(tzinfo=pytz.utc)
    local_dt = utc_dt.astimezone(local_tz)
    return local_dt.strftime('%H:%M:%S')

def extract_forecast_data(forecast_data, units):
    forecast_list = []
    for entry in forecast_data['list']:
        date_text = entry['dt_txt']
        date = datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
        if date.hour == 12:  
            icon_code = entry['weather'][0]['icon']
            icon_filename = icon_mapping.get(icon_code, 'default.png')
            temp = round(entry['main']['temp'])  
            wind_speed = round(entry['wind']['speed'])
            forecast_list.append({
                'date': date.strftime('%A | %d %B'),
                'temperature': f"{temp}",  
                'description': entry['weather'][0]['description'],
                'wind_speed': f"{wind_speed}",
                'humidity': entry['main']['humidity'],
                'icon': icon_filename
            })
    return forecast_list[:5]
 

DATABASE_URL = 'sqlite:///weather_data.db'  

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class Weather(Base):
    __tablename__ = 'weather'
    
    id = Column(Integer, primary_key=True)
    city = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<Weather(city={self.city}, date={self.date}, temperature={self.temperature}, humidity={self.humidity}, wind_speed={self.wind_speed})>"

Base.metadata.create_all(engine)

def load_historical_data():
    start_date = datetime(2023, 8, 1)
    end_date = datetime(2023, 9, 30)
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    data = {
        'city': [],
        'date': [],
        'temperature': [],
        'humidity': [],
        'wind_speed': []
    }

    for date in dates:
        for city in ['Sarajevo', 'Mostar']:
            data['city'].append(city)
            data['date'].append(date.date())
            temp = round(20 + 10 * (0.5 - (date - start_date).days / (end_date - start_date).days), 1)
            humidity = round(50 + 20 * (0.5 - (date - start_date).days / (end_date - start_date).days), 1)
            wind_speed = round(5 + 3 * (0.5 - (date - start_date).days / (end_date - start_date).days), 1)
            data['temperature'].append(temp)
            data['humidity'].append(humidity)
            data['wind_speed'].append(wind_speed)

    df = pd.DataFrame(data)

    df.to_csv('mock_weather_data.csv', index=False)

    for _, row in df.iterrows():
        weather = Weather(
            city=row['city'],
            date=pd.to_datetime(row['date']),
            temperature=row['temperature'],
            humidity=row['humidity'],
            wind_speed=row['wind_speed']
        )
        session.add(weather)
    session.commit()

@app.route('/')
def home():
    city = 'Sarajevo'
    units = 'metric'

    unit_symbol = '°C'
    wind_speed_unit = 'm/s'

    data = get_weather(city, units)
    forecast_data = get_forecast(city, units)
    forecast = extract_forecast_data(forecast_data, units)

    if data["cod"] != "404":
        icon_code = data['weather'][0]['icon']
        icon_filename = icon_mapping.get(icon_code, 'default.png')

        lat, lon = data['coord']['lat'], data['coord']['lon']
        tz_name = get_time_zone(lat, lon)
        city_time_zone = tz_name if tz_name else 'UTC'

        sunrise = convert_to_local_time(data['sys']['sunrise'], city_time_zone)
        sunset = convert_to_local_time(data['sys']['sunset'], city_time_zone)
        local_time = datetime.now(pytz.timezone(city_time_zone)).strftime("%d-%m-%Y | %H:%M:%S")

        wind_speed = data['wind']['speed']
        temperature = round(data['main']['temp'])  
        temp_max = round(data['main']['temp_max'])
        temp_min = round(data['main']['temp_min'])
        feels_like = round(data['main']['feels_like'])

        weather = {
            'city': data['name'],
            'country_code': data['sys']['country'],
            'icon': icon_filename,
            'description': data['weather'][0]['description'],
            'temperature': f"{temperature}",  
            'temp_max': f"{temp_max}",
            'temp_min': f"{temp_min}",
            'sunrise': sunrise,
            'feels_like': f"{feels_like}",
            'humidity': data['main']['humidity'],
            'wind_speed': f"{wind_speed}",
            'sunset': sunset
        }
    else:
        weather = None
        local_time = None

    show_comparison_button = city in ['Sarajevo', 'Mostar']

    return render_template('index.html', weather=weather, current_datetime=local_time, forecast=forecast, unit=unit_symbol, wind_speed_unit=wind_speed_unit, show_comparison_button=show_comparison_button)

@app.route('/search', methods=['GET'])
def search():
    city = request.args.get('city')
    units = request.args.get('units', 'metric')

    if city: 
        unit_symbol = '°C' if units == 'metric' else '°F'
        wind_speed_unit = 'm/s' if units == 'metric' else 'mph'

        weather_data = get_weather(city,units)
        forecast_data = get_forecast(city, units)
        forecast = extract_forecast_data(forecast_data, units)

        if weather_data["cod"] != "404":
            icon_code = weather_data['weather'][0]['icon']
            icon_filename = icon_mapping.get(icon_code, 'default.png')

            lat, lon = weather_data['coord']['lat'], weather_data['coord']['lon']
            tz_name = get_time_zone(lat, lon)
            city_time_zone = tz_name if tz_name else 'UTC'

            sunrise = convert_to_local_time(weather_data['sys']['sunrise'], city_time_zone)
            sunset = convert_to_local_time(weather_data['sys']['sunset'], city_time_zone)
            local_time = datetime.now(pytz.timezone(city_time_zone)).strftime("%d-%m-%Y | %H:%M:%S")

            wind_speed = weather_data['wind']['speed']
            temperature = round(weather_data['main']['temp']) 
            temp_max = round(weather_data['main']['temp_max'])
            temp_min = round(weather_data['main']['temp_min'])
            feels_like = round(weather_data['main']['feels_like'])

            weather = {
                'city': weather_data['name'],
                'country_code': weather_data['sys']['country'],
                'icon': icon_filename,
                'description': weather_data['weather'][0]['description'],
                'temperature': f"{temperature}",  
                'temp_max': f"{temp_max}",
                'temp_min': f"{temp_min}",
                'sunrise': sunrise,
                'feels_like': f"{feels_like}",
                'humidity': weather_data['main']['humidity'],
                'wind_speed': f"{wind_speed}",
                'sunset': sunset
            }
        else:
            weather = None
            local_time = None

        show_comparison_button = city.title() in ['Sarajevo', 'Mostar']

        return render_template('index.html', weather=weather, current_datetime=local_time, forecast=forecast, unit=unit_symbol, wind_speed_unit=wind_speed_unit, show_comparison_button=show_comparison_button)
    
    return redirect('/')


@app.route('/comparison/<city>')
def comparison(city):
    city = city.title()
    units = request.args.get('units', 'metric') 

    unit_symbol = '°C' if units == 'metric' else '°F'
    wind_speed_unit = 'm/s' if units == 'metric' else 'mph'

    def convert_temperature(temp, units):
        try:
            temp = float(temp)
            if units == 'imperial':
                return round(temp * 9/5 + 32)
            return temp
        except ValueError:
            return 'N/A'

    def convert_wind_speed(speed, units):
        try:
            speed = float(speed)
            if units == 'imperial':
                return round(speed * 2.237, 1)
            return speed
        except ValueError:
            return 'N/A'

    today = datetime.now().date()
    num_days = 5
    future_dates = [today + timedelta(days=i) for i in range(num_days)]

    forecast_data = get_forecast(city, units)
    current_forecast = extract_forecast_data(forecast_data, units)

    csv_file_path = "data/mock_weather_data.csv"
    df = pd.read_csv(csv_file_path)
    df['date'] = pd.to_datetime(df['date']).dt.date
    df['city'] = df['city'].str.title()

    historical_dates = [date.replace(year=today.year - 1) for date in future_dates]
    historical_data = df[(df['city'] == city) & (df['date'].isin(historical_dates))]

    historical_forecast = []
    for date in historical_dates:
        historical_weather = historical_data[historical_data['date'] == date]
        if not historical_weather.empty:
            historical_weather = historical_weather.iloc[0]
            historical_forecast.append({
                'date': date.strftime('%d %B %Y'),
                'temperature': f"{convert_temperature(historical_weather['temperature'], units)}",
                'humidity': f"{historical_weather['humidity']}%",
                'wind_speed': f"{convert_wind_speed(historical_weather['wind_speed'], units)}"
            })
        else:
            historical_forecast.append({
                'date': date.strftime('%d %B %Y'),
                'temperature': 'Data not available',
                'humidity': 'Data not available',
                'wind_speed': 'Data not available'
            })

    current_forecast_formatted = [
        {
            'date': future_dates[i].strftime('%d %B %Y'),
            'temperature': f"{data['temperature']}",
            'humidity': f"{data['humidity']}%",
            'wind_speed': f"{data['wind_speed']}"
        }
        for i, data in enumerate(current_forecast)
    ]

    return render_template('comparison.html', 
                           city=city,
                           future_dates=future_dates,
                           current_forecast=current_forecast_formatted,
                           historical_forecast=historical_forecast,
                           unit_symbol=unit_symbol,
                           wind_speed_unit=wind_speed_unit)



if __name__ == '__main__':
    configure()
    app.run(debug=True)