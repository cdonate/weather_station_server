from schema import Schema, Use

weather_data = Schema([
    {
        'temperature': Use(float),
        'humidity': Use(float),
        'pressure': Use(float),
        'rainfall': Use(int)
    }
])
