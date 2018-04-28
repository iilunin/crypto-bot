class CustomSerializable:
    def format_float(self, flt):
        if flt.is_integer():
            return '{:.0f}'.format(flt)
        return '{:.08f}'.format(flt)

    def serializable_dict(self):
        return self.__dict__
