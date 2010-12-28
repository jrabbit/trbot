import socket 
import string
import sys

import translate
import googleajax

SERVER = 'chat.freenode.net' #server to connect to
PORT = 8000 #port to connect to
NICKNAME = 'tr-bot' #nickname to join with
# CHANNELS = ['#27c3-Saal-1'] #channels to join
CHANNELS = ['#bots']
VERBOSE = 1
IRC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#open a connection with the server
def irc_conn():
    IRC.connect((SERVER, PORT))

#simple function to send data through the socket
def send_data(command):
    IRC.send(command + '\n')

#join the channel
def join(channel):
    send_data("JOIN %s" % channel)

#send login data (customizable)
def login(nickname, username='user', password = None, realname='tr-bot', hostname='jrabbit', servername='Server'):
    send_data("USER %s %s %s %s" % (username, hostname, servername, realname))
    send_data("NICK " + nickname)

irc_conn()
login(NICKNAME)
for channel in CHANNELS:
    join(channel)

#PING PONG
while True:
    
    data = IRC.recv (1024)
    if VERBOSE:
        print data
    # if data.split(':')[-1] == 'End of /NAMES list.':
    #     print "synced to channel"
    if data.find('PING') != -1:
        IRC.send('PONG' + " " + data.split()[1] + '\r\n')
    if data.split()[1] == 'PRIVMSG':
        try:
            message = ':'.join(data.split(':')[2:]).decode('utf-8')
        except Exception, e:
            print e
            print data.split(':')[2]
            print data
        sender = data.split(':')[1].split('!')[0]
        if sys.argv[1] == '-de':
            print '<' + sender + '> ' +  googleajax.fixGoogleText(translate.fromAjax(message, 'en', 'de'))
        if sys.argv[1] == '-en':
            print '<' + sender + '> ' +  googleajax.fixGoogleText(translate.fromAjax(message, 'de', 'en'))
