class Trigger(object):
    def __init__(self, thrown):
        self.thrown = thrown
    
    def __repr__(self):
        return 'Trigger({0})'.format(self.thrown)
    
    def __str__(self):
        return repr(self)

    def get_thrown(self):
        return self.thrown
