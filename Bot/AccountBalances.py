from Bot.FXConnector import FXConnector


class Balance:
    def __init__(self, getter, invalidate):
        self.__getter = getter
        self.invalidate_fn = invalidate

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

    def invalidate(self):
        if self.invalidate_fn:
            self.invalidate_fn()


class AccountBalances:
    def __init__(self, fx: FXConnector):
        self.bal_dict = {}
        self.fx = fx

    def update_balances(self, new_balances):
        self.bal_dict.update(new_balances)

    def invalidate(self):
        self.update_balances(self.fx.get_all_balances_dict())

    def get_balance(self, asset):
        return Balance(lambda: self.bal_dict[asset], self.invalidate)
