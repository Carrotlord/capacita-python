MINUTES_PER_HR = 60

def plural(num, word):
    return word if num == 1 else word + 's'

def make_duration(duration_str):
    args = (int(s) for s in duration_str.split(':'))
    return Duration(*args)

class Duration(object):
    def __init__(self, hours, minutes):
        self.hours = hours
        self.minutes = minutes
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

    def __str__(self):
        return '{0} {1}, {2} {3}'.format(
            self.hours, plural(self.hours, 'hour'),
            self.minutes, plural(self.minutes, 'minute')
        )

    def __repr__(self):
        return str(self)
