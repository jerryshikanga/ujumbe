def get_weather_forecast_periods():
    periods = []
    periods.append("1 Hour")
    periods.append("12 Hours")
    periods.append("1 Day")
    periods.append("1 Week")
    periods.append("1 Month")

    string = ""
    counter = 0
    for period in periods :
        string += "{}. {}\n".format(counter, period)
        counter += 1
    return string
