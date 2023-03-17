# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import uos, machine
uos.dupterm(None, 1) # disable REPL on UART(0)
import gc
import webrepl
import time
import network

webrepl.start()
gc.collect()

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='esp-leds', password='aaaaaaaaaaaa')

wlan = network.WLAN(network.STA_IF)
wlan.active(True) 
wlan.scan()

wlan.connect('aaaaaa', 'abbbbbbb')
wlan.ifconfig()

