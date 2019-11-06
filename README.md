# busbolobot

A Telegram bot for buses timetables in Bologna.



## Getting started

* Install dependencies.
```
sudo apt install python3-setuptools
sudo apt install python3-pip
sudo apt install python3-venv
```
or
```
sudo pacman -S python-setuptools 
sudo pacman -S python-pip
sudo pacman -S python-virtualenv
```



## Deploy as systemd service


* Create a new user and add it to sudoers. Then switch to new user and navigate to its home directory.

```
sudo adduser busbolouser
sudo adduser busbolouser sudo
su busbolouser
cd
```

* Clone repository.
```
git clone https://github.com/luca-ant/busbolobot.git
cd busbolouser
```
or
```
git clone git@github.com:luca-ant/busbolobot.git
cd busbolobot
```

* Run service.sh with *install* argument.
```
chmod u+x service.sh
./service.sh install
```

* Check manually the file */etc/systemd/system/busbolobot.service*. Put the bot token where you see "YOUR_TOKEN_HERE".

* Start the service
```
sudo systemctl enable busbolobot.service
sudo systemctl start busbolobot.service

```

## Run manually

* Clone repository.
```
git clone https://github.com/luca-ant/busbolobot.git
```
or
```
git clone git@github.com:luca-ant/busbolobot.git
```


* Create a virtual environment and install requirements modules.
```
cd busbolobot
python3 -m venv venv
source venv/bin/activate

python3 -m pip install -r requirements.txt
```

* Set BUS_BOT_TOKEN environment variable with bot's token.

```
export BUS_BOT_TOKEN=YOUR_TOKEN_HERE
```
* Run the python script as:

```
python unibotimetablesbot/unibotimetablesbot.py
```

## Credits
* busbolobot was developed by Luca Antognetti


**An instance of bot it's now running!** You can find it on Telegram searching `@busbolobot`










