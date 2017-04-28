from fractions import Fraction

def frac_to_ratio(frac):
    """Convert Python fraction object to Ratio."""
    try:
        return Ratio(frac.numerator, frac.denominator)
    except AttributeError:
        return frac
    
def prepare_frac(ratio):
    """Convert Ratio objects back to Python fraction."""
    if ratio.__class__ is Ratio:
        return ratio.fraction
    return ratio

class Ratio(object):
    """Fraction object printed as numerator:denominator."""
    def __init__(self, n, d):
        self.fraction = Fraction(n, d)
        
    def __add__(self, other):
        return frac_to_ratio(self.fraction + prepare_frac(other))
    
    def __sub__(self, other):
        return frac_to_ratio(self.fraction - prepare_frac(other))
        
    def __mul__(self, other):
        return frac_to_ratio(self.fraction * prepare_frac(other))
        
    def __div__(self, other):
        return frac_to_ratio(self.fraction / prepare_frac(other))
    
    def __pow__(self, other):
        return frac_to_ratio(self.fraction ** prepare_frac(other))
    
    def __float__(self):
        return float(self.fraction.numerator) / self.fraction.denominator
        
    def __eq__(self, other):
        return float(self) == float(other)
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __repr__(self):
        return str(self.fraction.numerator) + ':' + str(self.fraction.denominator)
    
    def __str__(self):
        return repr(self)
