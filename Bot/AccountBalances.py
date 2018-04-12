class Balance:
    def __init__(self, getter):
        self.__getter = getter

    @property
    def avail(self):
        return self.__getter()['f']

    @property
    def locked(self):
        return self.__getter()['l']

    @avail.setter
    def avail(self, val):
        self.__getter()['f'] = val

    @locked.setter
    def locked(self, val):
        self.__getter()['l'] = val


class AccountBalances:
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        if not self.__dict__:
            self.bal_dict = {}

    def update_balances(self, new_balances):
        self.bal_dict.update(new_balances)

    def get_balance(self, asset):
        return Balance(lambda: self.bal_dict[asset])
