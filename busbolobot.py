import os
import csv
import collections
import sys
import math
import time
import logging
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


def makeInlineTrackKeyboard(params):
    try:
        stop = params[0]
    except:
        stop = ""
    try:
        line = params[1]
    except:
        line=""


    keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [dict(text='TRACK', callback_data="track "+ stop + " " + line)
            ]])        
    return keyboard




class TrackThread(Thread):
    def __init__(self, bot, msg, stop, line, first_msg ):
 
        Thread.__init__(self)
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        self.chat_id = from_id 
        self.msg_id = msg['message']['message_id']     
        self.stop = stop
        self.line = line
        self.stop_flag = False
        self.count = 10
        self.bot = bot
        self.last_message = first_msg
        self.keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [dict(text='STOP', callback_data="stop "+ stop + " " + line)]
        ])

    def run(self):
        while(self.count > 0):
            try:
                self.count = self.count - 1
                time.sleep(60)
                if self.stop_flag:
                    break
                output_string = getStopInfo((self.stop,self.line))
                self.last_message = output_string
                self.bot.deleteMessage((self.chat_id,self.msg_id))
                new_msg = self.bot.sendMessage(self.chat_id, output_string, reply_markup=self.keyboard)
                self.msg_id = new_msg["message_id"]

#                self.bot.editMessageText(self.msg_edited, output_string, reply_markup=self.keyboard)

            except Exception as e:
                print(repr(e))

        if self.stop_flag:  
            try:
                now = datetime.now()
                logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### CHAT_ID = "+ str(self.chat_id) +  " ### TRACKING STOP for " + self.stop + " " + self.line)
                logging.info("-"*50)
                print(str(self.chat_id) + " stop " + str(self.stop) + " " + str(self.line))
                #self.bot.editMessageText((self.chat_id, self.msg_id), self.last_message + "\n\nTRACKING STOPPED!" , reply_markup=makeInlineTrackKeyboard((self.stop, self.line)))
                self.bot.editMessageText((self.chat_id, self.msg_id), self.last_message , reply_markup=makeInlineTrackKeyboard((self.stop, self.line)))
            except Exception as e:
                print(repr(e))
        else:
        #    self.bot.sendMessage(self.chat_id, "TRACKING ENDED!")
            now = datetime.now()
            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### CHAT_ID = "+ str(self.chat_id) +  " ### TRACKING END for " + self.stop + " " + self.line)
            logging.info("-"*50)
            try:
                print(str(self.chat_id) + " end " + str(self.stop) + " " + str(self.line))
                self.bot.editMessageText((self.chat_id, self.msg_id), self.last_message + "\n\nTRACKING ENDED!" , reply_markup=makeInlineTrackKeyboard((self.stop, self.line)))
                #self.bot.editMessageText((self.chat_id, self.msg_id), self.last_message, reply_markup=makeInlineTrackKeyboard((self.stop, self.line)))
            except Exception as e:
                print(repr(e))


    def set_stop_flag(self, b):
        self.stop_flag = b


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


donation_string = emo_ita + " Ti piace questo bot? Se vuoi sostenerlo puoi fare una donazione qui! -> https://www.paypal.me/lucaant\n\n"+emo_eng + " Do you like this bot? If you want to support it you can make a donation here -> https://www.paypal.me/lucaant"

help_string = emo_ita + " ITALIANO\n"+ "Invia\n\"NUMERO_FERMATA\"\noppure\n\"NUMERO_FERMATA LINEA\"\noppure\n\"NUMERO_FERMATA LINEA ORA\" \noppure\nla tua posizione per ricevere l'elenco delle fermate vicine e poi scegli la fermata e la linea che ti interessa dalla tastiera sotto.\n\nPer problemi e malfunzionamenti inviare una mail a luca.ant96@libero.it descrivendo dettagliatamente il problema.\n\n"+ emo_eng + " ENGLISH\n"+"Send\n\"STOP_NUMBER\"\nor\n\"STOP_NUMBER LINE\"\nor\n\"STOP_NUMBER LINE TIME\"\nor\nyour location to get the list of nearby stops and then choose one from keyboard below.\n\nFor issues send a mail to luca.ant96@libero.it describing the problem in detail." 

