import urllib2
import urllib
import json
# From http://www.dreamincode.net/forums/topic/198590-using-python-and-google-translate/
def fromAjax(text, languageFrom, languageTo):
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
    content=urllib2.urlopen(url).read()
    try: trans_dict=json.loads(content)
    except AttributeError:
        try: trans_dict=json.load(content)
        except AttributeError: trans_dict=json.read(content)
    return trans_dict['responseData']['translatedText']
