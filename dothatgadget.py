import math
import time

from gadget import GadgetBase, IndicatorStatus, BackgroundStatus
from dothat import lcd
from dothat import backlight


class DotHatGadget(GadgetBase):
    NUM_COLS = 16
    NUM_ROWS = 3

    MIN_LED_BRIGHTNESS = 0
    MAX_LED_BRIGHTNESS = 255

    NUM_LEDS = 6
    ANIM_INTERVAL_SECONDS = 0.01

    def __init__(self):
        super(DotHatGadget, self).__init__()

    def display_boot_animation(self, anim_time=10.0):
        elapsed_time = 0.0
        x = 0
        while True:
            if elapsed_time >= anim_time:
                break
            x += 1
            backlight.sweep((x % 360) / 360.0)
            backlight.set_graph(abs(math.sin(x / 100.0)))
            time.sleep(DotHatGadget.ANIM_INTERVAL_SECONDS)
            elapsed_time += DotHatGadget.ANIM_INTERVAL_SECONDS
        self.clear_build_indicators()
        self.set_background_status(BackgroundStatus.Info)


    def set_status_lines(self, lines):
        lcd.clear()
        for i in range(min(len(lines), DotHatGadget.NUM_ROWS)):
            lcd.set_cursor_position(0, i)
            lcd.write(lines[i][:DotHatGadget.NUM_COLS])

    def set_build_indicator(self, i, status):
        if status == IndicatorStatus.On:
            backlight.graph_set_led_state(i, 1)
        else:
            backlight.graph_set_led_state(i, 0)

    def clear_build_indicators(self):
        backlight.graph_off()

    def set_background_status(self, status):
        if status == BackgroundStatus.Ok:
            backlight.rgb(0, 255, 0)
        elif status == BackgroundStatus.Error:
            backlight.rgb(255, 0, 0)
        elif status == BackgroundStatus.Warn:
            backlight.rgb(255, 255, 0)
        else:
            backlight.rgb(0, 0, 255)
