MINUTES_PER_HR = 60
MINUTE_RATIOS = [0, 2, 3, 5, 7, 8, 10, 12, 13, 15, 17, 18,
20, 22, 23, 25, 27, 28, 30, 32, 33, 35, 37, 38,
40, 42, 43, 45, 47, 48, 50, 52, 53, 55, 57, 58,
60, 62, 63, 65, 67, 68, 70, 72, 73, 75, 77, 78,
80, 82, 83, 85, 87, 88, 90, 92, 93, 95, 97, 98]

def plural(num, word):
    return word if num == 1 else word + 's'

def make_duration(duration_str):
    if '.' in duration_str:
        return make_partial_hours(duration_str)
    args = (int(s) for s in duration_str.split(':'))
    return Duration(*args)

def to_minute(partial_hour):
    scale = 100.0
    num_digits = len(partial_hour)
    if num_digits == 1:
        partial_hour += '0'
    elif num_digits > 2:
        scale *= 10 ** (num_digits - 2)
    partial_hour = int(partial_hour)
    try:
        return MINUTE_RATIOS.index(partial_hour)
    except ValueError:
        # No exact match, so just approximate:
        return (MINUTES_PER_HR * partial_hour) / scale

def make_partial_hours(duration_str):
    pieces = duration_str.split('.')
    hours = int(pieces[0])
    minutes = to_minute(pieces[1])
    return Duration(hours, minutes)

class Duration(object):
    def __init__(self, hours, minutes):
        self.hours = hours
        self.minutes = minutes
        if not isinstance(minutes, float):
            self.normalize()

    def normalize(self):
        self.hours += self.minutes / MINUTES_PER_HR
        self.minutes %= MINUTES_PER_HR
        if self.hours < 0 and self.minutes != 0:
            self.hours += 1
            self.minutes -= MINUTES_PER_HR

    def __add__(self, other):
        return Duration(self.hours + other.hours, self.minutes + other.minutes)

    def __sub__(self, other):
        return Duration(self.hours - other.hours, self.minutes - other.minutes)

    def __mul__(self, scale):
        return Duration(self.hours * scale, self.minutes * scale)

    def __rmul__(self, scale):
        return self * scale

    def to_hours(self):
        return self.hours + self.minutes / float(MINUTES_PER_HR)

    def to_approx_hours(self):
        if isinstance(self.minutes, int) and 0 <= self.minutes < MINUTES_PER_HR:
            return self.hours + (MINUTE_RATIOS[self.minutes] / 100.0)
        return self.to_hours()

    def __str__(self):
        return '{0} {1}, {2} {3}'.format(
            self.hours, plural(self.hours, 'hour'),
            self.minutes, plural(self.minutes, 'minute')
        )

    def __repr__(self):
        return str(self)
