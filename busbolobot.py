import os
import csv
import collections
import sys
import math
import time
import logging
import traceback
import xml.etree.ElementTree as ET
from pydub import AudioSegment
import speech_recognition as sr
import requests
import threading
import telepot
from datetime import datetime
from collections import defaultdict
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from threading import Lock, Thread


with open(sys.argv[1]) as f:
    token = f.read().strip()
f.close()

bot = telepot.Bot(token)

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


donation_string = emo_ita + " Ti piace questo bot? Se vuoi sostenerlo puoi fare una donazione qui! -> https://www.paypal.me/lucaant\n\n" + \
    emo_eng + " Do you like this bot? If you want to support it you can make a donation here -> https://www.paypal.me/lucaant"

help_string = emo_help + " <b>HELP</b>\n\n"+emo_ita + " ITALIANO\n" + "Invia\n\"NUMERO_FERMATA\"\noppure\n\"NUMERO_FERMATA LINEA\"\noppure\n\"NUMERO_FERMATA LINEA ORA\" \noppure\nla tua posizione per ricevere l'elenco delle fermate vicine e poi scegli la fermata e la linea che ti interessa dalla tastiera sotto.\n<i>Esempi:</i>\n<code>4004</code>\n<code>4004 27</code>\n<code>4004 27 0810</code>\n\n<b>Puoi anche aggiungere le fermate che usi più spesso ai preferiti per averle sempre a portata di mano!</b>\n\nPer problemi e malfunzionamenti inviare una mail a luca.ant96@libero.it descrivendo dettagliatamente il problema.\n\n" + \
    emo_eng + " ENGLISH\n" + "Send\n\"STOP_NUMBER\"\nor\n\"STOP_NUMBER LINE\"\nor\n\"STOP_NUMBER LINE TIME\"\nor\nyour location to get the list of nearby stops and then choose one from keyboard below.\n<i>Examples:</i>\n<code>4004</code>\n<code>4004 27</code>\n<code>4004 27 0810</code>\n\n<b>You can also add the stops you use most often to your favourites to always have them at hand!</b>\n\nFor issues send a mail to luca.ant96@libero.it describing the problem in detail."
privacy_string = "<b>In order to provide you the service, this bot collects user data like yours recent stops and lines. When you send a location, it is also logged.\nUsing this bot you allow your data to be saved.</b>"

url = "https://hellobuswsweb.tper.it/web-services/hello-bus.asmx/QueryHellobus"

file_xml_fermate = "lineefermate_20190511.xml"
favourite_filename = "favourite.csv"
logging.basicConfig(filename="busbolobot.log", level=logging.INFO)

writer_lock = Lock()
audio_recognizer = sr.Recognizer()

tree = ET.parse(file_xml_fermate)
xml_root = tree.getroot()

dict_user_favourites = collections.defaultdict(list)
dirty_bit_favourites_list = collections.defaultdict()
notify_threads = collections.defaultdict()
audio_file = "/tmp/audio_temp"


def makeInlineStopKeyboard(params, time):
    try:
        stop = params[0].strip()
    except:
        stop = ""
    try:
        line = " " + params[1].strip()
    except:
        line = ""

    s = (stop + line).strip()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=emo_stop + ' STOP!',
                              callback_data="stop " + s)],
        [InlineKeyboardButton(text=emo_notify + ' RESTART for 5 min',
                              callback_data="notify " + s + " 5")],
        [InlineKeyboardButton(text=emo_notify + ' RESTART for 10 min',
                              callback_data="notify " + s + " 10")]

    ])
    return keyboard


def makeInlineTrackKeyboard(chat_id, params):
    try:
        stop = params[0].strip()
    except:
        stop = ""
    try:
        line = " " + params[1].strip()
    except:
        line = ""
    s = (stop + line).strip()
    if s.strip() in dict_user_favourites[chat_id]:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=emo_cross + ' REMOVE "' + s + '" FROM FAVOURITES',
                                  callback_data="remove " + s)],
            [InlineKeyboardButton(text=emo_notify + ' NOTIFY for 5 min',
                                  callback_data="notify " + s + " 5")],
            [InlineKeyboardButton(text=emo_notify + ' NOTIFY for 10 min',
                                  callback_data="notify " + s + " 10")],
            [InlineKeyboardButton(text=emo_notify + ' NOTIFY for 15 min',
                                  callback_data="notify " + s + " 15")]
        ])

    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=emo_fav + ' ADD "' + s + '" TO FAVOURITES',
                                  callback_data="add " + s)],
            [InlineKeyboardButton(text=emo_notify + ' NOTIFY for 5 min',
                                  callback_data="notify " + s + " 5")],
            [InlineKeyboardButton(text=emo_notify + ' NOTIFY for 10 min',
                                  callback_data="notify " + s + " 10")],
            [InlineKeyboardButton(text=emo_notify + ' NOTIFY for 15 min',
                                  callback_data="notify " + s + " 15")]
        ])
    return keyboard


