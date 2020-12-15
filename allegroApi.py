import requests, json
from requests_oauthlib import OAuth2

client_id = 'f33c9197ce8449278c008349cd6e328c'
client_secret = 'hY8QO7Xisjnm9q2B3pTMN6v9mIsbdAKMyXcH80hNmppPKhtm2imhdYxfLUcHjqRo'

token_url = "https://allegro.pl/auth/oauth/token"
callback_url = "http://localhost:8000"
auth_url = "https://allegro.pl/auth/oauth/authorize?response_type=code&client_id=092d816d71984ffd87a255b7b0538646&redirect_uri=http://localhost:8000"
search_url = 'https://api.allegro.pl/offers/listing'

class AllegroAPI:
    def __init__(self):
        out = requests.get(auth_url)
        out.close()
        out = requests.post(
            "https://allegro.pl/auth/oauth/token?grant_type=client_credentials",
            auth=(client_id, client_secret)
        )
        self.token = out.json()["access_token"]
        out.close()
        self.get_all_categories()
        self.product_list = None
        self.product_iterator = -1

    def get_all_categories(self):
        head = {
            'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/vnd.allegro.public.v1+json'
        }
        out = requests.get("https://api.allegro.pl/sale/categories", headers = head)
        category_list = {}
        for x in out.json()["categories"]:
            category_list[x["name"]] = x["id"]
        out.close()
        return category_list

    def next_prod(self):
        if self.product_iterator + 1 >= len(self.product_list):
            return False
        self.product_iterator += 1
        return True

    def prev_prod(self):
        if self.product_iterator - 1 < 0:
            return False
        self.product_iterator -= 1
        return True

    def get_current_prod_str(self):
        cur_prod = self.get_current_prod()
        seller = f'{cur_prod["seller"]["login"]}'
        popularity = f'{cur_prod["sellingMode"]["popularity"]}'
        stock = f'{cur_prod["stock"]["available"]}'
        delivery = f'{cur_prod["delivery"]["lowestPrice"]["amount"]} {cur_prod["delivery"]["lowestPrice"]["currency"]}'
        price = f'{cur_prod["sellingMode"]["price"]["amount"]} {cur_prod["sellingMode"]["price"]["currency"]}'
        prod_str = f'\tNazwa: {cur_prod["name"]}\n\tSprzedawca: {seller}\n\tCena: {price}\n\tDostepnych sztuk: {stock}\n\tDostawa: {delivery}\n\tPopularnosc: {popularity}'
        return prod_str

    def get_current_prod(self):
        return self.product_list[self.product_iterator]

    def get_current_url(self):
        cur_prod = self.get_current_prod()
        lower_name = cur_prod["name"].lower()
        lower_name = lower_name.replace(' ','-')
        prod_id = cur_prod["id"]
        url = "https://allegro.pl/oferta/" + f'{lower_name}-{prod_id}'
        return url

    def lose_info(self):
        self.product_list = None
        self.product_iterator = -1

    def search_prod(self, prod, category_id=None):
        head = {
            'authorization': 'Bearer ' + self.token,
            'accept': 'application/vnd.allegro.public.v1+json',
        }
        if category_id:
            link = search_url + '?phrase=' + prod + f'&category.id={category_id}'
        else:
            link = search_url + '?phrase=' + prod
        out = requests.get(link, headers=head)
        self.product_list = out.json()['items']['promoted']
        self.product_iterator = 0
        out.close()
        return len(self.product_list)     # ile znalazlo produktow