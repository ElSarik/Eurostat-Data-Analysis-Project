import requests
import re
from bs4 import BeautifulSoup

def cofog_scrap():
    cofog_divisions = {}

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '\
            'AppleWebKit/537.36 (KHTML, like Gecko) '\
            'Chrome/75.0.3770.80 Safari/537.36'}

    # Send a GET request to the website and retrieve the HTML
    url = "https://www.oecd-ilibrary.org/sites/800c1533-en/index.html?itemId=/content/component/800c1533-en"
    response = requests.get(url, headers=headers)
    html = response.text

    # Use Beautiful Soup to parse the HTML and extract the table
    soup = BeautifulSoup(html, "html.parser")
    # table = soup.findAll("tbody", class_='web_group-tbody')
    table = soup.find("tbody", {"class":"web_group-tbody"})


    # Iterate through the rows of the table and extract the data
    for row in table.find_all("tr"):

        cells = row.find_all("td")

        division = re.sub(r'\n', '', cells[0].text)

        group = []

        item_list = cells[1].find_all("li")
        for item in item_list:
            item = re.sub(r'\n', '', item.text)
            item = re.sub(r'Social protection n.e.c', 'Social protection n.e.c.', item)
            group.append(item)

        cofog_divisions[division] = group
    
    return cofog_divisions