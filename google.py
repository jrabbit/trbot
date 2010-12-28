import re
import htmlentitydefs

def _fixer(match, _htmlentitymap=htmlentitydefs.name2codepoint):
    entity = match.group(1)
    result = _htmlentitymap.get(entity)
    if not result:
        result = int(entity)
    return unichr(result)
    
def fixGoogleText(text, _fixer=_fixer, 
        _re_xmlentities=re.compile(ur'\&\#?(\w+|\d{2});', re.UNICODE)):
    return _re_xmlentities.sub(_fixer, text)