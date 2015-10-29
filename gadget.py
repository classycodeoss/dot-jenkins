MAX_LINES = 3
MAX_CHARS = 16
MAX_INDICATORS = 6

class IndicatorStatus:
    On, Off = range(2)


class BackgroundStatus:
    Ok, Warn, Error, Info = range(4)


class GadgetBase(object):
    def __init__(self):
        pass

    def set_status_lines(self, lines):
        print("HW:set_status_lines: %s" % '|'.join(lines))

    def set_indicator(self, i, status):
        if i >= MAX_INDICATORS:
            return
        if status == IndicatorStatus.Off:
            print('HW:set_indicator [%d] OFF' % i)
        elif status == IndicatorStatus.On:
            print('HW:set_indicator [%d] ON' % i)
        elif status == IndicatorStatus.FadeInOut:
            print('HW:set_indicator [%d] FADE' % i)
        elif status == IndicatorStatus.Blink:
            print('HW:set_indicator [%d] BLINK' % i)
        else:
            raise ValueError('Unsupported build indicator status')

    def clear_indicators(self):
        pass

    def display_boot_animation(self, anim_time=10.0):
        pass

    def set_background_status(self, status):
        pass
