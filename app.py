from flask import Flask, render_template, request
import requests
from datetime import datetime
import pytz
from pytz import timezone
from timezonefinder import TimezoneFinder  
from dotenv import load_dotenv
import os

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

def convert_temperature(temp, units):
    if units == 'metric':
        return temp  
    elif units == 'imperial':
        return round(temp * 1.8 + 32) 
    else:
        return temp  
    
def convert_wind_speed(speed, units):
    if units == 'metric':
        return speed
    elif units == 'imperial':
        return round(speed * 2.237)  
    else:
        return speed  

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
            temp = round(convert_temperature(entry['main']['temp'], units))
            forecast_list.append({
                'date': date.strftime('%A | %d %B'),
                'temperature': temp,
                'description': entry['weather'][0]['description'],
                'wind_speed': entry['wind']['speed'],
                'humidity': entry['main']['humidity'],
                'icon': icon_filename
            })
    return forecast_list[:5]  


@app.route('/')
def home():
    city = 'Sarajevo'
    units = 'metric'
    unit_symbol = '°C' if units == 'metric' else '°F'
    wind_speed_unit = 'm/s' if units == 'metric' else 'mph'
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

        wind_speed = convert_wind_speed(data['wind']['speed'], units)
        temperature = convert_temperature(data['main']['temp'], units)
        temp_max = convert_temperature(data['main']['temp_max'], units)
        temp_min = convert_temperature(data['main']['temp_min'], units)
        feels_like = convert_temperature(data['main']['feels_like'], units)

        weather = {
            'city': data['name'],
            'country_code': data['sys']['country'],  
            'icon': icon_filename,
            'description': data['weather'][0]['description'],
            'temperature': round(temperature),
            'temp_max': round(temp_max),
            'temp_min': round(temp_min),
            'sunrise': sunrise,
            'feels_like': round(feels_like),
            'humidity': data['main']['humidity'],
            'wind_speed': wind_speed,
            'sunset': sunset
        }
    else:
        weather = None
        local_time = None

    return render_template('index.html', weather=weather, current_datetime=local_time, forecast=forecast, unit=unit_symbol, wind_speed_unit=wind_speed_unit)

@app.route('/search', methods=['GET'])
def search():
    city = request.args.get('city')
    units = request.args.get('units', 'metric')
    unit_symbol = '°C' if units == 'metric' else '°F'
    wind_speed_unit = 'm/s' if units == 'metric' else 'mph'

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

        wind_speed = convert_wind_speed(data['wind']['speed'], units)
        temperature = convert_temperature(data['main']['temp'], units)
        temp_max = convert_temperature(data['main']['temp_max'], units)
        temp_min = convert_temperature(data['main']['temp_min'], units)
        feels_like = convert_temperature(data['main']['feels_like'], units)

        weather = {
            'city': data['name'],
            'country_code': data['sys']['country'], 
            'icon': icon_filename,
            'description': data['weather'][0]['description'],
            'temperature': round(temperature),
            'temp_max': round(temp_max),
            'temp_min': round(temp_min),
            'sunrise': sunrise,
            'feels_like': round(feels_like),
            'humidity': data['main']['humidity'],
            'wind_speed': wind_speed,
            'sunset': sunset
        }
    else:
        weather = None
        local_time = None

    return render_template('index.html', weather=weather, current_datetime=local_time, forecast=forecast, unit=unit_symbol, wind_speed_unit=wind_speed_unit)

if __name__ == '__main__':
    app.run(debug=True)