class TrackThread(Thread):
    def __init__(self, time_notify, bot, msg, stop, line, first_msg):

        Thread.__init__(self)
        query_id, from_id, query_data = telepot.glance(
            msg, flavor='callback_query')
        self.chat_id = from_id
        self.msg_id = msg['message']['message_id']
        self.stop = stop.strip()
        self.line = line.strip()
        self.stop_flag = False
        self.count = time_notify
        self.bot = bot
        self.last_message = first_msg
        self.keyboard = makeInlineStopKeyboard((stop, line), time_notify)

    def run(self):
        while (self.count > 0):
            try:
                self.count = self.count - 1
                time.sleep(60)
                if self.stop_flag:
                    break
                output_string = getStopInfo((self.stop, self.line))
                self.last_message = output_string
                self.bot.deleteMessage((self.chat_id, self.msg_id))
                new_msg = self.bot.sendMessage(
                    self.chat_id, output_string, parse_mode='HTML', reply_markup=self.keyboard)
                self.msg_id = new_msg["message_id"]

            #                self.bot.editMessageText(self.msg_edited, output_string,parse_mode='HTML', reply_markup=self.keyboard)

            except Exception as e:
                traceback.print_exc()

        if self.stop_flag:
            try:
                now = datetime.now()
                logging.info(
                    "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### CHAT_ID = " + str(self.chat_id) + " ### TRACKING STOP for " + self.stop + " " + self.line)

                print(str(self.chat_id) + " stop " +
                      str(self.stop) + " " + str(self.line))
                self.bot.editMessageText((self.chat_id, self.msg_id), self.last_message, parse_mode='HTML',
                                         reply_markup=makeInlineTrackKeyboard(self.chat_id, (self.stop, self.line)))
            except telepot.exception.TelegramError:
                traceback.print_exc()
                pass
            except Exception as e:
                traceback.print_exc()
        else:
            #    self.bot.sendMessage(self.chat_id,  parse_mode='HTML',"TRACKING ENDED!")
            now = datetime.now()
            logging.info(
                "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### CHAT_ID = " + str(self.chat_id) + " ### TRACKING END for " + self.stop + " " + self.line)

            try:
                print(str(self.chat_id) + " end " +
                      str(self.stop) + " " + str(self.line))
                self.bot.editMessageText((self.chat_id, self.msg_id), self.last_message + "\n<b>TRACKING ENDED!</b>", parse_mode='HTML',
                                         reply_markup=makeInlineTrackKeyboard(self.chat_id, (self.stop, self.line)))
            except Exception as e:
                traceback.print_exc()

    def set_stop_flag(self, b):
        self.stop_flag = b


def restoreFavourites():
    if os.path.isfile(favourite_filename):
        try:
            with open(favourite_filename) as f:
                csv_reader = csv.reader(f, delimiter=':')
                for row in csv_reader:
                    chat_id = int(row[0].replace("'", " ").strip())
                    fav = row[1:9]
                    dict_user_favourites[chat_id] = fav

        except Exception as e:
            traceback.print_exc()


def addFav(chat_id, req):
    dirty_bit_favourites_list[chat_id] = 0
    if req not in dict_user_favourites[chat_id] and req.replace(" ", "").isdigit():
        dirty_bit_favourites_list[chat_id] = 1
        if len(dict_user_favourites[chat_id]) >= 10:
            dict_user_favourites[chat_id].pop(0)
        dict_user_favourites[chat_id].append(req.strip())
    storeFavourites()


