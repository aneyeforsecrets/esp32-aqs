import time
import adafruit_sgp30   # Library for the usage of the SGP30 VOC sensor
import dht              # Library for the usage of the DHT22 temperature/humidity sensor
import json
import os
from machine import Pin, I2C
import logging
import logging.handlers as handlers

# Some Settings

co2eq_warning_level = 1500    # co2eq level in ppm after which the warning is triggered

# Set up logging
logger = logging.getLogger('aqs')

# Here we define our formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logHandler = handlers.RotatingFileHandler(
    'messages.log', maxBytes=256, backupCount=2)

# Here we set our logHandler's formatter
logHandler.setFormatter(formatter)

logger.addHandler(logHandler)


# construct an I2C bus
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=100000)

# Create library object on our I2C port
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

# Initiialize SGP30 sensor and restore baseline variables
logging.info(
    "Initiating SGP30 sensor and attempting to restore baseline values.")

sgp30.iaq_init()
with open("data_file.json") as infile:
    baseline = json.load(infile)

sgp30.set_iaq_baseline(baseline["co2eq_base"], baseline["tvoc_base"])
logging.info("Restored baseline values co2eq %d and tvoc %d",
             baseline["co2eq_base"], baseline["tvoc_base"])

# Create temperature sensor object
dht = dht.DHT22(Pin(0))

# Create LED object for on-board LED
led_onboard = Pin(5, Pin.OUT)
led_onboard.value(1)


elapsed_sec = 0

while True:
    # Before the DHT22 values can be used measure() needs to be called seperately - limited to once every 2 seconds!
    dht.measure()

    # Call values of the sensors and write them into a dictionary to allow storage as JSON later.
    # SGP30 does not need a separate measure call
    log = {"temperature": dht.temperature(), "humidity": dht.humidity(),
           "co2eq": sgp30.co2eq, "tvoc": sgp30.tvoc}

    # Append dictionary log as JSON
    with open("history.json", "a+") as outfile:
        json.dump(log, outfile)

    # If CO2eq levels exceed 1500 ppm, turn on LED to signal it's time to crack open a window
    if log["co2eq"] >= co2eq_warning_level and led_onboard.value() != 0:
        logging.info("CO2eq level exceeded %d ppm!", co2eq_warning_level)
        led_onboard.value(0)
    elif led_onboard.value() != 1:
        logging.info("CO2eq back below %d ppm.", co2eq_warning_level)
        led_onboard.value(1)

    print("temp = {:5.1f} °C \t humi = {:5.1f}% \t CO2e = {:d} ppm \t TVOC = {:d} ppb".format(
        log["temperature"], log["humidity"], log["co2eq"], log["tvoc"]))

    # Wait - minimum 2 seconds before DHT22 sensor can be measured again
    time.sleep(2)
    elapsed_sec += 2

    # According to the sensor documentation of the SGP30 it automatically calibrates itself
    # depending on the environment. These values should be stored once every hour and restored after boot
    if elapsed_sec % 3600 == 0:
        elapsed_sec = 0
        baseline["co2eq_base"] = sgp30.baseline_co2eq
        baseline["tvoc_base"] = sgp30.baseline_tvoc

        with open("data_file.json", "w") as outfile:
            json.dump(baseline, outfile)

        logging.info("Stored baselines to flash.")
