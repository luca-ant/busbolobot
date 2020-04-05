import collections
import math
import config




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


def get_stop_location(xml_root, stop):
    if stop == "":
        return ("LAT not found", "LON not found")

    for child in xml_root:
        stop_id = child[1].text

        if stop_id == stop:
            stop_lat = child[7].text
            stop_lon = child[8].text
            return (stop_lat, stop_lon)
    return ("LAT not found", "LON not found")


def get_stop_name(xml_root, stop):

    for child in xml_root:
        stop_id = child[1].text

        if stop_id == stop:
            name = child[2].text
            break
    else:
        name = ""

    return name


def make_nearby_output(xml_root, lat_user, lon_user):
    result = collections.defaultdict()
    bus_lines = collections.defaultdict(list)
    output = list()
    string_keyboard_list = list()
    output.append(config.emo_ita + " FERMATE VICINE\n" +
                  config.emo_eng + " NEARBY STOPS\n\n")
    for child in xml_root:
        linea = child[0].text
        stop_id = child[1].text
        stop_name = child[2].text
        stop_lat = child[7].text
        stop_lon = child[8].text

        dist = distance(lat_user, lon_user,
                        float(stop_lat), float(stop_lon))
        if (dist < 25):

            element = stop_id + " - " + stop_name + \
                " (" + repr(int(dist)) + " m)"
            bus_lines[element].append(linea)
            string_keyboard_list.append(stop_id + " " + linea)
            if stop_id not in string_keyboard_list:
                string_keyboard_list.append(stop_id)

    for s in bus_lines.keys():
        output.append(s)
        output.append("\n")
        output.append("Lines: ")
        for n in bus_lines[s]:
            output.append(n + " ")
        output.append("\n\n")

    string_keyboard_list.sort()
    result["string_keyboard_list"] = string_keyboard_list
    result["output_string"] = "".join(output)
    return result
