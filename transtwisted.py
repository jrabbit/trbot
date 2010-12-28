import sys
import re
import urllib2
import urllib
import json
from twisted.internet import reactor, task, defer, protocol
from twisted.python import log
from twisted.words.protocols import irc
from twisted.web.client import getPage
from twisted.application import internet, service

import translate
import googleajax

HOST, PORT = 'irc.freenode.net', 6667
VERBOSE = 1

def googleTranslate(text, languageFrom, languageTo):
    """
    Returns a simple string translating the text from "languageFrom" to
    "LanguageTo" using Google Translate AJAX Service.
    """

    LANG={
        "arabic":"ar", "bulgarian":"bg", "chinese":"zh-CN",
        "croatian":"hr", "czech":"cs", "danish":"da", "dutch":"nl",
        "english":"en", "finnish":"fi", "french":"fr", "german":"de",
        "greek":"el", "hindi":"hi", "italian":"it", "japanese":"ja",
        "korean":"ko", "norwegian":"no", "polish":"pl", "portugese":"pt",
        "romanian":"ro", "russian":"ru", "spanish":"es", "swedish":"sv" }

    base_url='http://ajax.googleapis.com/ajax/services/language/translate?'
    langpair='%s|%s'%(LANG.get(languageFrom.lower(),languageFrom),
                      LANG.get(languageTo.lower(),languageTo))
    params=urllib.urlencode( (('v',1.0),
                       ('q',text.encode('utf-8')),
                       ('langpair',langpair),) )
    url=base_url+params
    d = getPage(url)
    d.addCallback(json.loads)
    d.addCallback(lambda obj: googleajax.fixGoogleText(obj['responseData']['translatedText']))
    return d


class MyFirstIRCProtocol(irc.IRCClient):
    nickname = 'twistedtrans'

    # This is called once the server has acknowledged that we sent
    # both NICK and USER.
    def signedOn(self):
        self.join(self.factory.channels)

    # Obviously, called when a PRIVMSG is received.
    def privmsg(self, user, channel, message):
        if channel == '*': 
            return
        nick, _, host = user.partition('!')
        if nick.lower() in ('nickserv', 'chanserv'):
            return # ignore nickserv and chanserv
        if channel == self.nickname:
            self.msg(nick, "please don't msg me directly, use the channel")
            return
        d = googleTranslate(message, 'de', 'en')
        d.addCallback(self._send_it, fromuser=nick, channel=channel)
        
        e = googleTranslate(message, 'en', 'de')
        e.addCallback(self._send_it, fromuser=nick, channel=channel)
        
    def _send_it(self, message, fromuser, channel):
        message = '%s> %s' % (fromuser, message.encode('utf-8'))
        self.msg(channel, message)


class MyFirstIRCFactory(protocol.ReconnectingClientFactory):
    protocol = MyFirstIRCProtocol
    channels = '##infotest'

if __name__ == '__main__':
    # This runs the program in the foreground. We tell the reactor to connect
    # over TCP using a given factory, and once the reactor is started, it will
    # open that connection.
    reactor.connectTCP(HOST, PORT, MyFirstIRCFactory())
    # Since we're running in the foreground anyway, show what's happening by
    # logging to stdout.
    if VERBOSE:
        log.startLogging(sys.stdout)
    # And this starts the reactor running. This call blocks until everything is
    # done, because this runs the whole twisted mainloop.
    reactor.run()

# This runs the program in the background. __name__ is __builtin__ when you use
# twistd -y on a python module.
elif __name__ == '__builtin__':
    # Create a new application to which we can attach our services. twistd wants
    # an application object, which is how it knows what services should be
    # running. This simplifies startup and shutdown.
    application = service.Application('MyFirstIRCBot')
    # twisted.application.internet.TCPClient is how to make a TCP client service
    # which we can attach to the application.
    ircService = internet.TCPClient(HOST, PORT, MyFirstIRCFactory())
    ircService.setServiceParent(application)
    # twistd -y looks for a global variable in this module named 'application'.
    # Since there is one now, and it's all set up, there's nothing left to do.