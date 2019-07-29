import requests
from bs4 import BeautifulSoup
import os




 

response = requests.get("https://mfarm.co.ke/trends")



soup = BeautifulSoup(response.text, features ="html.parser")
table = soup.find("table",class_= "price-table")

header = "Product, Location,Quantity, Low(kshs), high(kshs)"
headers= [header.text for header in table.find_all('th')]
row = []
for row in table.findAll('tr'):

     cells= row.findAll('td')

     #print(cells)
     
     if len(cells)!= 0:
        no_cells = cells[1]


file = open(os.path.expanduser("Farmer_market.csv"), "wb")
file.write(bytes(header,encoding = "utf-8", errors = "ignore"))
file.write(bytes(cells,encoding = "utf-8", errors ="ignore"))

