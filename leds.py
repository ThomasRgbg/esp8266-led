from machine import Pin
from neopixel import NeoPixel
from time import sleep
import uasyncio

# L1     5 2 1
#        4 3 0

# L2     5 2 1
#        4 3 0

# L3     5 2 1
#        4 3 0

# L4     4 3 0
#        5 2 1

white = (255,255,255)
red   = (255,0,0)
blue  = (0,255,0)
green = (0,0,255)
pink  = (64,128,0)
yellow = (255,0,150)
black = (0,0,0)


class LedGlobe46:
    def __init__(self, gpioA, gpioB, gpioC, gpioD):
        self.np = []
        self.np.append(NeoPixel(Pin(gpioA, Pin.OUT), 6))
        self.np.append(NeoPixel(Pin(gpioB, Pin.OUT), 6))
        self.np.append(NeoPixel(Pin(gpioC, Pin.OUT), 6))
        self.np.append(NeoPixel(Pin(gpioD, Pin.OUT), 6))

        self.order_lower = [(0,1), (0,2), (0,5),
                            (1,1), (1,2), (1,5),
                            (2,1), (2,2), (2,5),
                            (3,4), (3,3), (3,0), 
                            ]

        self.order_upper = [(0,0), (0,3), (0,4),
                            (1,0), (1,3), (1,4),
                            (2,0), (2,3), (2,4),
                            (3,5), (3,2), (3,1), 
                            ]

        self.blank()

    def __len__(self):
        return 24
    
    def __getitem__(self, x):
        if x >= (len(self) / 2):
            i , j = self.order_upper[x-12]
        else:
            i , j = self.order_lower[x]
        return self.np[i][j]

    def __setitem__(self, x, val):
        if x >= (len(self) / 2):
            i , j = self.order_upper[x-12]
        else:
            i , j = self.order_lower[x]
        # print("i = {0}, j={1}, val={2}".format(i,j,val))
        self.np[i][j] = val
        self.write()
        
    def write(self):
        for i in range(len(self.np)):
            self.np[i].write()
            
    async def blank(self):
        for i in range(len(self.np)):
            for j in range(len(self.np[0])):
                self.np[i][j] = (0,0,0)
            self.np[i].write()

    # Animations
    async def rotate_on(self, color):
        print("rotate_on: {0}".format(color))
        for x in range(len(self)):
            self[x] = color
            await uasyncio.sleep_ms(50)

    async def rotate(self, color):
        self.all_on(black)
        for x in range(len(self)):
            self[x] = color
            if x > 0: 
                self[x-1] = black
            await uasyncio.sleep_ms(50)
        self.all_on(black)

    async def all_on(self, color):
        print("all_on: {0}".format(color))
        for x in range(len(self)):
            self[x] = color

    async def test_lower(self):
        while True:
            await self.rotate(red)
            await self.rotate(red)
            await self.rotate(green)
            self.rotate(green)
            self.rotate(blue)
            self.rotate(blue)
            self.rotate(yellow)
            self.rotate(yellow)
            self.rotate(pink)
            self.rotate(pink)
            self.all_on(black)
            self.rotate_on(red)
            self.rotate_on(green)
            self.rotate_on(blue)
            self.rotate_on(yellow)
            self.rotate_on(pink)
            self.all_on(black)
            
    async def test_rotate_all(self):
        #while True:
        await self.rotate_on(red)
        await self.rotate_on(blue)
        await self.rotate_on(yellow)
        await self.rotate_on(pink)
        await self.rotate_on(green)
        await self.rotate_on(blue)
        await self.rotate_on(pink)
        await self.all_on(black)
            
    async def test(self):
        await self.test_rotate_all()


class LedStrip4:
    def __init__(self, gpionum):
        self.pin=Pin(gpionum, Pin.OUT)
        self.np = NeoPixel(self.pin, 8)

    @property
    def np1l(self):
        return self.np[0]
    
    @np1l.setter
    def np1l(self, rgb):
        self.np[0] = rgb
        self.np.write()

    @property
    def np1h(self):
        return self.np[1]

    @np1h.setter
    def np1h(self, rgb):
        self.np[1] = rgb
        self.np.write()
        
    @property
    def np2l(self):
        return self.np[3]
    
    @np2l.setter
    def np2l(self, rgb):
        self.np[3] = rgb
        self.np.write()

    @property
    def np2h(self):
        return self.np[2]

    @np2h.setter
    def np2h(self, rgb):
        self.np[2] = rgb
        self.np.write()

    @property
    def np3l(self):
        return self.np[4]
    
    @np3l.setter
    def np3l(self, rgb):
        self.np[4] = rgb
        self.np.write()

    @property
    def np3h(self):
        return self.np[5]

    @np3h.setter
    def np3h(self, rgb):
        self.np[5] = rgb
        self.np.write()
        
    def test(self, color):
        self.np3l = color
        for i in range(5):
            temp = self.np3h
            self.np3h = self.np2h
            self.np2h = self.np1h
            self.np1h = self.np1l
            self.np1l = self.np2l
            self.np2l = self.np3l
            self.np3l = temp
            # await uasyncio.sleep_ms(400)
            sleep(0.25)

    def testrun(self):
        self.test(white)
        self.test(green)
        self.test(red)
        self.test(blue)
        self.test(yellow)
        self.test(pink)
            


