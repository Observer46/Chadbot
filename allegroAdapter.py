from chatterbot.logic import BestMatch
from chatterbot.conversation import Statement
from allegroApi import AllegroAPI
import re
import random as rand

ack_list = ["tak", "owszem", "dobrze", "milo z twojej strony", "chce"]
rej_list = ["nie", "spadaj", "podziekuje"]
quit_list = ["zegnaj", "wylacz", "zakoncz", "papa"]
category_ask_list = ["jakie", "pokaz", "co"]
category_select_list = ["z"]
next_list = ["nastepny", "kolejny", "dalej", "next", "jeszcze"]
prev_list = ["wczesniejszy", "poprzedni", "prev", "previous", "wroc"]
take_list = ["biore", "ok", "zamawiam", "chce"]
end_list = ["nie kupuje", "rezygnuje", "odechcialo", "nie chce", "dosc", "wystarczy"]

final_response = [
    "Ciesze sie, ze pomoglem! Moze porozmawiamy o czyms jeszcze",
    "Super! Porozmawiajmy jeszcze",
    "Swietnie, pogadajmy o czyms jeszcze"
]

next_prod_list = [
    "Oto kolejny produkt:",
    "Nastepny produkt:",
    "Kolejna pozycja:"
]

prev_prod_list = [
    "Oto poprzedni produkt:",
    "Poprzedni produkt:",
    "Wczesniejsza pozycja:"
]

thanks_reply_list = [
    "Do uslug!",
    "Cala przyjemnosc po mojej stronie!",
    "Polecam sie na przyszlosc!"
]

show_all_categories_list = [
    "Pokazac wszystkie kategorie?",
    "Czy chcesz wylistowac wszystkie kategorie?"
]

search_reply_list = [
    "W takim razie chetnie pomoge! Co wyszukac?",
    "Super! Co szukac?",
    "Swietnie! Jaki produkt wyszukac?"
]

search_prompt_list = [
    "Chcesz bym wyszukal produkt",
    "Rozpoczac szukanie",
    "Czy zyczysz sobie, bym wyszukal"
]

search_prompt_accept_list = [
    "Znaleziono:", "Wynik:"
]

search_prompt_reject_list = [
    "W takim razie co chcesz wyszukac?",
    "Zatem czego szukamy?",
    "Jaki produkt w takim razie wyszukac?"
]

search_prompt_no_context_list = [
    "Moje pytanie to czy znalezc",
    "Dobra, ale szukac",
    "Okej, ale czy chcesz wyszukac"
]

search_offer_reject_list = [
    "No, skoro nie chcesz mojej pomocy to porozmawiajmy o czyms innym...",
    "Szkoda, ze nie chcesz mojej pomocy :c",
    "Nie to nie! Porozmawiajmy o czyms innym"
]




def get_word_after(text, split_word):
    _, _, rest = text.partition(split_word)
    return rest.split()[0] if rest else None

def random_answer(reply_list):
    idx = rand.randint(0, len(reply_list) - 1)
    return reply_list[idx]


max_anger = 5