def rmFav(chat_id, line_stop):
    if line_stop.strip() in dict_user_favourites[chat_id]:
        dirty_bit_favourites_list[chat_id] = 1
        dict_user_favourites[chat_id].remove(line_stop.strip())

    storeFavourites()


def storeFavourites():
    writer_lock.acquire()
    dirty = False
    for key in dirty_bit_favourites_list.keys():
        if dirty_bit_favourites_list[key] == 1:
            dirty = True
            break

    if dirty:
        try:
            with open(favourite_filename, 'w') as f:
                for key in dict_user_favourites.keys():
                    f.write(str(key) + ":")
                    f.write(":".join(dict_user_favourites[key]) + "\n")

        except Exception as e:
            traceback.print_exc()
    writer_lock.release()


def distance(lat_user, lon_user, lat_stop, lon_stop):
    r = 6372.795477598

    radLatA = math.pi * lat_user / 180
    radLonA = math.pi * lon_user / 180
    radLatB = math.pi * lat_stop / 180
    radLonB = math.pi * lon_stop / 180

    phi = abs(radLonA - radLonB)

    p = math.acos((math.sin(radLatA) * math.sin(radLatB)) +
                  (math.cos(radLatA) * math.cos(radLatB) * math.cos(phi)))

    distance = p * r * 1000
    return distance


def getStopName(stop):

    for child in xml_root:
        id_fermata = child[1].text

        if id_fermata == stop:
            name = child[2].text
            break
    else:
        name = ""

    return name


def makeLocationKeyboard(stringKeyboardList):

    row = int(len(stringKeyboardList) / 3) + 2
    cols = 3

    buttonLists = list()
    for i in range(row):
        buttonLists.append(list())

    i = 0
    index = 0
    for str in stringKeyboardList:
        buttonLists[index].append(str)
        i += 1
        if i % cols == 0:
            index = index + 1
    buttonLists[row - 1].append(emo_back + " BACK TO MAIN")
    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)

    return keyboard


def makeFavouritesKeyboard(chat_id):

    row = 6
    cols = 2

    buttonLists = list()
    for i in range(row):
        buttonLists.append(list())

    index = 0
    for i in range(len(dict_user_favourites[chat_id])):
        name = getStopName(dict_user_favourites[chat_id][i].split()[0])
        buttonLists[index].append(
            dict_user_favourites[chat_id][i] + " - " + name)
        if i % cols != 0:
            index += 1


#    buttonLists = list()
#    for i in range(4):
#        buttonLists.append(list())

#    if len(dict_user_favourites[chat_id]) > 6:
#        buttonLists[0] = dict_user_favourites[chat_id][:3]
#        buttonLists[1] = dict_user_favourites[chat_id][3:6]
#        buttonLists[2] = dict_user_favourites[chat_id][6:]
#    elif len(dict_user_favourites[chat_id]) > 3:
#        buttonLists[0] = dict_user_favourites[chat_id][:3]
#        buttonLists[1] = dict_user_favourites[chat_id][3:]
#    else:
#        buttonLists[0] = dict_user_favourites[chat_id]

    buttonLists[5].append(emo_back + " BACK TO MAIN")

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def makeMainKeyboard(chat_id):

    buttonLists = list()

    for i in range(3):
        buttonLists.append(list())
    buttonLists[0].append(emo_fav+" FAVOURITES")

    buttonLists[1].append(emo_help+" HELP")
    buttonLists[2].append(emo_privacy+" PRIVACY POLICY")
    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def parseResponse(stop, line, text):
    try:
        name = getStopName(stop)
        nextArr = text.split(sep=",")
        first = nextArr[0][14:].strip()
        firstInfo = first.split()
        result = list()
        result.append(emo_bus + " [<b>" + firstInfo[0] + "</b>] ")

        if firstInfo[1] == "DaSatellite":
            result.append(emo_sat + " DA SATELLITE ")
        else:
            result.append(emo_clock + " DA ORARIO ")

        tdiff = datetime.strptime(
            firstInfo[2], '%H:%M') - datetime.strptime(time.strftime('%H:%M'), '%H:%M')

        result.append("tra <b>" + repr(int(tdiff.seconds / 60)) +
                      " minuto/i </b>(" + firstInfo[2] + ")")

        if len(nextArr) > 1:
            second = nextArr[1].strip()
            secondInfo = second.split()

            result.append("\n" + emo_bus + " [<b>" + secondInfo[0] + "</b>] ")

            if secondInfo[1] == "DaSatellite":
                result.append(emo_sat + " DA SATELLITE ")
            else:
                result.append(emo_clock + " DA ORARIO ")

            tdiff = datetime.strptime(
                secondInfo[2], '%H:%M') - datetime.strptime(time.strftime('%H:%M'), '%H:%M')
            result.append("tra <b>" + repr(int(tdiff.seconds / 60)
                                           ) + " minuto/i </b>(" + secondInfo[2] + ")")

        result.append("\n")
        result.append(emo_ita)
        if (line != ""):
            result.append(" Linea: <b>" + line + "</b>")

        result.append(" Fermata: <b>" + stop +
                      "</b> " + "<i>("+name+")</i>\n")
        result.append(emo_eng)
        if (line != ""):
            result.append(" Line: <b>" + line + "</b>")

        result.append(" Stop: <b>" + stop +
                      "</b> " + "<i>("+name+")</i>\n")

        return "".join(result)
    except:
        traceback.print_exc()
        return text


