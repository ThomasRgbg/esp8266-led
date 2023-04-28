from machine import Pin, I2C, reset, RTC, unique_id, Timer, WDT, UART
import time

time.sleep(10)

import uasyncio
import gc
import micropython

from leds import *

from gurgleapps_webserver import GurgleAppsWebserver
import ujson as json


#####
# Schematic/Notes
######

# GPIO12 = Chan 1
# GPIO13 = Chan 2
# GPIO14 = Chan 3
# GPIO15 = Chan 4

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
# LEDs
#####

# time.sleep(5)

#l1 = LedStrip4(12)
#l2 = LedStrip4(13)
#l3 = LedStrip4(14)
#l4 = LedStrip4(15)

ledcube = LedGlobe46(12,13,14,15)
#ledcube.blank()

led_running = True

#####
# Webserver 
#####

server = GurgleAppsWebserver(port=80, doc_root="/www", log_level=2)

#####
# Webserver Callbacks
#####

status = True

async def send_status(request, response):
    response_string = json.dumps({"status":status, "count":count,
                                  "errcount":errcount, "led_running":led_running,
                                  "animation_delay":ledcube.animation_delay,
                                  "led_mode":ledcube.mode,
                                  })
    await response.send_json(response_string, 200)

async def led_start(request, response):
    global led_running
    led_running = True
    await send_status(request, response)

async def led_stop(request, response):
    global led_running
    led_running = False
    await send_status(request, response)

async def led_faster(request, response):
    ledcube.faster()
    await send_status(request, response)

async def led_slower(request, response):
    ledcube.slower()
    await send_status(request, response)

#async def led_mode_rotate_left(request, response):
    #ledcube.mode = rotate_left
    #await send_status(request, response)

#async def led_mode_fade(request, response):
    #ledcube.mode = fade
    #await send_status(request, response)

server.add_function_route("/status", send_status)
server.add_function_route("/reset", reset)
server.add_function_route("/start", led_start)
server.add_function_route("/stop", led_stop)
server.add_function_route("/faster", led_faster)
server.add_function_route("/slower", led_slower)
#server.add_function_route("/rotate_left", rotate_left)
#server.add_function_route("/fade", fade)


#####
# Task definition
#####

async def housekeeping():
    global errcount
    global count
    await uasyncio.sleep_ms(1000)

    while True:
        print("housekeeping() - count {0}, errcount {1}".format(count,errcount))
        # wdt.feed()
        gc.collect()
        micropython.mem_info()

        # Too many errors, e.g. could not connect to MQTT
        if errcount > 20:
            reset()

        count += 1
        await uasyncio.sleep_ms(60000)



async def ledrun():
    global led_running
    while True:
        if led_running:
            await ledcube.test()
        else:
            await ledcube.blank()
        await uasyncio.sleep_ms(10)


####
# Main
####

print("main_loop")
ledcube.all_on(green)

main_loop = uasyncio.get_event_loop()


main_loop.create_task(uasyncio.start_server(server.serve_request, "0.0.0.0", 80))
main_loop.create_task(housekeeping())
main_loop.create_task(ledrun())

main_loop.run_forever()
main_loop.close()

