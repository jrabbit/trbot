import sys
import operator
import math
import re
import BeautifulSoup
from twisted.internet import reactor, task, defer, protocol
from twisted.python import log
from twisted.words.protocols import irc
from twisted.web.client import getPage
from twisted.application import internet, service

import translate
import googleajax



HOST, PORT = 'irc.freenode.net', 6667

# This is a dict of all of the operators the RPN calculator can handle. It maps
# the operator symbol to a tuple of (number of parameters, function to call).
calc_operators = {
    '+': (2, operator.add),
    '-': (2, operator.sub),
    '*': (2, operator.mul),
    '/': (2, operator.truediv),
    '//': (2, operator.div),
    '%': (2, operator.mod),
    '^': (2, operator.pow),
    'abs': (1, abs),
    'ceil': (1, math.ceil),
    'floor': (1, math.floor),
    'round': (2, round),
    'trunc': (1, int),
    'log': (2, math.log),
    'ln': (1, math.log),
    'pi': (0, lambda: math.pi),
    'e': (0, lambda: math.e),
}

class MyFirstIRCProtocol(irc.IRCClient):
    nickname = 'twistedtrans'
    
    # This is called once the server has acknowledged that we sent
    # both NICK and USER.
    def signedOn(self):
        self.join(self.factory.channels)
    
    # Obviously, called when a PRIVMSG is received. 
    def privmsg(self, user, channel, message):
        nick, _, host = user.partition('!')
        # When channel == self.nickname, the message was sent to the bot 
        # directly and not to a channel. If we're not addressed and this wasn't
        # a direct message, don't do anything.
        if channel != self.nickname and not message.startswith(self.nickname):
            return
        # Strip off any addressing. 
        message = re.sub(
            r'^%s[.,>:;!?]*\s*' % re.escape(self.nickname), '', message)
        command, _, rest = message.partition(' ')
        # Get the function corresponding to the command given. 
        func = getattr(self, 'command_' + command, None)
        # Or, if there was no function, ignore it.
        if func is None:
            return
        # maybeDeferred will always return a Deferred. It calls func(rest), and
        # if that returned a Deferred, return that. Otherwise, return the return
        # value of the function wrapped in twisted.internet.defer.succeed. If
        # an exception was raised, wrap the traceback in 
        # twisted.internet.defer.fail and return that.
        d = defer.maybeDeferred(func, rest)
        # Depending on if this was directly addressed to us or not, change how
        # the response will be sent. If the command succeeded, reply with the
        # result. Otherwise, reply with a terse error message.
        if channel == self.nickname:
            args = [nick]
        else:
            args = [channel, nick]
        d.addCallbacks(self._send_message(*args), self._show_error(*args))
    
    def _send_message(self, target, nick=None):
        def callback(msg):
            if nick:
                msg = '%s, %s' % (nick, msg)
            self.msg(target, msg)
        return callback
    
    def _show_error(self, target, nick=None):
        def errback(f):
            msg = f.getErrorMessage()
            if nick:
                msg = '%s, %s' % (nick, msg)
            self.msg(target, msg)
            return f
        return errback
    
    def command_ping(self, rest):
        return 'Pong.'
    
    def command_saylater(self, rest):
        when, _, msg = rest.partition(' ')
        when = int(when)
        d = defer.Deferred()
        # A small example of how to defer the reply from a command. callLater
        # will callback the Deferred with the reply after so many seconds.
        reactor.callLater(when, d.callback, msg)
        # Returning the Deferred here means that it'll be returned from 
        # maybeDeferred in privmsg.
        return d
    
    def command_pagetitle(self, url):
        d = getPage(url)
        # Another example of using Deferreds. twisted.web.client.getPage returns
        # a Deferred which is called back when the URL requested has been 
        # downloaded. We add a callback to the chain which will parse the page
        # title out of the returned page. Without the following line, this 
        # function would still work, but the reply would be the entire contents
        # of the page. 
        d.addCallback(self._parse_pagetitle, url)
        return d
    
    def _parse_pagetitle(self, page, url):
        # Yank the page title from a string containing HTML data. BeautifulSoup
        # only parses the <head> tag from the HTML and returns that.
        head_tag = BeautifulSoup.SoupStrainer('head')
        soup = BeautifulSoup.BeautifulSoup(page, 
            parseOnlyThese=head_tag, convertEntities=['html', 'xml'])
        if soup.title is None:
            return '%s -- no title found' % url
        # Since BeautifulSoup gives you unicode and unicode data must be encoded
        # to send over the wire, we have to encode the title. Sadly IRC predates
        # unicode, so there's no formal way of specifying the encoding of data
        # transmitted over IRC. UTF-8 is our best bet, and what most people use.
        title = unicode(soup.title.string).encode('utf-8')
        # Since we're returning this value from a callback, it will be passed in
        # to the next callback in the chain.
        return '%s -- "%s"' % (url, title)
    
    def command_calc(self, rest):
        # RPN calculator! This is way simpler to implement than anything that
        # uses infix notation.
        stack = []
        for tok in rest.split():
            if tok in calc_operators:
                n_pops, func = calc_operators[tok]
                args = [stack.pop() for x in xrange(n_pops)]
                args.reverse()
                stack.append(func(*args))
            elif '.' in tok:
                stack.append(float(tok))
            else:
                stack.append(int(tok))
        result = str(stack.pop())
        if stack:
            result += ' (warning: %d item(s) left on stack)' % len(stack)
        return result

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