url = "https://hellobuswsweb.tper.it/web-services/hello-bus.asmx/QueryHellobus"

file_xml_fermate = "lineefermate_20190511.xml"
favourite_filename = "favourite.csv"
logging.basicConfig(filename="busbolobot.log", level=logging.INFO)

#file_xml_fermate = "/bot/busbolobot/lineefermate_20190511.xml"
#favourite_filename = "/bot/busbolobot/favourite.csv"
#logging.basicConfig(filename="/bot/busbolobot/busbolobot.log", level=logging.INFO)


writer_lock = Lock()
audio_recognizer = sr.Recognizer()

tree = ET.parse(file_xml_fermate)
xml_root = tree.getroot()

dict_user_favourites = collections.defaultdict(list)
dirty_bit_favourites_list = collections.defaultdict()
track_threads = collections.defaultdict()
audio_file = "/tmp/audio_temp"

def restoreFavourites():
    if os.path.isfile(favourite_filename):
        try:
            with open(favourite_filename) as f:
                csv_reader = csv.reader(f, delimiter=':')
                for row in csv_reader:
                    chat_id = int(row[0].replace("'"," ").strip())
                    fav = row[1:]
                    dict_user_favourites[chat_id] = fav
                    
        except Exception as e:
            print(repr(e))


def addLastReq(chat_id, req):
    dirty_bit_favourites_list[chat_id] = 0
    if req not in dict_user_favourites[chat_id] and req.replace(" ", "").isdigit():
        dirty_bit_favourites_list[chat_id] = 1
        if len(dict_user_favourites[chat_id]) >= 9:
            dict_user_favourites[chat_id].pop(0)
        dict_user_favourites[chat_id].append(req.strip())
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
            print(repr(e))
    writer_lock.release()



def distance(lat_user, lon_user, lat_stop, lon_stop):
    r = 6372.795477598

    radLatA = math.pi * lat_user / 180
    radLonA = math.pi * lon_user / 180
    radLatB = math.pi * lat_stop / 180
    radLonB = math.pi * lon_stop / 180

    phi = abs(radLonA - radLonB)

    p = math.acos( (math.sin(radLatA) * math.sin(radLatB)) + (math.cos(radLatA) * math.cos(radLatB) * math.cos(phi)) )

    distance = p * r *1000
    return distance

def makeLocationKeyboard(stringKeyboardList):

    buttonLists = list()

    for i in range(0, int(len(stringKeyboardList)/3)+1, 1):
       buttonLists.append(list())
    i = 0
    index = 0
    for str in stringKeyboardList:
        buttonLists[index].append(str)
        i += 1
        if i % 3 == 0:
            index = index + 1

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)

    return keyboard

def makeRecentKeyboard(chat_id):

    buttonLists = list()
    for i in range(0, int(len(dict_user_favourites[chat_id])/3)+1, 1):
        buttonLists.append(list())
    
    if len(dict_user_favourites[chat_id]) > 6:
        buttonLists[0] = dict_user_favourites[chat_id][:3]
        buttonLists[1] = dict_user_favourites[chat_id][3:6]
        buttonLists[2] = dict_user_favourites[chat_id][6:]
    elif len(dict_user_favourites[chat_id]) > 3:
        buttonLists[0] = dict_user_favourites[chat_id][:3]
        buttonLists[1] = dict_user_favourites[chat_id][3:]
    else:
        buttonLists[0] = dict_user_favourites[chat_id]
    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists,resize_keyboard=True)
    return keyboard 

