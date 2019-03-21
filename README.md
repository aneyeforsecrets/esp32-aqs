# esp32-aqs
An ESP32-Based Air Quality Sensor.

# Goal
Goal of the project is to build and configure an air quality sensor that sends air quality metrics to an external destination and caches it locally if no internet connection is available.

# Parts
Board: LOLIN D32 Pro V2.0.0

CO2eq & TVOC sensor: Adafruit SGP30 Air Quality

Temperature & Humidity sensor: DHT22

# To-Do
Software:

- Rewrite logging of environmental data to use logging module
- Prepare different log types (every minute, every hour, every day etc.) to reduce total log size

Hardware:
- Attach display to allow reading of measurements
- Add PM sensor
- Install board into case
- Add 5v Fan to increase measurement accuracy
- Transfer from breadboard to pcb
