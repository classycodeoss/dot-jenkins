from gadget import GadgetBase, IndicatorStatus
from dothat import lcd
from dothat import backlight


class DotHatGadget(GadgetBase):
    NUM_COLS = 16
    NUM_ROWS = 3

    MIN_LED_BRIGHTNESS = 0
    MAX_LED_BRIGHTNESS = 255

    def __init__(self):
        super(DotHatGadget, self).__init__()

    def set_status_lines(self, lines):
        lcd.clear()
        for i in range(min(len(lines), DotHatGadget.NUM_ROWS)):
            lcd.set_cursor_position(0, i)
            lcd.write(lines[i][:DotHatGadget.NUM_COLS])

    def set_build_indicator(self, i, status):
        if status == IndicatorStatus.On:
            backlight.set(i, DotHatGadget.MAX_LED_BRIGHTNESS)
        elif status == IndicatorStatus.Off:
            backlight.set(i, DotHatGadget.MIN_LED_BRIGHTNESS)


