class MarketDataHandler(object):
    def __init__(self):
        self.DATA_BASE_URL = None

    def get_general_data(self):
        raise NotImplementedError("Handler should implement this method.")

    def get_specific_product(self, name):
        raise NotImplementedError("Handler should implement this method.")

    def get_products_by_location(self, name):
        raise NotImplementedError("Handler should implement this method.")