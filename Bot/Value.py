from enum import Enum


class Value:
    class Type(Enum):
        ABS = 0
        REL = 1

    def __init__(self, obj: str):
        if not isinstance(obj, str):
            obj = str(obj)
        if obj.endswith('%'):
            self.type = Value.Type.REL
        else:
            self.type = Value.Type.ABS

        #Issue 21 float parsing
        self.v = float(obj.replace('%', '').replace(',', '.'))

    def is_abs(self):
        return self.type == Value.Type.ABS

    def is_rel(self):
        return self.type == Value.Type.REL

    def get_val(self, rel_val):
        if self.is_abs():
            return self.v
        if self.v == 100:
            return rel_val
        return round(rel_val * self.v / 100, 8)

    def __eq__(self, other):
        return self.v == other.v and self.type == other.type

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return ('{:.0f}%'.format(self.v) if self.v.is_integer() else '{:.2f}%'.format(
            self.v)) if self.is_rel() else '{:.8f}'.format(self.v)

    def __repr__(self):
        return self.__str__()
