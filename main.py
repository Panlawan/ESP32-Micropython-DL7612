#import pyb

import ure
import BME280, time, ubinascii, machine
from bmp280 import *
import struct
from machine import UART, Pin, SoftI2C,PWM
from struct import unpack
from cayennelpp import CayenneLPP
from micropython import const
import ssd1306
downlinks = ""

oled_vcc_pin = machine.Pin(5, machine.Pin.OUT)
cycle = 0
frequency = 20000
pwm = PWM(Pin(23), frequency)

pwm.duty(1023)
time.sleep(1)
pwm.duty(0)

LED_GPIO = const(2)  # define a constant
led = machine.Pin(LED_GPIO, mode=machine.Pin.OUT)  # GPIO output
led = Pin(2, Pin.OUT)
led.on()
print('on')
time.sleep(1)
led.off()
print('off')
#adc = pyb.ADCAll(12)    # create an ADCAll object
#rtc = pyb.RTC()
#rtc.wakeup(60000)
#led = pyb.LED(1)

time.sleep(5)
oled_vcc_pin.value(1)

temp = 0.0
pres = 0.0
hum = 0.0
rstr = ""
p = ""
i2c = SoftI2C(scl=Pin(15), sda=Pin(4), freq=100000)
#i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
#bme = BME280.BME280(i2c=i2c)
bmp = BMP280(i2c)

bmp.use_case(BMP280_CASE_WEATHER)
bmp.oversample(BMP280_OS_HIGH)

bmp.temp_os = BMP280_TEMP_OS_8


oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

uart = UART(2, 115200,timeout=300)
#uart.write("AT+NRB\r\n")
#print(uart.read())

oled.fill(0)
oled.text('ESP32 TTNV3', 0, 0)
oled.text('waiting.....', 0, 20)
oled.show()
time.sleep(3)

def sendATcommand(ATcommand):
    print("Command: {0}\r\n".format(ATcommand))
    print(ATcommand)
    uart.write("{0}\r\n".format(ATcommand))
    time.sleep(0.5)
    rstr = uart.read().decode("utf-8")
    
    #if rstr:
    #    rstr
    print(rstr)
    oled.fill(0)
    oled.text(rstr, 0, 30)
    oled.show()
    return rstr

def get_RSSI():
    msg = sendATcommand("AT+CSQ")
    
    try:
        if msg:
            rstr = str(msg, 'utf-8')
            #print ("string is UTF-8, length %d bytes" % len(rstr))
            if len(rstr) <20:
                 RSSI,SNRA = msg.split(":")[1].split(",")
                #print (type(RSSI))
                #print (type(SNRA))
        else:
            RSSI="0.0"
            SNRA="0.0"
    except UnicodeError:
        print ("string is not UTF-8")
        RSSI="0.0"
        NRA="0.0"
    
    print("RSSI  =", RSSI )
    print("SNR  =", SNRA )
    SNR=SNRA[:2]
    time.sleep(5)
    

#sendATcommand("AT")
#sendATcommand("AT+INFO")
#sendATcommand("AT+RESTORE")
#sendATcommand("AT+ADR=1")
#sendATcommand("AT+DR=0")
#sendATcommand("AT+CLASS=A")
#sendATcommand("AT+DEVADDR=26041238")

sendATcommand("AT+APPEUI=00000000xxxxxxxx") 
sendATcommand("AT+DEVEUI=CD4905D0xxxxxxxx") 
sendATcommand("AT+APPKEY=B01DA4B37D7CB4CE8B9C298Cxxxxxxxx")
sendATcommand("AT+CLASS=C")
sendATcommand("AT+SAVE")

sendATcommand("AT+APPEUI") 
sendATcommand("AT+DEVEUI") 
sendATcommand("AT+APPKEY")

#sendATcommand("AT+ACTIVATE=1") #OTA Activate
#sendATcommand("AT+ISMBAND=2") #AS1
sendATcommand("AT+NCONFIG")
#sendATcommand("AT+SAVE") 
#sendATcommand("AT+CHSET")


###LOOP OTAA
rstr = sendATcommand("AT+NRB")
time.sleep(20)
rstr = sendATcommand("AT+CGATT")
tryno = 1

while rstr != "+CGATT:1":
    rstr = sendATcommand("AT+CGATT")
    print("Respond String")
    print(rstr)
    if rstr.startswith("+CGATT:1"):
        print("*******OTAA OK*******")
        break
    print("Retry OTAA Continue")
    b = str(tryno)
    print(b[-1:])
    if b[-1:] == "0":
        print("YES")
        sendATcommand("AT+NRB")
    else:
        print("NO")
    tryno = tryno + 1

    time.sleep(20.0)
print("Join Success")
oled.text('joined.....', 0, 30)
oled.show()
###END LOOP OTAA


cnt = 1
while True:
    #led.value(1)
    print("Packet No #{}".format( cnt ) )
    bmp.force_measure()
    #temp,pa,hum = bme.values
    #temp = bme.temperature
    temp = bmp.temperature
    #hum = bme.humidity
    #pres = bme.pressure
    pres = bmp.pressure

#    vbat = adc.read_core_vbat()      # read MCU VBAT
#    print(vbat)
    
    print("********BME280 values:")
    print("temp:",temp," Hum:",hum ,"PA:", pres)

    c = CayenneLPP()
    c.addTemperature(1, float(temp)) 
#   c.addRelativeHumidity(1, float(hum))
#   c.addAnalogInput(1, float(vbat))
    c.addBarometricPressure(1, (float(pres)))
    d = (ubinascii.hexlify(c.getBuffer()))
    print(" — — — — -Start Send Status — — — — — — ")
    print("AT+NMGS={0},{1}\r\n".format(int(len(d)/2),(d.decode("utf-8"))))
    #sendATcommand("AT+NMGS={0},{1}".format(int(len(d)/2),(d.decode("utf-8"))))

    #p = ure.search("0100(.+?)\r\n", uart.read().decode("utf-8"))
    uart.write("AT+NMGS={0},{1}\r\n".format(int(len(d)/2), (d.decode('utf-8'))))
    p = ure.search("0100(.+?)\r\n", uart.read().decode("utf-8")) #Node
    #p = uart.read().decode("utf-8")
    print(p)
    try:
        #print (p.group(0))
        pgroup=(p.group(0))
        downlinks = str(pgroup)
        print(downlinks)
    except AttributeError:
        pgroup=""
        print ("Not found Downlink Packet")

    if downlinks[0:4] == "0100":
        cycle = int((1023/100) * int(downlinks[6:], 16))
        print(cycle)
        
        if int(downlinks[4:6]) == 1:
            print("Command1 Detected: On LED =============>")
            pwm.duty(cycle)
            print("Brightness = "+str(cycle))
        elif int(downlinks[4:6]) == 0:
            print("Command1 Detected: Off LED =============>")
            print(cycle)
            pwm.duty(0)
        else:
            print("No Known Command Detect")
   
    print("— — — — -End Send Status — — — — — — ")
    #get_RSSI()
 
    oled.fill(0)
    oled.text('ESP32 TTNV3', 0, 0)
    oled.text("Packet No:"+str(cnt), 0, 10)
    oled.text("T:"+str(temp), 0, 30)
    oled.text("Pa:"+str(pres*0.01), 0, 40)
    oled.text("Brightness"+str(cycle), 0, 50)
    oled.show()  
    print("********End Signal values:*********")
    
    cnt = cnt + 1
    time.sleep(60.0)  

