from datetime import datetime
import schedule
import shutil
import zipfile
import wget
import time
import os
import collections
import logging
import traceback
import xml.etree.ElementTree as ET
import threading
from datetime import datetime, timedelta
from collections import defaultdict

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, Handler
from telegram import ParseMode
from threading import Thread

from keyboards import make_inline_stop_keyboard, make_inline_notify_keyboard, make_location_keyboard, make_favourites_keyboard, make_main_keyboard
from location import make_nearby_output
from favourite import get_favourites, restore_all_favourites, add_favourite, remove_favourite
from web_request import get_stop_info
import config

xml_root = None

notify_threads = collections.defaultdict()


class NotifyThread(Thread):
    def __init__(self, update, context, time_notify, stop, line, first_msg):

        Thread.__init__(self)

        self.chat_id = update.callback_query.message.chat_id
        self.update = update
        self.context = context
        self.msg_id = update.callback_query.message.message_id
        self.time_notify = time_notify
        self.stop = stop.strip()
        self.line = line.strip()
        self.stop_flag = False
        self.count = time_notify
        self.last_message = first_msg
        self.end_time = None
        self.keyboard = make_inline_stop_keyboard((stop, line), time_notify)

    def run(self):

        self.end_time = datetime.now() + timedelta(minutes=self.time_notify)

        while (self.count > 0):
            try:
                self.count = self.count - 1
                time.sleep(60)
                if self.stop_flag:
                    break
                output_string = get_stop_info(xml_root, (self.stop, self.line))
                output_string += "\n<b>NOTIFICATIONS UP TO " + \
                    self.end_time.strftime("%H:%M")+"</b>"
                self.last_message = output_string

                self.context.bot.delete_message(chat_id=self.chat_id,
                                                message_id=self.msg_id)

                new_msg = self.update.callback_query.message.reply_html(
                    output_string, reply_markup=self.keyboard)
                self.msg_id = new_msg.message_id

            except:
                traceback.print_exc()

        if self.stop_flag:
            try:
                now = datetime.now()
                logging.info(
                    "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### CHAT_ID = " + str(self.chat_id) + " ### NOTIFICATIONS STOP for " + self.stop + " " + self.line)

                print(str(self.chat_id) + " stop " +
                      str(self.stop) + " " + str(self.line))

                self.context.bot.edit_message_text(self.last_message, chat_id=self.chat_id,
                                                   message_id=self.msg_id, parse_mode=ParseMode.HTML,
                                                   reply_markup=make_inline_notify_keyboard(self.chat_id, (self.stop, self.line)))
            except:
                traceback.print_exc()

        else:
            now = datetime.now()
            logging.info(
                "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### CHAT_ID = " + str(self.chat_id) + " ### NOTIFICATIONS END for " + self.stop + " " + self.line)

            try:
                print(str(self.chat_id) + " end " +
                      str(self.stop) + " " + str(self.line))
                self.context.bot.edit_message_text(self.last_message + "\n<b>NOTIFICATIONS ENDED!</b>", chat_id=self.chat_id,
                                                   message_id=self.msg_id, parse_mode=ParseMode.HTML,
                                                   reply_markup=make_inline_notify_keyboard(self.chat_id, (self.stop, self.line)))
            except:
                traceback.print_exc()

    def set_stop_flag(self, b):
        self.stop_flag = b



