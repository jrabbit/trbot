from StringIO import StringIO

from oice.langdet import langdet
from oice.langdet import streams
from oice.langdet import languages

def isEnglish(text_orig):
    text = streams.Stream(StringIO(text_orig))
    lang = langdet.LanguageDetector.detect(text)
    if lang == languages.english:
        return True
    else:
        return False