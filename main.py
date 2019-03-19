import time
import adafruit_sgp30
import dht
import json
import os

from machine import Pin, I2C

# construct an I2C bus
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=100000)

# Create library object on our I2C port
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

# Initiialize SGP30 sensor and set baseline variables
sgp30.iaq_init()

# Create temperature sensor object
dht = dht.DHT22(Pin(0))

led_onboard = Pin(5, Pin.OUT)
led_onboard.value(1)

elapsed_sec = 0


# Restore baseline files from flash
with open("data_file.json") as infile:
    baselines = json.load(infile)

sgp30.set_iaq_baseline(baselines["co2eq_base"], baselines["tvoc_base"])

while True:
    dht.measure()

    log = {"temperature" : dht.temperature(), "humidity" : dht.humidity(), "co2eq" : sgp30.co2eq, "tvoc" : sgp30.tvoc}

    with open ("history.json", "a+") as outfile:
        json.dump(log, outfile)

    if co2eq >= 1500 and led_onboard.value() != 0:
        led_onboard.value(0)
    elif led_onboard.value() != 1:
        led_onboard.value(1)

    print("temp = {:5.1f} °C \t humi = {:5.1f}% \t CO2e = {:d} ppm \t TVOC = {:d} ppb".format(
        log["temperature"], log["humidity"], log["co2eq"], log["tvoc"]))

    time.sleep(2)
    elapsed_sec += 2

    if elapsed_sec % 3600 == 0:
        elapsed_sec = 0
        baselines["co2eq_base"] = sgp30.baseline_co2eq
        baselines["tvoc_base"] = sgp30.baseline_tvoc

        with open("data_file.json", "w") as outfile:
            json.dump(baselines, outfile)

        print("**** Saved baselines to flash!")
