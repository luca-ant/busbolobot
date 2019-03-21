import collections
import sys
import math
from datetime import datetime
import time
import xml.etree.ElementTree as ET
import requests
import telepot
from collections import defaultdict
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

with open(sys.argv[1]) as f:
    token = f.read().strip()
f.close()

bot = telepot.Bot(token)
donation_string = "Se ti è piacuto questo bot e vuoi sostenerlo puoi fare una donazione qui! -> https://www.paypal.me/lucaant"
url = "https://hellobuswsweb.tper.it/web-services/hello-bus.asmx/QueryHellobus"

file_xml_fermate = "lineefermate_20190301.xml"

tree = ET.parse(file_xml_fermate)
xml_root = tree.getroot()



dictUserFavourites = collections.defaultdict(list)


def addLastReq(chat_id, req):
    if req not in dictUserFavourites[chat_id]:
        if len(dictUserFavourites[chat_id]) >= 3:
            dictUserFavourites[chat_id].pop(0)

        dictUserFavourites[chat_id].append(req)







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

def makeLocationKeyboard(stringList):

    buttonLists = list()

    for i in range(0, int(len(stringList)/3)+1, 1):
       buttonLists.append(list())
    i = 0
    index = 0
    for str in stringList:
        buttonLists[index].append(str)
        i += 1
        if i % 3 == 0:
            index = index + 1

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)

    return keyboard

def makeRecentKeyboard(chat_id):

    buttonLists = list()

    buttonLists.append(list())
    buttonLists[0] = dictUserFavourites[chat_id]

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists,resize_keyboard=True)
    return keyboard 

def parseResponse(text):
    try:
        nextArr = text.split(sep=",")
        first = nextArr[0][14:].strip()
        second = nextArr[1].strip()
        firstInfo = first.split() 
        secondInfo = second.split() 
        result = list()
        result.append("TperHellobus:\n") 
        result.append("["+firstInfo[0]+"] -> ")
        
        if firstInfo[1] == "DaSatellite":
            result.append("Da satellite ")
        else:
            result.append("Da orario ")
        
        tdiff = datetime.strptime(firstInfo[2],'%H:%M') - datetime.strptime(time.strftime('%H:%M'), '%H:%M')

        diff = datetime.strptime("0:05",'%H:%M') - datetime.strptime(time.strftime('23:50'), '%H:%M')
        int(tdiff.seconds/60)

        result.append("tra " + repr(int(tdiff.seconds/60)) + " minuto/i ("+ firstInfo[2] +")\n")
        
        result.append("["+secondInfo[0]+"] -> ")
        
        if secondInfo[1] == "DaSatellite":
            result.append("Da satellite ")
        else:
            result.append("Da orario ")
        
        tdiff = datetime.strptime(secondInfo[2],'%H:%M') - datetime.strptime(time.strftime('%H:%M'), '%H:%M')

        diff = datetime.strptime("0:05",'%H:%M') - datetime.strptime(time.strftime('23:50'), '%H:%M')
        int(tdiff.seconds/60)


        result.append("tra " + repr(int(tdiff.seconds/60)) + " minuto/i ("+ secondInfo[2] +")")

        

        return "".join(result)
    except:
       return text


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



def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    #print(msg) 

    if content_type == "text":
        if (msg["text"] == "/start"):
            output_string = "TPER HelloBus on Telegram!\n""Invia\n\"NUMERO_FERMATA LINEA\"\noppure\n\"NUMERO_FERMATA LINEA ORA\" \noppure\nla tua posizione per ricevere l'elenco delle fermate vicine e poi scegli la fermata e la linea che ti interessa dalla tastiera.\n\nPer problemi e malfunzionamenti inviare una mail a luca.ant96@libero.it descrivendo dettagliatamente il problema."
    

            bot.sendMessage(chat_id, output_string, reply_markup=ReplyKeyboardRemove())
        elif (msg["text"] == "/help"):
            output_string ="Invia\n\"NUMERO_FERMATA LINEA\"\noppure\n\"NUMERO_FERMATA LINEA ORA\" \noppure\nla tua posizione per ricevere l'elenco delle fermate vicine e poi scegli la fermata e la linea che ti interessa dalla tastiera.\n\nPer problemi e malfunzionamenti inviare una mail a luca.ant96@libero.it descrivendo dettagliatamente il problema."
    
            bot.sendMessage(chat_id, donation_string)
            bot.sendMessage(chat_id, output_string, reply_markup=ReplyKeyboardRemove())
        else:
            params = msg["text"].split()
            output_string = getStopInfo(params)
            addLastReq(chat_id, msg["text"])
            bot.sendMessage(chat_id, donation_string)
            bot.sendMessage(chat_id, output_string, reply_markup=makeRecentKeyboard(chat_id))

    
    elif content_type == "location":

        
        lat_user = msg["location"]["latitude"]
        lon_user = msg["location"]["longitude"]
        d = collections.defaultdict(list)
        output = []
        stringList = []
        output.append("FERMATE VICINE:\n\n")
        for child in xml_root:
            linea = child[0].text
            id_fermata = child[1].text
            nome_fermata = child[2].text
            lat_fermata = child[7].text
            lon_fermata = child[8].text
            
            dist = distance(float(lat_user), float(lon_user), float(lat_fermata), float(lon_fermata)) 
            if(dist < 15):
                
                element = id_fermata + " - "+ nome_fermata + " ("+ repr(int(dist)) +" m)"
                d[element].append(linea)
                stringList.append(id_fermata + " "+linea)
        

        for s in d.keys():
            output.append(s)
            output.append("\n")
            output.append("Linee: ")
            for n in d[s]:
                output.append(n + " ")
        
            output.append("\n\n")
        
        
        stringList.sort()
        output_string = "".join(output)
        bot.sendMessage(chat_id, donation_string)

        bot.sendMessage(chat_id, output_string, reply_markup=makeLocationKeyboard(stringList))

    else:
        output_string = "Non ho capito... Invia un messaggio di testo o la tua posizione!"
        bot.sendMessage(chat_id, output_string)



MessageLoop(bot, {'chat': on_chat_message}).run_as_thread()

print('Listening ...')
# Keep the program running.
while 1:
    time.sleep(10)