def callback_query(update, context):
    try:
        text = update.callback_query.message.text
        chat_id = update.callback_query.message.chat_id
        message_id = update.callback_query.message.message_id
        query_data = update.callback_query.data
        user_favourites = get_favourites(chat_id)
        print(chat_id, query_data)
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

            end_time = datetime.now() + timedelta(minutes=t)

            output_string = get_stop_info(xml_root, (stop, line))
            output_string += "\n<b>NOTIFICATIONS STARTED UP TO " + \
                end_time.strftime("%H:%M") + "</b>"
            now = datetime.now()
            logging.info(
                "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### CHAT_ID = " + str(chat_id) + " ### NOTIFICATIONS START " + stop + " " + line + " for " + str(
                    t) + " min")
            thread = NotifyThread(update, context, t,
                                  stop, line, output_string)

            try:
                notify_threads[chat_id].set_stop_flag(True)
            except:
                pass

            notify_threads[chat_id] = thread
            thread.start()

            try:
                update.callback_query.edit_message_text(
                    output_string, parse_mode=ParseMode.HTML, reply_markup=make_inline_stop_keyboard((stop, line), t))
            except:
                update.callback_query.answer(text="SLOW DOWN!!")
                traceback.print_exc()

            update.callback_query.answer(text="NOTIFICATIONS STARTED!")

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
                notify_threads[chat_id].set_stop_flag(True)
            except:
                pass

            output_string = get_stop_info(xml_root, (stop, line))
            output_string += "\n<b>NOTIFICATIONS STOPPED!</b>"
            update.callback_query.answer(text="NOTIFICATIONS STOPPED!")

            try:
                update.callback_query.edit_message_text(output_string, parse_mode=ParseMode.HTML,
                                                        reply_markup=make_inline_notify_keyboard(chat_id, (stop, line)))
            except:
                update.callback_query.answer(text="SLOW DOWN!!")
                traceback.print_exc()

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
            if fav not in user_favourites:
                add_favourite(chat_id, stop+" "+line)

                output_string = "<b>" + stop + " " + line+" WAS ADDED TO YOUR FAVOURITES</b>"

                update.callback_query.message.reply_html(
                    output_string, reply_markup=make_favourites_keyboard(xml_root, chat_id))
                output_string = get_stop_info(xml_root, (stop, line))

                update.callback_query.message.reply_html(
                    output_string, reply_markup=make_inline_notify_keyboard(chat_id, (stop, line)))
            else:
                output_string = "<b>" + stop + " " + line + \
                    " ALREADY IN YOUR FAVOURITES</b>"

                update.callback_query.message.reply_html(
                    output_string, reply_markup=make_favourites_keyboard(xml_root, chat_id))

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
            if fav in user_favourites:

                remove_favourite(chat_id, stop+" "+line)

                output_string = "<b>" + stop + " " + line + \
                    " WAS REMOVED FROM YOUR FAVOURITES</b>"

                update.callback_query.message.reply_html(
                    output_string, reply_markup=make_favourites_keyboard(xml_root, chat_id))
                output_string = get_stop_info(xml_root, (stop, line))

                update.callback_query.message.reply_html(
                    output_string, reply_markup=make_inline_notify_keyboard(chat_id, (stop, line)))
            else:
                output_string = "<b>" + stop + " " + line + " NOT IN YOUR FAVOURITES</b>"

                update.callback_query.message.reply_html(
                    output_string, reply_markup=make_favourites_keyboard(xml_root, chat_id))

    except:
        update.callback_query.answer(text="SLOW DOWN!!")
        traceback.print_exc()


def start(update, context):
    chat_id = update.message.chat_id
    output_string = config.emo_bus + " TPER HelloBus on Telegram! " + \
        config.emo_bus + "\n\n" + config.help_string
    update.message.reply_html(
        output_string, reply_markup=make_favourites_keyboard(xml_root, chat_id))


def help(update, context):
    chat_id = update.message.chat_id
    update.message.reply_html(
        config.help_string, reply_markup=make_main_keyboard(chat_id))


def message(update, context):
    chat_id = update.message.chat_id
    text = update.message.text

