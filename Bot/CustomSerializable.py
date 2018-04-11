class CustomSerializable:
    def format_float(self, flt):
        return '{:.08f}'.format(flt)

    def serializable_dict(self):
        return self.__dict__
