class IndicatorStatus:
    On, Off = range(2)


class BackgroundStatus:
    Ok, Warn, Error, Info = range(4)


class GadgetBase(object):
    def __init__(self):
        pass

    def set_status_lines(self, lines):
        print("HW:set_status_lines:\n%s" % '\n'.join(lines))

    def set_build_indicator(self, i, status):
        if status == IndicatorStatus.Off:
            print('[%d] OFF' % i)
        elif status == IndicatorStatus.On:
            print('[%d] ON' % i)
        elif status == IndicatorStatus.FadeInOut:
            print('[%d] FADE' % i)
        elif status == IndicatorStatus.Blink:
            print('[%d] BLINK' % i)
        else:
            raise ValueError('Unsupported build indicator status')

    def clear_build_indicators(self):
        pass

    def display_boot_animation(self, anim_time=10.0):
        pass

    def set_background_status(self, status):
        pass