def parseResponse(stop, line, text):
    try:
        nextArr = text.split(sep=",")
        first = nextArr[0][14:].strip()
        firstInfo = first.split() 
        result = list()
        result.append(emo_ita + " Fermata: "+ stop)
        if(line != ""):
            result.append(" Linea: "+ line + "\n") 
        else:
            result.append("\n")
        result.append(emo_eng + " Stop: "+ stop ) 
        if(line != ""):
            result.append(" Line: "+ line + "\n") 
        else:
            result.append("\n")
        result.append("\n")
        result.append(emo_bus+ " ["+firstInfo[0]+"] " )
        
        if firstInfo[1] == "DaSatellite":
            result.append(emo_sat + " DA SATELLITE ")
        else:
            result.append(emo_clock+ " DA ORARIO ")
        
        tdiff = datetime.strptime(firstInfo[2],'%H:%M') - datetime.strptime(time.strftime('%H:%M'), '%H:%M')

        result.append("tra " + repr(int(tdiff.seconds/60)) + " minuto/i ("+ firstInfo[2] +")")
       
        if len(nextArr)>1:
            second = nextArr[1].strip()
            secondInfo = second.split() 
            
            result.append("\n"+emo_bus+ " ["+secondInfo[0]+"] ")
            
            if secondInfo[1] == "DaSatellite":
                result.append(emo_sat + " DA SATELLITE ")
            else:
                result.append(emo_clock+ " DA ORARIO ")
            
            tdiff = datetime.strptime(secondInfo[2],'%H:%M') - datetime.strptime(time.strftime('%H:%M'), '%H:%M')
            result.append("tra " + repr(int(tdiff.seconds/60)) + " minuto/i ("+ secondInfo[2] +")")

        return "".join(result)
    except:
       return text


def makeNearbyOutput(lat_user, lon_user):
    result = collections.defaultdict()
    busLines = collections.defaultdict(list)
    output = list()
    stringKeyboardList = list()
    output.append(emo_ita + " FERMATE VICINE\n" + emo_eng+" NEARBY STOPS\n\n")
    for child in xml_root:
        linea = child[0].text
        id_fermata = child[1].text
        nome_fermata = child[2].text
        lat_fermata = child[7].text
        lon_fermata = child[8].text
        
        dist = distance(float(lat_user), float(lon_user), float(lat_fermata), float(lon_fermata)) 
        if(dist < 25):
            
            element = id_fermata + " - "+ nome_fermata + " ("+ repr(int(dist)) +" m)"
            busLines[element].append(linea)
            stringKeyboardList.append(id_fermata + " "+linea)
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

    body = "fermata="+stop+"&linea="+ line +"&oraHHMM="+time
    headers = { 'Content-Type': 'application/x-www-form-urlencoded'}
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
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        msg_edited = (from_id, msg['message']['message_id'])
        print(from_id , query_data)
        if (query_data.startswith("track")):
            try:
                stop = query_data.split()[1]
            except:
                stop = ""
            try:
                line = query_data.split()[2]
            except:
                line = ""
            
            output_string = getStopInfo((stop, line))

            now = datetime.now() 
            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### CHAT_ID = "+ str(from_id) +" ### TRACKING START for " + stop + " " + line)
            logging.info("-"*50)
        
            thread = TrackThread(bot, msg, stop, line, output_string) 
            
            try:
                track_threads[from_id].set_stop_flag(True)
            except:
                pass
            track_threads[from_id] = thread 
            thread.start()
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [dict(text='STOP', callback_data="stop "+ stop + " " + line)]
            ])
            try:
        #        bot.sendMessage(from_id, "TRACKING STARTED!")
                bot.editMessageText(msg_edited, output_string , reply_markup=keyboard)
            except Exception as e:
                print(repr(e))

            bot.answerCallbackQuery(query_id,text="TRACKING STARTED!")

        if (query_data.startswith("stop")):
            
            try:
                stop = query_data.split()[1]
            except:
                stop = ""
            try:
                line = query_data.split()[2]
            except:
                line = ""
           

            try:
                track_threads[from_id].set_stop_flag(True)
            except:
                pass 
            
            bot.answerCallbackQuery(query_id,text="TRACKING STOPPED!")
        #    bot.sendMessage(from_id, "TRACKING STOPPED!")
            output_string = msg["message"]["text"]  
            #bot.editMessageText(msg_edited, output_string + "\n\nTRACKING STOPPED! ", reply_markup=makeInlineTrackKeyboard((stop,line)))
            bot.editMessageText(msg_edited, output_string , reply_markup=makeInlineTrackKeyboard((stop,line)))

    except Exception as e:
        print(repr(e))





