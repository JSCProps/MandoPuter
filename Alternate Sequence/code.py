"""
MandoPuter will display text in a Mandalorian font on a tiny LCD display

File   - code.py
Author - Jon Breazile

https://github.com/Breazile/MandoPuter

Font credits to ErikStormtrooper, the bitmap fonts were created from his TrueType font
http://www.erikstormtrooper.com/mandalorian.htm
"""
import time
import board
import neopixel
import displayio
import terminalio
import adafruit_dotstar as dotstar
import adafruit_imageload
from analogio import AnalogIn
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_st7789 import ST7789
from adafruit_st7735r import ST7735R
from adafruit_ssd1331 import SSD1331
from adafruit_ssd1351 import SSD1351
from adafruit_displayio_ssd1306 import SSD1306

"""
  ----------- User configurable items -----------

  This is where you can customize your setup. Some lines are commented out
  which means the line is not active. A commented line starts with a #
  Some items should have only one selection active like BOARD_TYPE and DISPLAY

  Recommended screen rotations (you can tweak it depending upon how you mount)

  Screen          Rotation
  0.96 LCD        270
  0.96 OLED       180
  0.96 Mono OLED  180
  1.14 LCD        270
  1.27 OLED       0
  1.3 LCD         0
  1.3 Mono OLED   0
  1.44 LCD        0
  1.5 OLED        0
  1.54 LCD        0
  1.8 LCD         180

"""
BOARD_TYPE     = "Feather"                            # Feather M4 Express
#BOARD_TYPE    = "ItsyBitsy"                          # ItsyBitsy M4 Express
#DISPLAY       = "0.96 LCD"                           # Adafruit 0.96" LCD display  https://www.adafruit.com/product/3533
#DISPLAY       = "0.96 OLED"                          # Adafruit 0.96" OLED display https://www.adafruit.com/product/684
#DISPLAY       = "0.96 Mono OLED"                     # Adafruit 1.3" Mono OLED display https://www.adafruit.com/product/326
#DISPLAY        = "1.14 LCD"                           # Adafruit 1.14" LCD display  https://www.adafruit.com/product/4383
#DISPLAY       = "1.27 OLED"                          # Adafruit 1.27" OLED display https://www.adafruit.com/product/1673
DISPLAY       = "1.3 LCD"                            # Adafruit 1.3" LCD display   https://www.adafruit.com/product/4313
#DISPLAY       = "1.3 Mono OLED"                      # Adafruit 1.3" Mono OLED display https://www.adafruit.com/product/938
#DISPLAY       = "1.44 LCD"                           # Adafruit 1.44" LCD display  https://www.adafruit.com/product/2088
#DISPLAY       = "1.5 OLED"                           # Adafruit 1.5" OLED display  https://www.adafruit.com/product/1431
#DISPLAY       = "1.54 LCD"                           # Adafruit 1.54" LCD display  https://www.adafruit.com/product/3787
#DISPLAY       = "1.8 LCD"                            # Adafruit 1.8" LCD display   https://www.adafruit.com/product/358
#TEXT_ROTATION = 0                                    # Orientation of the text shown on the screen
#TEXT_ROTATION = 90                                   # Orientation of the text shown on the screen
#TEXT_ROTATION = 180                                  # Orientation of the text shown on the screen
TEXT_ROTATION  = 270                                  # Orientation of the text shown on the screen
messages       = [ "JPS", "PJS", "JPS", "SPA", "JPS", "TBO", "KUH", "MKM", "TLO", "PAG", "MKM", "JPS", "MKM"] # Mandalorian charater sequence that is shown on the display
delays         = [  2.15,  0.17,  1.70,  0.15,  1.00,  0.25,  0.25,  0.25,  0.40,  0.35,  0.50,  0.20, 0.94] # Time that each character group is shown 0.50 is 500 milliseconds, or 1/2 of a second
TEXT_COLOR     = 0xFF0000                             # Red on black (you can chose colors here - https://www.color-hex.com/)
#TEXT_COLOR    = 0xFFFFFF                             # White on black - you might want this if you put a red window over the display
#SHOW_CREST     = 1                                    # Display the crest image after the text sequence
SHOW_CREST    = 0                                    # Do not display the crest image after the text sequence
#CREST          = "razorcrest.bmp"                   # File name of the BMP graphic to be shown after each text sequence
#CREST          = "critical.bmp"                # Red Mudhorn
#CREST_HOLD     = 3.00                                 # How long the crest is displayed in seconds
# -----------------------------------------------