#    user_favourites = get_favourites(chat_id)
    print(chat_id, text)
    now = datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id) + " = " + text)

    try:

        if text == config.emo_help+" HELP":

            update.message.reply_html(
                config.help_string, reply_markup=make_main_keyboard(chat_id))

        elif text == config.emo_privacy+" PRIVACY POLICY":

            update.message.reply_html(
                config.privacy_string, reply_markup=make_main_keyboard(chat_id))
        elif text == config.emo_fav+" FAVOURITES":

            output_string = text
            update.message.reply_html(
                output_string, reply_markup=make_favourites_keyboard(xml_root, chat_id))
        elif text == config.emo_back + " BACK TO MAIN":
            output_string = text
            update.message.reply_html(
                output_string, reply_markup=make_main_keyboard(chat_id))

        else:
            if "-" in text:
                mess = text.split("-")
                mess = ''.join(mess[0].strip())

            else:
                mess = text

            stop = mess.split()[0]

            params = mess.split()
            output_string = get_stop_info(xml_root, params)
            if "<b>help</b>" in output_string.lower() or "hellobushelp" in output_string.lower():
                update.message.reply_html(
                    output_string, reply_markup=make_main_keyboard(chat_id))
            else:
                update.message.reply_html(config.donation_string)
                update.message.reply_html(
                    output_string, reply_markup=make_inline_notify_keyboard(chat_id, params))

    except:
        traceback.print_exc()
        output_string = config.emo_ita + " Non ho capito... Invia un messaggio o la tua posizione!\n" + \
            config.emo_eng + " I don't understand... Send a message or your location"
        update.message.reply_html(
            output_string, reply_markup=make_main_keyboard(chat_id))


def location(update, context):
    try:
        chat_id = update.message.chat_id
        location = update.message.location

        lat_user = location.latitude
        lon_user = location.longitude

        output = make_nearby_output(xml_root, lat_user, lon_user)
        update.message.reply_html(config.donation_string)

        update.message.reply_html(output["output_string"], reply_markup=make_location_keyboard(
            output["string_keyboard_list"]))
    except:
        traceback.print_exc()
        output_string = config.emo_ita + " Non ho capito... Invia un messaggio o la tua posizione!\n" + \
            config.emo_eng + " I don't understand... Send a message or your location"
        update.message.reply_html(
            output_string, reply_markup=make_main_keyboard(chat_id))


def error(update, context):
    logging.warning('MESSAGE "%s" CAUSED ERROR "%s"',
                    update.message, context.error)

def update_stops_file():

    os.makedirs(config.download_dir, exist_ok=True)

    now = datetime.now()
    y = now.strftime("%Y")
    m = now.strftime("%m")
    d = now.strftime("%d")

    xml_url = 'https://solweb.tper.it/web/tools/open-data/open-data-download.aspx?source=solweb.tper.it&filename=lineefermate&version={}{}{}&format=xml'.format(y,m,d) 

    zip_name = wget.download(xml_url, out=config.download_dir+"lineefermate_{}{}{}.zip".format(y,m,d) )
    print()
    if zipfile.is_zipfile(zip_name):
        logging.info("### DOWNLOADED " + zip_name)
        print("### DOWNLOADED " + zip_name)

        with zipfile.ZipFile(zip_name, 'r') as zip_ref:
            zip_ref.extractall(config.download_dir)

        xml_file = 'lineefermate_{}{}{}.xml'.format(y,m,d)
        shutil.copy(config.download_dir+xml_file, config.xml_stops_file)

    global xml_root

    tree = ET.parse(config.xml_stops_file)
    xml_root = tree.getroot()

    logging.info("### LOADED " + config.xml_stops_file)
    print("### LOADED " + config.xml_stops_file)

    os.remove(zip_name)

def main():

    logging.info("### WORKING DIR " + config.working_dir)
    print("### WORKING DIR " + config.working_dir)

    os.makedirs(config.data_dir, exist_ok=True)
    os.makedirs(config.favourites_dir, exist_ok=True)

    update_stops_file()
    schedule.every().day.at("04:00").do(update_stops_file)

    updater = Updater(config.token, use_context=True)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", help))

    updater.dispatcher.add_handler(MessageHandler(Filters.text, message))
    updater.dispatcher.add_handler(CallbackQueryHandler(callback_query))
    updater.dispatcher.add_handler(MessageHandler(Filters.location, location))

    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    print('Listening ...')

    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
