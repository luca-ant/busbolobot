import os
import logging
token = os.environ['BUS_BOT_TOKEN']

emo_clock = u'\U0001F552'
emo_sat = u'\U0001F6F0'
emo_ita = u'\U0001F1EE'u'\U0001F1F9'
emo_eng = u'\U0001F1EC'u'\U0001F1E7'
emo_bus = u'\U0001F68C'
emo_money = u'\U0001F4B5'
emo_notify = u'\U0001F514'
emo_stop = u'\U0001F6D1'
emo_fav = u'\U00002B50'
emo_arrow_back = u'\U00002B05'
emo_double_arrow_back = u'\U000023EA'
emo_arrow_forward = u'\U000027A1'
emo_double_arrow_forward = u'\U000023E9'
emo_back = u'\U0001F519'
emo_cross = u'\U0000274C'
emo_help = u'\U00002139'
emo_confused = u'\U0001F615'
emo_privacy = u'\U0001F50F'
emo_pin = u'\U0001F4CC'
emo_gps = u'\U0001F4CD'


donation_string = emo_ita + " Ti piace questo bot? Se vuoi sostenerlo puoi fare una donazione qui! -> https://www.paypal.me/lucaant\n\n" + \
    emo_eng + " Do you like this bot? If you want to support it you can make a donation here -> https://www.paypal.me/lucaant"

help_string = emo_help + " <b>HELP</b>\n\n"+emo_ita + " ITALIANO\n" + "Invia\n\"NUMERO_FERMATA\"\noppure\n\"NUMERO_FERMATA LINEA\"\noppure\n\"NUMERO_FERMATA LINEA ORA\" \noppure\nla tua posizione per ricevere l'elenco delle fermate vicine e poi scegli la fermata e la linea che ti interessa dalla tastiera sotto.\n<i>Esempi:</i>\n<code>4004</code>\n<code>4004 27</code>\n<code>4004 27 0810</code>\n\n<b>Puoi anche aggiungere le fermate che usi più spesso ai preferiti per averle sempre a portata di mano!</b>\n\nPer problemi e malfunzionamenti inviare una mail a luca.antognetti5@gmail.com descrivendo dettagliatamente il problema.\n\n" + \
    emo_eng + " ENGLISH\n" + "Send\n\"STOP_NUMBER\"\nor\n\"STOP_NUMBER LINE\"\nor\n\"STOP_NUMBER LINE TIME\"\nor\nyour location to get the list of nearby stops and then choose one from keyboard below.\n<i>Examples:</i>\n<code>4004</code>\n<code>4004 27</code>\n<code>4004 27 0810</code>\n\n<b>You can also add the stops you use most often to your favourites to always have them at hand!</b>\n\nFor issues send a mail to luca.antognetti5@gmail.com describing the problem in detail."
privacy_string = "<b>In order to provide you the service, this bot collects user data like yours recent stops and lines. When you send a location, it is also logged.\nUsing this bot you allow your data to be saved.</b>"

url = "https://hellobuswsweb.tper.it/web-services/hello-bus.asmx/QueryHellobus"


working_dir = os.path.dirname(os.path.abspath(__file__))+"/"

data_dir = working_dir+"busbolobot_data/"
xml_stops_file = data_dir+"lineefermate.xml"
favourites_dir = data_dir+"favourites/"
download_dir = working_dir+"download/"
logging.basicConfig(filename=working_dir+"busbolobot.log", level=logging.INFO)