# set some parameters used for shapes and text
BATTERY_80        = 3.75   # voltage for the battery at 80% capacity
BATTERY_30        = 3.53   # voltage for the battery at 30% capacity
BATTERY_15        = 3.48   # voltage for the battery at 15% capacity
BATT_SAMPLE_AVG   = 50     # rolling number of battery readings to average (IIR filter)
VOLT_LOG_INVERVAL = 00     # log voltage every n seconds. Set to 0 to disable battery logging
                           # for logging to work read the comments in LogVoltage() below

# setup the onboard neopixel LED, we will use it later to show battery level
if BOARD_TYPE == "Feather" :
    led = neopixel.NeoPixel(board.NEOPIXEL, 1)  # onboard neopixel
elif BOARD_TYPE == "ItsyBitsy":
    led = dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1) # onboard dotstar
led.brightness = 0.05  # dim the LED to 5%
led[0] = (255, 0, 255) # purple

def get_voltage(pin):
    return (pin.value * 3.3) / 65536 * 2

# Setup communication lines to the display
spi = board.SPI()
if BOARD_TYPE == "Feather" :
    tft_cs = board.D6   # Feather M4 Express
    tft_dc = board.D9
    lcd_rst = board.D5
    vbat_voltage = AnalogIn(board.VOLTAGE_MONITOR) # for measuring battery voltage
elif BOARD_TYPE == "ItsyBitsy":
    tft_cs = board.D2   # ItsyBitsy M4 Express
    tft_dc = board.D3
    lcd_rst = board.D4
    # battery voltage measurements need a jumper from batt to A1
    vbat_voltage = AnalogIn(board.A1)

# Setup the bus, display object, and font for the display
displayio.release_displays()
if DISPLAY == "0.96 LCD":
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=lcd_rst)
    display = ST7735R(display_bus, rotation=TEXT_ROTATION, width=160, height=80, colstart=24, bgr=True)
    font = bitmap_font.load_font("mandalor80.bdf")  # 80 pixel tall bitmap font
elif DISPLAY == "0.96 OLED":
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=lcd_rst)
    display = SSD1331(display_bus, rotation=TEXT_ROTATION, width=96, height=64)
    font = bitmap_font.load_font("mandalor64.bdf")  # 64 pixel tall bitmap font
elif DISPLAY == "0.96 Mono OLED":
    TEXT_COLOR = 0xFFFFFF  # it's monochrome, you can only do white
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=lcd_rst, baudrate=1000000)
    display = SSD1306(display_bus, rotation=TEXT_ROTATION, width=128, height=64)
    font = bitmap_font.load_font("mandalor64.bdf")  # 64 pixel tall bitmap font
elif DISPLAY == "1.14 LCD":
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs)
    display = ST7789(display_bus, rotation=TEXT_ROTATION, width=240, height=135, rowstart=40, colstart=53)
    font = bitmap_font.load_font("mandalor135.bdf")  # 135 pixel tall bitmap font
elif DISPLAY == "1.27 OLED":
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=lcd_rst, baudrate=16000000)
    display = SSD1351(display_bus, rotation=TEXT_ROTATION, width=128, height=96)
    font = bitmap_font.load_font("mandalor96.bdf")  # 96 pixel tall bitmap font
elif DISPLAY == "1.3 LCD":
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=lcd_rst)
    display = ST7789(display_bus, rotation=TEXT_ROTATION, width=240, height=240, rowstart=80)
    font = bitmap_font.load_font("mandalor180.bdf")  # 240 pixel tall bitmap font
elif DISPLAY == "1.3 Mono OLED":
    TEXT_COLOR = 0xFFFFFF  # it's monochrome, you can only do white
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=lcd_rst, baudrate=1000000)
    display = SSD1306(display_bus, rotation=TEXT_ROTATION, width=128, height=64)
    font = bitmap_font.load_font("mandalor64.bdf")  # 64 pixel tall bitmap font
elif DISPLAY == "1.44 LCD":
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=lcd_rst)
    display = ST7735R(display_bus, rotation=TEXT_ROTATION, width=128, height=128, colstart=2, rowstart=1)
    font = bitmap_font.load_font("mandalor96.bdf")  # 128 pixel tall bitmap font
elif DISPLAY == "1.5 OLED":
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=lcd_rst, baudrate=16000000)
    display = SSD1351(display_bus, rotation=TEXT_ROTATION, width=128, height=128)
    font = bitmap_font.load_font("mandalor96.bdf")  # 128 pixel tall bitmap font
elif DISPLAY == "1.54 LCD":
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=lcd_rst)
    display = ST7789(display_bus, rotation=TEXT_ROTATION, width=240, height=240, rowstart=80)
    font = bitmap_font.load_font("mandalor180.bdf")  # 240 pixel tall bitmap font