def makeNearbyOutput(lat_user, lon_user):
    result = collections.defaultdict()
    busLines = collections.defaultdict(list)
    output = list()
    stringKeyboardList = list()
    output.append(emo_ita + " FERMATE VICINE\n" +
                  emo_eng + " NEARBY STOPS\n\n")
    for child in xml_root:
        linea = child[0].text
        id_fermata = child[1].text
        nome_fermata = child[2].text
        lat_fermata = child[7].text
        lon_fermata = child[8].text

        dist = distance(float(lat_user), float(lon_user),
                        float(lat_fermata), float(lon_fermata))
        if (dist < 25):

            element = id_fermata + " - " + nome_fermata + \
                " (" + repr(int(dist)) + " m)"
            busLines[element].append(linea)
            stringKeyboardList.append(id_fermata + " " + linea)
            if id_fermata not in stringKeyboardList:
                stringKeyboardList.append(id_fermata)

    for s in busLines.keys():
        output.append(s)
        output.append("\n")
        output.append("Linee: ")
        for n in busLines[s]:
            output.append(n + " ")
        output.append("\n\n")

    stringKeyboardList.sort()
    result["stringKeyboardList"] = stringKeyboardList
    result["output_string"] = "".join(output)
    return result


def makeReq(stop, line, time):
    body = "fermata=" + stop + "&linea=" + line + "&oraHHMM=" + time
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(url=url, data=body, headers=headers)

    root = ET.fromstring(response.text)

    return parseResponse(stop, line, root.text)


def getStopInfo(params):
    if len(params) >= 3:
        return makeReq(params[0], params[1], params[2])
    elif len(params) == 2:
        return makeReq(params[0], params[1], "")
    elif len(params) == 1:
        return makeReq(params[0], "", "")
    else:
        return "error"


def getStopLocation(stop):
    if stop == "":
        return ("LAT not found", "LON not found")

    for child in xml_root:
        id_fermata = child[1].text

        if id_fermata == stop:
            lat_fermata = child[7].text
            lon_fermata = child[8].text
            return (lat_fermata, lon_fermata)
    return ("LAT not found", "LON not found")


