import requests
from bs4 import BeautifulSoup

from ujumbe.apps.marketdata.handlers.base import MarketDataHandler


class Mfarm(MarketDataHandler):
    def __init__(self):
        super(Mfarm, self).__init__()
        self.DATA_BASE_URL = "https://mfarm.co.ke/trends"

    def extract_data_from_html(self, html):
        soup = BeautifulSoup(html, features="html.parser")
        table = soup.find("table", class_="price-table")
        data = []
        for i, row in enumerate(table.findAll("tr")):
            if i == 0:
                # The first row contains headers, skip it else corrupt db data
                continue
            row_data = dict(currency_code="KES")
            for j, cell in enumerate(row.findAll("td")):
                if j == 0:
                    row_data["product_name"] = cell.string
                elif j == 1:
                    row_data["location_name"] = cell.string
                elif j == 2:
                    quantity_parts = cell.string.replace(" ", "").split("\n")
                    row_data["quantity"] = float(quantity_parts[1])
                    row_data["measurement_unit"] = quantity_parts[2]
                elif j == 3:
                    row_data["low_price"] = float(cell.string.replace(",", ""))
                elif j == 4:
                    row_data["high_price"] = float(cell.string.replace(",", ""))
            data.append(row_data)
        return data

    def get_general_data(self):
        response = requests.get(self.DATA_BASE_URL)
        response.raise_for_status() # throw an error and abort in case of any failure
        return self.extract_data_from_html(response.text)

    def get_specific_product(self, name):
        url = "{}/daily?utf8=✓&q={}&commit=Go".format(self.DATA_BASE_URL, name)
        response = requests.get(url)
        response.raise_for_status()  # throw an error and abort in case of any failure
        return self.extract_data_from_html(response.text)

    def get_products_by_location(self, name):
        url = "{}/daily?utf8=✓&q={}&commit=Go".format(self.DATA_BASE_URL, name)
        response = requests.get(url)
        response.raise_for_status()  # throw an error and abort in case of any failure
        return self.extract_data_from_html(response.text)
