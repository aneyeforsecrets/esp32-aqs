import time
import adafruit_sgp30   # Library for the usage of the SGP30 VOC sensor
import dht  # Library for the usage of the DHT22 temperature/humidity sensor
import json
import os
from machine import Pin, I2C
import logging
import logging.handlers as handlers


class BaselineValues:
    def __init__(self, sensor):
        self.values = {}
        self.values["co2eq_base"] = 0
        self.values["tvoc_base"] = 0
        self.sensor = sensor

    def restore(self):
        # Initiialize SGP30 sensor and restore baseline variables
        logging.info(
            "Initiating SGP30 sensor and attempting to restore baseline values.")

        self.sensor.iaq_init()

        with open("data_file.json") as infile:
            self.values = json.load(infile)

        self.sensor.set_iaq_baseline(
            self.values["co2eq_base"], self.values["tvoc_base"])

        logging.info("Restored baseline values co2eq %d and tvoc %d",
                     self.values["co2eq_base"], self.values["tvoc_base"])

    def store(self):
        self.values["co2eq_base"] = self.sensor.baseline_co2eq
        self.values["tvoc_base"] = self.sensor.baseline_tvoc

        with open("data_file.json", "w") as outfile:
            json.dump(self.values, outfile)

        logging.info("Stored baselines to flash.")


def measure(time_delay):
    def checkAirRequirement(log, co2eq_warning_level):
        if log["co2eq"] >= co2eq_warning_level and led_onboard.value() != 0:
            logging.info("CO2eq level exceeded %d ppm!", co2eq_warning_level)
            led_onboard.value(0)
        elif led_onboard.value() != 1:
            logging.info("CO2eq back below %d ppm.", co2eq_warning_level)
            led_onboard.value(1)

    # Before the DHT22 values can be used measure() needs to be called
    # seperately - limited to once every 2 seconds!
    dht.measure()

    # Call values of the sensors and write them into a dictionary to allow
    # storage as JSON later. SGP30 does not need a separate measure call
    log = {"temperature": dht.temperature(), "humidity": dht.humidity(),
           "co2eq": sgp30.co2eq, "tvoc": sgp30.tvoc}

    # Append dictionary log as JSON
    with open("history.json", "a+") as outfile:
        json.dump(log, outfile)

    # If CO2eq levels exceed 1500 ppm, turn on LED to signal it's time to
    # crack open a window
    checkAirRequirement(log, co2eq_warning_level)


# Time between measurements in seconds
time_delay = 2
# Time between saving baseline values to flash in seconds - recommended 1h
baseline_save_delay = 3600
# co2eq level in ppm after which the warning is triggered
co2eq_warning_level = 1500


# Set up logging
logger = logging.getLogger('aqs')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

with open("messages.log", "a+") as outfile:
    outfile.write("System Start.")

logHandler = handlers.RotatingFileHandler(
    'messages.log', maxBytes=256, backupCount=2)

logHandler.setFormatter(formatter)

logger.addHandler(logHandler)


# construct an I2C bus
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=100000)

# Create SGP30 sensor object and restore baseline values from flash
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

baseline = BaselineValues(sgp30)
baseline.restore()

# Create temperature sensor object
dht = dht.DHT22(Pin(0))

# Create LED object for on-board LED
led_onboard = Pin(5, Pin.OUT)
led_onboard.value(1)

elapsed_sec = 0

while True:
    measure(time_delay)

    if elapsed_sec % baseline_save_delay == 0 and elapsed_sec != 0:
        # According to the sensor documentation of the SGP30 it automatically
        # calibrates itself depending on the environment. These values should
        # be stored once every hour and restored after boot
        elapsed_sec = 0
        baseline.store()

    # Wait - minimum 2 seconds before DHT22 sensor can be measured again
    time.sleep(time_delay)
    elapsed_sec += time_delay
