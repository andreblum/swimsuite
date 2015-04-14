import spidev, time
from pymongo import Connection
import RPi.GPIO as GPIO
import logging
import logging.handlers

logging.basicConfig()
logger = logging.getLogger('swimsuite')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address=('localhost',514),facility=logging.handlers.SysLogHandler.LOG_LOCAL0)
logger.addHandler(handler)

logger.info('starting swimsuite')

HISTHERESIS = 5*60 # don't change valve within 5 minutes of last change

PUMP_ON_HOUR = 10
PUMP_ON_MIN = 0

PUMP_OFF_HOUR = 16
PUMP_OFF_MIN = 0

PUMP_OFF_MAX_HOUR = 21
PUMP_OFF_MAX_MIN = 0

MAX_TEMP = 29.0

# see https://github.com/abelectronicsuk/adcdacpi/blob/master/spiadc.py

spi = spidev.SpiDev(0,0)
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.OUT)      # valve close
GPIO.setup(22, GPIO.OUT)     # valve open
GPIO.setup(25, GPIO.OUT)	   # pump

last_valve_time = 0

def get_adc_int(channel):
    r = spi.xfer2([1,(2+channel)<<6,0]) # read byte list from MCP3202
    return ((r[1]&0x0F) << 8) + (r[2]) # convert byte list to integer

calibrated = [ 
    (16, 2425),
    (16.4, 2411),
    (17.3, 2367),
    (20.2, 2233),
    (27.9, 1978),
    (46.2, 1097)]

mvals = []
fact = (1978.0 - 2425.0) / (27.9-16.0)
base = 16.0
pump_events = []

def val_to_celsius(val):
    return base + (val-2425)/fact

def get_roof_temp():
    global mvals
    ch1_val=get_adc_int(1)
    mvals.append(ch1_val)
    if len(mvals) > 20:
        mvals.pop(0)
    mavg = int(sum(mvals) / float(len(mvals)))

    return val_to_celsius(mavg)

def get_water_temp():
    ch0_val=get_adc_int(0)
    return val_to_celsius(ch0_val)

def get_valve():
    off = GPIO.input(4)
    on = GPIO.input(25)

    if on and not off:
        return True
    elif off and not on:
        return False
    else:
        logger.critical('Valve in unknown state. Setting to off')
        set_valve(False)

def set_valve(on):
    if on:
        GPIO.output(4, False)
        GPIO.output(25, True)
    else:
        GPIO.output(25, False)
        GPIO.output(4, True)

def get_pump():
    return GPIO.input(22) != 0

def set_pump(on):
    if on:
        GPIO.output(22, True)
    else:
        GPIO.output(22, False)

    pump_events.append(time.time())
    if len(pump_events) > 5:
        val = pump_events.pop(0)   # look at timestamp of 5 switches ago
        if time.time() - val < 10*60:
             logger.critical('Pump switched 5 times in less than 10 minutes!!! Exiting. STOP.')
             raise Exception('Pump switched 5 times in less than 10 minutes!!! Exiting. STOP.')

try:
    connection = Connection('192.168.1.6', 27017)
    db = connection.swimsuite_database
    posts = db.posts
    events = db.events


    while(True):


        w = get_water_temp()
        r = get_roof_temp()

        v = get_valve()

        # pump
        now = time.time()
        now_st = time.localtime(now)
        today_start = time.mktime((now_st[0], now_st[1], now_st[2], PUMP_ON_HOUR, PUMP_ON_MIN, 0, 0, 0, -1))
        today_stop = time.mktime((now_st[0], now_st[1], now_st[2], PUMP_OFF_HOUR, PUMP_OFF_MIN, 0, 0, 0, -1))
        today_max = time.mktime((now_st[0], now_st[1], now_st[2], PUMP_OFF_MAX_HOUR, PUMP_OFF_MAX_MIN, 0, 0, 0, -1))

        if now  >= today_start and now <= today_stop:
            if not get_pump():
                logger.info('Starting pump')
                events.insert({'time': int(now), 'event':'starting pump'})
                set_pump(True)
        else:
            if get_pump() and (r < w or w >= MAX_TEMP or time.time() > today_max):
                logger.info('Stopping pump')
                events.insert({'time': int(now), 'event':'stopping pump'})
                set_pump(False)

        # solar valve
        started = time.time()
        p = get_pump()

        logger.debug('water = %.2f, roof = %.2f, valve: %s, pump: %s' % (w, r, v, p))

        if time.time() > last_valve_time+HISTHERESIS:
            if w > MAX_TEMP and get_valve():
                logger.info('maximum temperature reached. switching valve off.')
                events.insert({'time': int(now), 'event': 'max temp. switching valve off'})
                last_valve_time = time.time()
                set_valve(False)
            elif r > w and w < MAX_TEMP and not get_valve():
                logger.info('roof higher than water, and valve off. switching valve on')
                events.insert({'time': int(now), 'event': 'switching valve on'})
                last_valve_time = time.time()
                set_valve(True)
            elif r < w and get_valve():
                logger.info('roof lower than water, and valve on. switching valve off')
                events.insert({'time': int(now), 'event': 'switching valve off'})
                last_valve_time = time.time()
                set_valve(False)

        posts.insert({'time': int(time.time()), 'water': w,
              'roof': r, 'valve': v, 'pump': p})

        time.sleep(started+10-time.time())
except Exception, e:
    logger.critical('swimsuite stopping: %s' % e)