def on_callback_query(msg):
    try:
        query_id, from_id, query_data = telepot.glance(
            msg, flavor='callback_query')
        msg_edited = (from_id, msg['message']['message_id'])
        print(from_id, query_data)
        if (query_data.startswith("notify")):
            array = query_data.split()
            if len(array) == 3:
                stop = array[1]
                line = ""
                t = int(array[2])
            elif len(array) == 4:
                stop = array[1]
                line = array[2]
                t = int(array[3])
            else:
                stop = ""
                line = ""
                t = 0
            output_string = getStopInfo((stop, line))

            now = datetime.now()
            logging.info(
                "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### CHAT_ID = " + str(from_id) + " ### TRACKING START " + stop + " " + line + " for " + str(
                    t) + " min")

            thread = TrackThread(t, bot, msg, stop, line, output_string)

            try:
                notify_threads[from_id].set_stop_flag(True)
            except:
                pass

            notify_threads[from_id] = thread
            thread.start()

            try:
                #        bot.sendMessage(from_id,  parse_mode='HTML',"TRACKING STARTED!")
                bot.editMessageText(
                    msg_edited, output_string, parse_mode='HTML', reply_markup=makeInlineStopKeyboard((stop, line), t))
            except telepot.exception.TelegramError:
                bot.answerCallbackQuery(query_id, text="SLOW DOWN!!")

            except Exception as e:
                traceback.print_exc()

            bot.answerCallbackQuery(query_id, text="TRACKING STARTED!")

        elif (query_data.startswith("stop")):
            array = query_data.split()
            if len(array) == 2:
                stop = array[1].strip()
                line = ""
            elif len(array) == 3:
                stop = array[1].strip()
                line = array[2].strip()
            else:
                stop = ""
                line = ""

            try:
                notify_threads[from_id].set_stop_flag(True)
            except:
                pass

            output_string = getStopInfo((stop, line))
            output_string += "\n<b>TRACKING STOPPED!</b>"
            bot.answerCallbackQuery(query_id, text="TRACKING STOPPED!")

            try:
                bot.editMessageText(msg_edited, output_string, parse_mode='HTML',
                                    reply_markup=makeInlineTrackKeyboard(from_id, (stop, line)))
            except telepot.exception.TelegramError:
                pass

        elif (query_data.startswith("add")):
            array = query_data.split()
            if len(array) == 2:
                stop = array[1].strip()
                line = ""
            elif len(array) == 3:
                stop = array[1].strip()
                line = array[2].strip()
            else:
                stop = ""
                line = ""

            fav = stop+" "+line
            fav = fav.strip()
            if fav not in dict_user_favourites[from_id]:
                addFav(from_id, stop+" "+line)

                output_string = "<b>" + stop + " " + line+" WAS ADDED TO YOUR FAVOURITES</b>"

                bot.sendMessage(from_id, output_string, parse_mode='HTML',
                                reply_markup=makeFavouritesKeyboard(from_id))
                output_string = getStopInfo((stop, line))

                bot.sendMessage(from_id, output_string, parse_mode='HTML',
                                reply_markup=makeInlineTrackKeyboard(from_id, (stop, line)))
            else:
                output_string = "<b>" + stop + " " + line + \
                    " ALREADY IN YOUR FAVOURITES</b>"

                bot.sendMessage(from_id, output_string, parse_mode='HTML',
                                reply_markup=makeFavouritesKeyboard(from_id))

        elif (query_data.startswith("remove")):
            array = query_data.split()
            if len(array) == 2:
                stop = array[1].strip()
                line = ""
                params = (stop,)
            elif len(array) == 3:
                stop = array[1].strip()
                line = array[2].strip()
                params = (stop, line)
            else:
                stop = ""
                line = ""

            fav = stop+" "+line
            fav = fav.strip()
            if fav in dict_user_favourites[from_id]:

                rmFav(from_id, stop+" "+line)

                output_string = "<b>" + stop + " " + line + \
                    " WAS REMOVED FROM YOUR FAVOURITES</b>"

                bot.sendMessage(from_id, output_string, parse_mode='HTML',
                                reply_markup=makeFavouritesKeyboard(from_id))
            else:
                output_string = "<b>" + stop + " " + line + \
                    " NOT IN YOUR FAVOURITES</b>"

                bot.sendMessage(from_id, output_string, parse_mode='HTML',
                                reply_markup=makeFavouritesKeyboard(from_id))

    except telepot.exception.TelegramError:
        bot.answerCallbackQuery(query_id, text="SLOW DOWN!!")
        traceback.print_exc()

    except Exception as e:
        traceback.print_exc()


