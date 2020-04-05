import requests
from datetime import datetime
import time
import xml.etree.ElementTree as ET
import logging
import traceback

from location import get_stop_name
import config


def parse_response(xml_root, stop, line, text):
    try:
        name = get_stop_name(xml_root, stop)
        nextArr = text.split(sep=",")
        first = nextArr[0][14:].strip()
        first_info = first.split()
        result = list()
        result.append(config.emo_bus + " [<b>" + first_info[0] + "</b>] ")

        if first_info[1] == "DaSatellite":
            result.append(config.emo_sat + " DA SATELLITE ")
        else:
            result.append(config.emo_clock + " DA ORARIO ")

        tdiff = datetime.strptime(
            first_info[2], '%H:%M') - datetime.strptime(time.strftime('%H:%M'), '%H:%M')

        result.append("tra <b>" + repr(int(tdiff.seconds / 60)) +
                      " minuto/i </b>(" + first_info[2] + ")")

        if len(nextArr) > 1:
            second = nextArr[1].strip()
            second_info = second.split()

            result.append("\n" + config.emo_bus + " [<b>" + second_info[0] + "</b>] ")

            if second_info[1] == "DaSatellite":
                result.append(config.emo_sat + " DA SATELLITE ")
            else:
                result.append(config.emo_clock + " DA ORARIO ")

            tdiff = datetime.strptime(
                second_info[2], '%H:%M') - datetime.strptime(time.strftime('%H:%M'), '%H:%M')
            result.append("tra <b>" + repr(int(tdiff.seconds / 60)
                                           ) + " minuto/i </b>(" + second_info[2] + ")")

        result.append("\n")
        result.append(config.emo_ita)
        if (line != ""):
            result.append(" Linea: <b>" + line + "</b>")

        result.append(" Fermata: <b>" + stop +
                      "</b> " + "<i>("+name+")</i>\n")
        result.append(config.emo_eng)
        if (line != ""):
            result.append(" Line: <b>" + line + "</b>")

        result.append(" Stop: <b>" + stop +
                      "</b> " + "<i>("+name+")</i>\n")

        return "".join(result)
    except:
        traceback.print_exc()
        return text


def make_request(xml_root, stop, line, time):
    body = "fermata=" + stop + "&linea=" + line + "&oraHHMM=" + time
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(url=config.url, data=body, headers=headers)

    root = ET.fromstring(response.text)

    return parse_response(xml_root, stop, line, root.text)


def get_stop_info(xml_root, params):
    if len(params) >= 3:
        return make_request(xml_root, params[0], params[1], params[2])
    elif len(params) == 2:
        return make_request(xml_root, params[0], params[1], "")
    elif len(params) == 1:
        return make_request(xml_root, params[0], "", "")
    else:
        return "error"
