from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "CaliCore MDT Server je online a čeká na příkazy!"

def run():
    # Spustí webový server na portu, který Render vyžaduje
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # Přesune webový server do vedlejšího vlákna, aby neblokoval Discord bota
    t = Thread(target=run)
    t.start()
