from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from favourite import get_favourites
from location import get_stop_name
import config

def make_inline_stop_keyboard(params, time):
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
        [InlineKeyboardButton(text=config.emo_stop + ' STOP!',
                              callback_data="stop " + s)],
        [InlineKeyboardButton(text=config.emo_notify + ' RESTART for 5 min',
                              callback_data="notify " + s + " 5")],
        [InlineKeyboardButton(text=config.emo_notify + ' RESTART for 10 min',
                              callback_data="notify " + s + " 10")]

    ])
    return keyboard


def make_inline_notify_keyboard(chat_id, params):
    try:
        stop = params[0].strip()
    except:
        stop = ""
    try:
        line = " " + params[1].strip()
    except:
        line = ""
    s = (stop + line).strip()

    if s.strip() in get_favourites(chat_id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=config.emo_cross + ' REMOVE "' + s + '" FROM FAVOURITES',
                                  callback_data="remove " + s)],
            [InlineKeyboardButton(text=config.emo_notify + ' NOTIFY for 5 min',
                                  callback_data="notify " + s + " 5")],
            [InlineKeyboardButton(text=config.emo_notify + ' NOTIFY for 10 min',
                                  callback_data="notify " + s + " 10")],
            [InlineKeyboardButton(text=config.emo_notify + ' NOTIFY for 15 min',
                                  callback_data="notify " + s + " 15")]
        ])

    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=config.emo_fav + ' ADD "' + s + '" TO FAVOURITES',
                                  callback_data="add " + s)],
            [InlineKeyboardButton(text=config.emo_notify + ' NOTIFY for 5 min',
                                  callback_data="notify " + s + " 5")],
            [InlineKeyboardButton(text=config.emo_notify + ' NOTIFY for 10 min',
                                  callback_data="notify " + s + " 10")],
            [InlineKeyboardButton(text=config.emo_notify + ' NOTIFY for 15 min',
                                  callback_data="notify " + s + " 15")]
        ])
    return keyboard




def make_location_keyboard(string_keyboard_list):

    row = int(len(string_keyboard_list) / 3) + 2
    cols = 3

    buttonLists = list()
    for i in range(row):
        buttonLists.append(list())

    i = 0
    index = 0
    for s in string_keyboard_list:
        buttonLists[index].append(s)
        i += 1
        if i % cols == 0:
            index = index + 1
    buttonLists[row - 1].append(config.emo_back + " BACK TO MAIN")
    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)

    return keyboard


def make_favourites_keyboard(chat_id, xml_root):
    user_favourites = get_favourites(chat_id)
    row = 6
    cols = 2

    buttonLists = list()
    for i in range(row):
        buttonLists.append(list())

    index = 0
    for i in range(len(user_favourites)):
        name = get_stop_name(xml_root, user_favourites[i].split()[0])
        buttonLists[index].append(
            user_favourites[i] + " - " + name)
        if i % cols != 0:
            index += 1

    buttonLists[5].append(config.emo_back + " BACK TO MAIN")

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_main_keyboard(chat_id):

    fav_button = KeyboardButton(text=config.emo_fav+" FAVOURITES")
    location_button = KeyboardButton(text=config.emo_gps + " SEND LOCATION", request_location=True)

    help_button = KeyboardButton(text=config.emo_help+" HELP")
    privacy_button = KeyboardButton(config.emo_privacy+" PRIVACY POLICY")

    custom_keyboard = [[fav_button],[location_button], [help_button], [privacy_button]]

    keyboard = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

    return keyboard
