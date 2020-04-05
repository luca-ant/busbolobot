import os
import collections
import traceback
import config

def restore_all_favourites():

    dict_user_favourites = collections.defaultdict(list)
    with os.scandir(config.favourites_dir) as entries:
        for e in entries:
            try:
                if e.is_file():
                    chat_id_str = e.name
                    chat_id = int(chat_id_str)
                if os.path.isfile(config.favourites_dir+chat_id_str):
                        with open(config.favourites_dir+chat_id_str) as f:
                            fav = f.readline().split(':')[0:9]
                            dict_user_favourites[chat_id] = fav

            except:
                traceback.print_exc()
    return dict_user_favourites

def add_favourite(chat_id, f):
    try:
        fav = get_favourites(chat_id)
        if f not in fav and f.replace(" ", "").isdigit():
            if len(fav) >= 10:
                fav.pop(0)
            fav.append(f)

        with open(config.favourites_dir+str(chat_id), 'w') as ff:
            for f in fav:
                ff.write(f + "\n")

    except Exception as e:
        traceback.print_exc()


def remove_favourite(chat_id, f):

    try:
        fav = get_favourites(chat_id)
        if f.strip() in fav:
            fav.remove(f.strip())
        with open(config.favourites_dir+str(chat_id), 'w') as ff:
            for f in fav:
                ff.write(f + "\n")

    except Exception as e:
        traceback.print_exc()



def get_favourites(chat_id):
    try:
        fav = []
        if os.path.isfile(config.favourites_dir+str(chat_id)):
            with open(config.favourites_dir+str(chat_id)) as ff:
                for line in ff:
                    if line.strip() not in fav and line.strip().replace(" ", "").isdigit():
                        fav.append(line.strip())

            fav = fav[0:10]
    except Exception as e:
        traceback.print_exc()
    return fav