def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(msg) 
    try:
        if content_type == "text":
            if (msg["text"] == "/start"):
                now = datetime.now()
                logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### MESSAGGIO = " + repr(msg))
                output_string = emo_bus + " TPER HelloBus on Telegram! "+ emo_bus +"\n\n"+ help_string
                bot.sendMessage(chat_id, output_string, reply_markup=ReplyKeyboardRemove())
            elif (msg["text"] == "/help"):
                now = datetime.now()
                logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### MESSAGGIO = " + repr(msg))
        
                bot.sendMessage(chat_id, donation_string)
                bot.sendMessage(chat_id, help_string, reply_markup=makeRecentKeyboard(chat_id))
            else:
                now = datetime.now()
                stop = msg["text"].split()[0]
                lat_lon = getStopLocation(stop)
                logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### LOCATION = " + lat_lon[0] + ", " + lat_lon[1]  + " ### MESSAGGIO = " + repr(msg))
                params = msg["text"].split()
                output_string = getStopInfo(params)
                addLastReq(chat_id, msg["text"])
                bot.sendMessage(chat_id, donation_string, reply_markup=makeRecentKeyboard(chat_id))
                if output_string.startswith("HellobusHelp"):
                    bot.sendMessage(chat_id, output_string)
                else:
                    bot.sendMessage(chat_id, output_string, reply_markup=makeInlineTrackKeyboard(params))

        
        elif content_type == "location":
            now = datetime.now()
            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### MESSAGGIO = " + repr(msg))
            lat_user = msg["location"]["latitude"]
            lon_user = msg["location"]["longitude"]
       
            output = makeNearbyOutput(lat_user, lon_user) 
            bot.sendMessage(chat_id, donation_string)

            bot.sendMessage(chat_id, output["output_string"], reply_markup=makeLocationKeyboard(output["stringKeyboardList"]))

        elif content_type == "voice":
            now = datetime.now()
            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### MESSAGGIO = " + repr(msg))
            bot.download_file(msg["voice"]["file_id"], audio_file+".ogg")
            audio_ogg = AudioSegment.from_ogg(audio_file+".ogg")
            audio_ogg.export(audio_file+".wav", format="wav")

            with sr.AudioFile(audio_file + ".wav") as source:
                audio = audio_recognizer.record(source)  

            try:
                string_from_audio = audio_recognizer.recognize_google(audio, language="it-IT")
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
                string_from_audio = ""
            except sr.RequestError as e:
                string_from_audio = ""
                print("Could not request results from Google Speech Recognition service; {0}".format(e))
            
            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### AUDIO TEXT = " + string_from_audio)
            try:
                stop = string_from_audio.split()[0]
            except:
                stop = ""

            lat_lon = getStopLocation(stop)
            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### LOCATION = " + lat_lon[0] + ", " + lat_lon[1] )

            params = string_from_audio.split()
            output_string = getStopInfo(params)
            if output_string == "error":
                output_string = emo_ita+ " Parla chiaro! Pronuncia\n\"NUMERO_FERMATA\"\noppure\n\"NUMERO_FERMATA LINEA\"\n"+ emo_eng +" Speak clearly! Say \n\"STOP_NUMBER\"\nor\n\"STOP_NUMBER LINE\""
                bot.sendMessage(chat_id, output_string)
            else:

                addLastReq(chat_id, string_from_audio)
                bot.sendMessage(chat_id, donation_string, reply_markup=makeRecentKeyboard(chat_id))
                bot.sendMessage(chat_id, "AUDIO TEXT: \""+ string_from_audio+ "\"")
                if output_string.startswith("HellobusHelp"):
                    bot.sendMessage(chat_id, output_string)
                else:
                    bot.sendMessage(chat_id, output_string, reply_markup=makeInlineTrackKeyboard(params))


        else:
            now = datetime.now()
            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### MESSAGGIO = " + repr(msg))
            output_string = emo_ita+ " Non ho capito... Invia un messaggio o la tua posizione!\n"+ emo_eng +" I don't understand... Send a message or your location"
            bot.sendMessage(chat_id, output_string)
        
    except Exception as e:
        print(repr(e))
        output_string = emo_ita+ " Non ho capito... Invia un messaggio o la tua posizione!\n"+ emo_eng +" I don't understand... Send a message or your location"
        bot.sendMessage(chat_id, output_string)

    logging.info("-"*50)



restoreFavourites()
MessageLoop(bot, {'chat': on_chat_message, 'callback_query': on_callback_query}).run_as_thread()



print('Listening ...')
# Keep the program running.
while 1:
    time.sleep(10)

