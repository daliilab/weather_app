import pandas as pd
from datetime import datetime, timedelta

# Generate dates for August and September 2023
start_date = datetime(2023, 8, 1)
end_date = datetime(2023, 9, 30)
dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

# Generate mock weather data
data = {
    'city': [],
    'date': [],
    'temperature': [],
    'humidity': [],
    'wind_speed': []
}

# Populate the data
for date in dates:
    for city in ['Sarajevo', 'Mostar']:
        data['city'].append(city)
        data['date'].append(date.date())
        # Generate random weather values
        temp = round(20 + 10 * (0.5 - (date - start_date).days / (end_date - start_date).days), 1)
        humidity = round(50 + 20 * (0.5 - (date - start_date).days / (end_date - start_date).days), 1)
        wind_speed = round(5 + 3 * (0.5 - (date - start_date).days / (end_date - start_date).days), 1)
        data['temperature'].append(temp)
        data['humidity'].append(humidity)
        data['wind_speed'].append(wind_speed)

# Create a DataFrame
df = pd.DataFrame(data)

# Save the DataFrame to a CSV file for review
df.to_csv('data/mock_weather_data.csv', index=False)

print(df.head())  
