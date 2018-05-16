class APIResult:
    def __init__(self, status=0, msg=None):
        self.status = status
        self.msg = msg

    @classmethod
    def OKResult(cls, msg=None):
        return {'status': 0, 'msg': msg}

    @classmethod
    def ErrorResult(cls, status, msg=None):
        return {'status': status, 'msg': msg}