def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    msg.pop("chat", None)
    msg.pop("from", None)
    print(msg)
    now = datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id) + " = " + str(msg))

    try:
        if content_type == "text":
            if msg["text"] == "/start":

                output_string = emo_bus + " TPER HelloBus on Telegram! " + \
                    emo_bus + "\n\n" + help_string
                bot.sendMessage(
                    chat_id, output_string, parse_mode='HTML', reply_markup=makeFavouritesKeyboard(chat_id))
            elif msg["text"] == "/help":

                bot.sendMessage(chat_id, help_string, parse_mode='HTML',
                                reply_markup=makeMainKeyboard(chat_id))

            elif msg["text"] == emo_help+" HELP":

                bot.sendMessage(chat_id, help_string, parse_mode='HTML',
                                reply_markup=makeMainKeyboard(chat_id))

            elif msg["text"] == emo_privacy+" PRIVACY POLICY":

                bot.sendMessage(chat_id, privacy_string, parse_mode='HTML',
                                reply_markup=makeMainKeyboard(chat_id))
            elif msg["text"] == emo_fav+" FAVOURITES":

                output_string = msg["text"]
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=makeFavouritesKeyboard(chat_id))
            elif msg["text"] == emo_back + " BACK TO MAIN":
                output_string = msg["text"]
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=makeMainKeyboard(chat_id))

            else:
                if "-" in msg["text"]:
                    mess = msg["text"].split("-")
                    mess = ''.join(mess[0].strip())

                else:
                    mess = msg["text"]

                stop = mess.split()[0]

                params = mess.split()
                output_string = getStopInfo(params)
                # addFav(chat_id, mess)
                if "<b>help</b>" in output_string.lower() or "hellobushelp" in output_string.lower():
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=makeMainKeyboard(chat_id))
                else:
                    bot.sendMessage(chat_id, donation_string,
                                    parse_mode='HTML')
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=makeInlineTrackKeyboard(chat_id, params))

        elif content_type == "location":

            lat_user = msg["location"]["latitude"]
            lon_user = msg["location"]["longitude"]

            output = makeNearbyOutput(lat_user, lon_user)
            bot.sendMessage(chat_id, donation_string, parse_mode='HTML')

            bot.sendMessage(chat_id, output["output_string"], parse_mode='HTML',
                            reply_markup=makeLocationKeyboard(output["stringKeyboardList"]))

        elif content_type == "voice":

            bot.download_file(msg["voice"]["file_id"], audio_file + ".ogg")
            audio_ogg = AudioSegment.from_ogg(audio_file + ".ogg")
            audio_ogg.export(audio_file + ".wav", format="wav")

            with sr.AudioFile(audio_file + ".wav") as source:
                audio = audio_recognizer.record(source)

            try:
                string_from_audio = audio_recognizer.recognize_google(
                    audio, language="it-IT")
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
                string_from_audio = ""
            except sr.RequestError as e:
                string_from_audio = ""
                print(
                    "Could not request results from Google Speech Recognition service; {0}".format(e))

            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                         " ### AUDIO TEXT from " + str(chat_id) + " = " + string_from_audio)
            try:
                stop = string_from_audio.split()[0]
            except:
                stop = ""

            params = string_from_audio.split()
            output_string = getStopInfo(params)
            if output_string == "error":
                output_string = emo_ita + " Parla chiaro! Pronuncia\n\"NUMERO_FERMATA\"\noppure\n\"NUMERO_FERMATA LINEA\"\n" + \
                    emo_eng + " Speak clearly! Say \n\"STOP_NUMBER\"\nor\n\"STOP_NUMBER LINE\""
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=makeMainKeyboard(chat_id))
            else:

                # addFav(chat_id, string_from_audio)
                bot.sendMessage(chat_id, donation_string, parse_mode='HTML',
                                reply_markup=makeMainKeyboard(chat_id))
                bot.sendMessage(chat_id, "AUDIO TEXT: \"" +
                                string_from_audio + "\"", parse_mode='HTML')
                if "<b>help</b>" in output_string.lower() or "hellobushelp" in output_string.lower():
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=makeMainKeyboard(chat_id))
                else:
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=makeInlineTrackKeyboard(chat_id, params))

        else:

            output_string = emo_ita + " Non ho capito... Invia un messaggio o la tua posizione!\n" + \
                emo_eng + " I don't understand... Send a message or your location"
            bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                            reply_markup=makeMainKeyboard(chat_id))

    except Exception as e:
        traceback.print_exc()
        output_string = emo_ita + " Non ho capito... Invia un messaggio o la tua posizione!\n" + \
            emo_eng + " I don't understand... Send a message or your location"
        bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                        reply_markup=makeMainKeyboard(chat_id))


restoreFavourites()
MessageLoop(bot, {'chat': on_chat_message,
                  'callback_query': on_callback_query}).run_as_thread()

print('Listening ...')
# Keep the program running.
while 1:
    time.sleep(10)
