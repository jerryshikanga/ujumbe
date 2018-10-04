# Fama Data
This is an app to provide data to small scale farmers.
The Data provided includes
- Weather forecast
- Current weather
- Historical weather

This app is to be in several modules i.e. 
- USSD
- SMS
- Web _(Coming soon)_
- Android _(Coming soon)_
- iOS _(Coming soon)_

This repo performs several functions
- Collects data from openweather api and stores it to the db _(celery)_
- Serves data via an api to mobile clients _(Django rest framework)_
- Handles SMS and USSD requests _(USSD Airflow)_
