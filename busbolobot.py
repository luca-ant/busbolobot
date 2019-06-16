import os
import csv
import collections
import sys
import math
import time
import logging
import xml.etree.ElementTree as ET
import requests
import telepot
from datetime import datetime
from collections import defaultdict
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from threading import Lock


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

tree = ET.parse(file_xml_fermate)
xml_root = tree.getroot()

dictUserFavourites = collections.defaultdict(list)
dirtyBitFavouritesList = collections.defaultdict()


def restoreFavourites():
    if os.path.isfile(favourite_filename):
        try:
            with open(favourite_filename) as f:
                csv_reader = csv.reader(f, delimiter=':')
                for row in csv_reader:
                    chat_id = int(row[0].replace("'"," ").strip())
                    fav = row[1:]
                    dictUserFavourites[chat_id] = fav
                    
        except Exception as e:
            print(repr(e))


def addLastReq(chat_id, req):
    dirtyBitFavouritesList[chat_id] = 0
    if req not in dictUserFavourites[chat_id] and req.replace(" ", "").isdigit():
        dirtyBitFavouritesList[chat_id] = 1
        if len(dictUserFavourites[chat_id]) >= 9:
            dictUserFavourites[chat_id].pop(0)
        dictUserFavourites[chat_id].append(req.strip())
    storeFavourites()


def storeFavourites():
    writer_lock.acquire()
    dirty = False
    for key in dirtyBitFavouritesList.keys():
        if dirtyBitFavouritesList[key] == 1:
            dirty = True
            break

    if dirty:
        try:
            with open(favourite_filename, 'w') as f:
                for key in dictUserFavourites.keys():

                    f.write(str(key) + ":")
                    f.write(":".join(dictUserFavourites[key]) + "\n")

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
    for i in range(0, int(len(dictUserFavourites[chat_id])/3)+1, 1):
        buttonLists.append(list())
    
    if len(dictUserFavourites[chat_id]) > 6:
        buttonLists[0] = dictUserFavourites[chat_id][:3]
        buttonLists[1] = dictUserFavourites[chat_id][3:6]
        buttonLists[2] = dictUserFavourites[chat_id][6:]
    elif len(dictUserFavourites[chat_id]) > 3:
        buttonLists[0] = dictUserFavourites[chat_id][:3]
        buttonLists[1] = dictUserFavourites[chat_id][3:]
    else:
        buttonLists[0] = dictUserFavourites[chat_id]
    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists,resize_keyboard=True)
    return keyboard 

def parseResponse(text):
    try:
        nextArr = text.split(sep=",")
        first = nextArr[0][14:].strip()
        firstInfo = first.split() 
        result = list()
        result.append("TperHellobus:\n") 
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
  
    return parseResponse(root.text)


def getStopInfo(params):
   
    if len(params) >= 3:
        return makeReq(params[0], params[1], params[2])
    elif len(params) == 2:
        return makeReq(params[0], params[1], "")
    elif len(params) == 1:
        return makeReq(params[0], "", "")
    else:
        return "An error occurred"

def getStopLocation(stop):
    for child in xml_root:
        id_fermata = child[1].text
        
        if id_fermata == stop:
            lat_fermata = child[7].text
            lon_fermata = child[8].text
            return (lat_fermata, lon_fermata)
    return ("LAT not found", "LON not found")

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
                bot.sendMessage(chat_id, donation_string)
                bot.sendMessage(chat_id, output_string, reply_markup=makeRecentKeyboard(chat_id))

        
        elif content_type == "location":
            now = datetime.now()
            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### MESSAGGIO = " + repr(msg))
            lat_user = msg["location"]["latitude"]
            lon_user = msg["location"]["longitude"]
       
            output = makeNearbyOutput(lat_user, lon_user) 
            bot.sendMessage(chat_id, donation_string)

            bot.sendMessage(chat_id, output["output_string"], reply_markup=makeLocationKeyboard(output["stringKeyboardList"]))

        else:
            now = datetime.now()
            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +" ### MESSAGGIO = " + repr(msg))
            output_string = emo_ita+ " Non ho capito... Invia un messaggio di testo o la tua posizione!\n"+ emo_eng +" I don't understand...  Send a text message or your location"
            bot.sendMessage(chat_id, output_string)
        
    except Exception as e:
        print(repr(e))
        output_string = emo_ita+ " Non ho capito... Invia un messaggio di testo o la tua posizione!\n"+ emo_eng +" I don't understand...  Send a text message or your location"
        bot.sendMessage(chat_id, output_string)


restoreFavourites()

MessageLoop(bot, {'chat': on_chat_message}).run_as_thread()



print('Listening ...')
# Keep the program running.
while 1:
    time.sleep(10)