class AllegroAdapter(BestMatch):
    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)

        self.search_prod = None
        self.search_category = None
        self.params = {
            "looking_for_present" : False,
            "offering_present_help" : False,
            "got_result" : False
        }
        self.anger_counter = 0
        self.api = AllegroAPI()
        self.categories = self.api.get_all_categories()

    def got_angry(self):
        return self.anger_counter >= max_anger

    def reset_present_search(self):
        self.params["looking_for_present"] = False
        self.params["offering_present_help"] = False
        self.params["got_result"] = False
        self.search_prod = None
        self.search_category = None

    def process_category(self, msg):
        _, _, rest = msg.partition("kategori")
        self.search_category = rest[2:]
        if len(self.search_category) >= 1 and self.search_category[-1] == '?':
            self.search_category = self.search_category[:-1]
        if len(self.search_category) == 0:
            self.search_category = "<empty>"
        for cat in self.categories.keys():
            if cat.lower() == self.search_category:
                self.search_category = cat
                return True
        return False

    def current_product(self):
        return self.product_list[self.product_iterator]

    def find_product_on_allegro(self):     
        count = self.api.search_prod(self.search_prod, self.categories[self.search_category])
        return count

    def get_curr_prod(self):
        return self.api.get_current_prod_str(), self.api.get_current_url()

    def next_prod(self):
        return self.api.next_prod()

    def prev_prod(self):
        return self.api.prev_prod()    

    def can_process(self, stmt):
        return True
    
    def process(self, input, additional_params=None):
        msg = input.text.lower()
        stmt = Statement(text="")
        stmt.confidence = 1

        for q in quit_list:
            if q in msg:
                stmt.text = "Papa!"
                return stmt

        if self.params["got_result"]:
            for take in take_list:
                if take in msg:
                    stmt.text = f"To tu masz link jeszcze raz: {self.api.get_current_url()}\n{random_answer(final_response)}"
                    self.reset_present_search()
                    return stmt

            for end in end_list:
                if end in msg:
                    stmt.text = f"No to rezygnujemy z kupna {self.search_prod}. Porozmawiajmy o czyms jeszcze!"
                    self.reset_present_search()
                    return stmt

            for nxt in next_list:
                if nxt in msg:
                    if self.next_prod():
                        prod, url = self.get_curr_prod()
                        stmt.text = f"{random_answer(next_prod_list)}:\nLink: {url}\n{prod}"
                        return stmt
                    else:
                        stmt.text = "Nie ma kolejnego produktu!"
                        return stmt

            for prev in prev_list:
                if prev in msg:
                    if self.prev_prod():
                        prod, url = self.get_curr_prod()
                        stmt.text = f"{random_answer(prev_prod_list)}:\nLink: {url}\n{prod}"
                        return stmt
                    else:
                        stmt.text = "Nie ma wczesniejszego produktu!"
                        return stmt
            
        if "prezent" in msg and not self.params["looking_for_present"] and not self.params["offering_present_help"]:
            self.params["offering_present_help"] = True
            receiver = get_word_after(msg, "dla")
            stmt.text = "O, chcesz pomocy z szukaniem prezentu"
            if receiver:
                stmt.text = stmt.text + " dla " + receiver + "?"
            else:
                stmt.text = stmt.text + "?"
            return stmt
            
        if self.params["offering_present_help"]:
            for ack in ack_list:
                if ack in msg:
                    self.params["offering_present_help"] = False
                    self.params["looking_for_present"] = True
                    stmt.text = random_answer(search_reply_list)
                    return stmt
            for rej in rej_list:
                if rej in msg:
                    self.params["offering_present_help"] = False
                    stmt.text = random_answer(search_offer_reject_list)
                    self.reset_present_search()
                    return stmt
        if self.params["looking_for_present"] and not self.search_prod:
            if len(msg.split()) == 1:
                self.search_prod = msg
                stmt.text = f"{random_answer(search_prompt_list)} {self.search_prod}?"
                return stmt

        if "szukaj" in msg or "szukac" in msg or "kup" in msg:
            _, _, rest = msg.partition("szukac")
            present = rest[1:]
            if not present:
                _, _, rest1 = msg.partition("szukaj")
                present = rest1[1:]
            if not present:
                _, _, rest2 = msg.partition("kup")
                present = rest2[1:]
            self.search_prod = present
            self.params["looking_for_present"] = True
            if "kategori" in msg:
                if not self.process_category(msg):
                    stmt.text = f"Niestety nie ma takiej kategorii jak {self.search_category} :c"
                    self.search_category = None
                    return stmt
            stmt.text = f"{random_answer(search_prompt_list)} {self.search_prod}?"
            return stmt
        
        if self.params["looking_for_present"] and self.search_prod:
            for ack in ack_list:
                if ack in msg:
                    res_count = self.find_product_on_allegro()
                    if res_count > 0:
                        prod, url = self.get_curr_prod()
                        stmt.text = f"{random_answer(search_prompt_accept_list)} {res_count} produktow!\nLink: {url}\n{prod}"
                        self.params["got_result"] = True
                    else:
                        stmt.text = "Brak rezultatow!"
                        self.reset_present_search()
                    return stmt

            for rej in rej_list:
                if rej in msg:
                    self.search_prod = None
                    stmt.text = random_answer(search_prompt_reject_list)
                    return stmt

            self.anger_counter += 1
            if self.got_angry():
                self.anger_counter = 0
                stmt.text = f"Sluchaj, Ty slyszales co Ci powiedzialem czy nie slyszales?\nDobra, to nie szukam {self.search_prod}"
                self.reset_present_search()
                return stmt

            stmt.text = f"{random_answer(search_prompt_no_context_list)} {self.search_prod}?"
            return stmt

        if "kategori" in msg:
            for ask in category_ask_list:
                if ask in msg:
                    self.search_category = "all"
                    stmt.text = random_answer(show_all_categories_list)
                    return stmt

            if self.process_category(msg):
                stmt.text = f"Wybrales kategorie {self.search_category}, co dalej?"
            else:
                stmt.text = f"Nieznana kategoria {self.search_category}!"
                self.search_category = None
            return stmt

        if self.search_category is "all":
            for ack in ack_list:
                if ack in msg:
                    self.search_category = None
                    stmt.text = "\tKategorie:"
                    for cat in self.categories.keys():
                        stmt.text = f"{stmt.text}\n{cat}"
                    return stmt

        self.reset_present_search()
        stmt = BestMatch.process(self, input_statement=input)
        return stmt


        




                

        
            