elif DISPLAY == "1.8 LCD":
    # need to reverse the color bytes
    TEXT_COLOR = ((TEXT_COLOR & 0xFF0000) >> 16) + (TEXT_COLOR & 0x00FF00) + ((TEXT_COLOR & 0x0000FF) << 16)
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=lcd_rst)
    if (TEXT_ROTATION == 0) or (TEXT_ROTATION == 180):
        display = ST7735R(display_bus, rotation=TEXT_ROTATION, width=128, height=160)
        font = bitmap_font.load_font("mandalor96.bdf")  # 160 pixel tall bitmap font
    else:
        display = ST7735R(display_bus, rotation=TEXT_ROTATION, width=160, height=128)
        font = bitmap_font.load_font("mandalor120.bdf")  # 128 pixel tall bitmap font

# Load the crest graphic
if SHOW_CREST == 1 :
    # Create the crest image centered on the display
    bitmap, palette = adafruit_imageload.load(CREST, bitmap=displayio.Bitmap, palette=displayio.Palette)
    x = int((display.width - bitmap.width) / 2)
    y = int((display.height - bitmap.height) / 2)
    if x < 0 : x = 0
    if y < 0 : y = 0
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette, x=x, y=y)
    crest = displayio.Group()
    crest.append(tile_grid)

# font rendering function, center text on the screen
def render_font(glyphs, group):
    text = label.Label(font, text=glyphs, color=TEXT_COLOR)
    text.x = int(((display.width - text.bounding_box[2])/2)-1)
    text.y = int((display.height / 2)-1)
    group.append(text)

# render each sequence of characters using the bitmap font
splashes = []
index = 0
for msg in messages:
    splashes.append(displayio.Group())
    render_font(msg, splashes[index])
    index = index + 1

# Used for changing the color of the onboard LED
def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return 0, 0, 0
    if pos < 85:
        return int(255 - pos * 3), int(pos * 3), 0
    if pos < 170:
        pos -= 85
        return 0, int(255 - pos * 3), int(pos * 3)
    pos -= 170
    return int(pos * 3), 0, int(255 - (pos * 3))

# Log the battery voltage (only used in development of battery voltage thresholds)
# you'll need to have boot.py copied to the controller
# Connect pin D4 to GND on power on in order for this to work (only on the Feather)
# see https://learn.adafruit.com/circuitpython-essentials/circuitpython-storage
def LogVoltage(voltage):
    try:
        with open("/battvolt.txt", "a") as fp:
            fp.write('{0:f}\n'.format(voltage))
            fp.flush()
    except OSError as e:
        # Could not write to the file. Most likely because the correct boot.py
        # was not copied to the system, and the D4 pin was not grounded on power on
        delay = 0.1
        if e.args[0] == 28:
            delay = 0.01
        i = 0
        while True:
            i = (i + 1) % 256  # run from 0 to 255
            led.fill(wheel(i))
            time.sleep(delay)

# read and average the battery voltage with an IIR filter
def GetAvgBattVoltage(voltage) :
    voltage = (get_voltage(vbat_voltage) * (1 / BATT_SAMPLE_AVG)) + (voltage * (1 - (1 / BATT_SAMPLE_AVG)))
    return voltage

# loop through and display each message for the specified duration
next_log = time.time() + VOLT_LOG_INVERVAL
avg_voltage = get_voltage(vbat_voltage)

while True:
    index = 0
    for splash in splashes:
        avg_voltage = GetAvgBattVoltage(avg_voltage)
        display.show(splash)
        avg_voltage = GetAvgBattVoltage(avg_voltage)
        time.sleep(delays[index])
        avg_voltage = GetAvgBattVoltage(avg_voltage)
        index = index + 1

    if SHOW_CREST == 1 :
        display.show(crest)
        time.sleep(CREST_HOLD)
        avg_voltage = GetAvgBattVoltage(avg_voltage)

    # log the battery voltage to a file (only used for development)
    if VOLT_LOG_INVERVAL > 0 :
        if time.time() > next_log :
            print(avg_voltage)
            #LogVoltage(avg_voltage)
            next_log = time.time() + VOLT_LOG_INVERVAL

    # color the onboard neopixel to show battery level
    if avg_voltage > BATTERY_80 :
        led[0] = (0, 255, 0) # green    - 100% to 81% capacity
    elif avg_voltage > BATTERY_30 :
        led[0] = (192, 127, 0) # yellow - 80%  to 31% capacity
    elif avg_voltage > BATTERY_15 :
        led[0] = (255, 46, 0) # orange  - 30%  to 16% capacity
    else:
        led[0] = (255, 0, 0) # red      - 15%  to  0% capacity
