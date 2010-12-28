import socket 
import string
import sys

import translate

SERVER = 'chat.freenode.net' #server to connect to
PORT = 8000 #port to connect to
NICKNAME = 'tr-bot' #nickname to join with
CHANNEL = '#27c3-Saal-1' #channel to join
VERBOSE = 0
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
join(CHANNEL)

#PING PONG
while True:
    
    data = IRC.recv (1024)
    if VERBOSE:
        print data
    if data.find('PING') != -1:
        IRC.send('PONG' + " " + data.split()[1] + '\r\n')
    message = unicode(data.split(':')[2])
    sender = data.split(':')[1].split('!')[0]
    if data.split()[1] == 'PRIVMSG':
        if sys.argv[1] == '-de':
            print '<' + sender + '> ' +  translate.fromAjax(message, 'en', 'de')
        if sys.argv[1] == '-en':
            print '<' + sender + '> ' +  translate.fromAjax(message, 'de', 'en')
    # for word in data.split():
    #     if word in trigger_words:
    #         IRC.send('PRIVMSG' + " " + CHANNEL + " :" + trigger_words[word] + '\r\n')
