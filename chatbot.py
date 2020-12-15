from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

if __name__ == "__main__":
    chatbot = ChatBot(
        name = "MyBot",
        logic_adapters = [{
            "import_path" : "allegroAdapter.AllegroAdapter",
            "statement_comparision_function" : "chatterbot.comparisions.levenshtein_distance",
            "default_response" : "Nie rozumiem co do mnie powiedziales :c"
        }]
    )

    trainer = ChatterBotCorpusTrainer(chatbot)
    chatbot.storage.drop()
    trainer.train("polish")
    
    print("Gotowy do rozmowy!")
    work = True
    while(work):
        user_line = input("> ")
        reply = chatbot.get_response(user_line)
        if "Papa!" == reply.text:
            work = False
        print("AllegroBot:",reply)