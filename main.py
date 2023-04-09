from machine import Pin, I2C, reset, RTC, unique_id, Timer, WDT, UART
import time

time.sleep(10)

import uasyncio
import gc
import micropython

from leds import *

#####
# Schematic/Notes
######

# GPIO12 = Chan 1
# GPIO13 = Chan 2
# GPIO14 = Chan 3
# GPIO15 = Chan 4

#####
# LEDs
#####

# time.sleep(5)

#l1 = LedStrip4(12)
#l2 = LedStrip4(13)
#l3 = LedStrip4(14)
#l4 = LedStrip4(15)

ledcube = LedGlobe46(12,13,14,15)

#####
# Watchdog
#####

class Watchdog:
    def __init__(self, interval):
        self.timer = Timer(-1)
        self.timer.init(period=(interval*1000), mode=Timer.PERIODIC, callback=self.wdtcheck)
        self.feeded = True
        
    def wdtcheck(self, timer):
        if self.feeded:
            print("Watchdog feeded, all fine")
            self.feeded = False
        else:
            print("Watchdog hungry, lets do a reset in 5 sec")
            time.sleep(5)
            reset()
            
    def feed(self):
        self.feeded = True
        print("Feed Watchdog")

# wdt = Watchdog(interval = 120)
# wdt.feed()

#####
# Housekeeping
#####

count = 1
errcount = 0

def get_count():
    global count
    return count

def get_errcount():
    global errcount
    return errcount

#####
# Task definition
#####

async def housekeeping():
    global errcount
    global count
    while True:
        await uasyncio.sleep_ms(60000)
        print("housekeeping() - count {0}, errcount {1}".format(count,errcount))
        # wdt.feed()
        gc.collect()
        micropython.mem_info()

        # Too many errors, e.g. could not connect to MQTT
        if errcount > 20:
            reset()

        count += 1



async def ledrun():
    while True:
        ledcube.test()
        await uasyncio.sleep_ms(1000)


####
# Main
####


main_loop = uasyncio.get_event_loop()

main_loop.create_task(housekeeping())
main_loop.create_task(ledrun())

main_loop.run_forever()
main_loop.close()

