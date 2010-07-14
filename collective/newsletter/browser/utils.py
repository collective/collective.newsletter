from zope.component import getUtility

from BeautifulSoup import BeautifulSoup
import re
import htmlentitydefs

from collective.newsletter.interfaces import IMailingList, IMailingListManager

uri_exp = re.compile('^[a-zA-z]+:')

def get_mailinglist_manager():
    return getUtility(IMailingListManager, 'mailinglist_manager')

def get_list_api(name):
    return getUtility(IMailingList, name)


def make_absolute(url, base_url, root_url):
    if url.startswith('/'):
        return root_url + url

    if not uri_exp.match(url):
        return base_url + '/' + url

    return url

def relative_to_absolute_url_transform(html, base_url, root_url):
    soup = BeautifulSoup(html)

    for link in soup.findAll('a'):
        try:
            link['href'] = make_absolute(link['href'], base_url, root_url)
        except KeyError:
            pass

    for image in soup.findAll('img'):
        try:
            image['src'] = make_absolute(image['src'], base_url, root_url)
        except KeyError:
            pass

    return soup.prettify()



codepoint2entity = {}
safe_characters = ['<', '>', '"', '&']
for c in htmlentitydefs.codepoint2name:
    if c not in map(ord, safe_characters): # skip "safe" characters
        codepoint2entity[c] = '&%s;' % unicode(htmlentitydefs.codepoint2name[c])

def escape_to_entities(string):
    """Unicode to HTML entity-converter (neccesary for latin-1)."""

    ustr = string.translate(codepoint2entity)
    result = []
    for s in ustr:
        if ord(s) > 0x7f:
            s = '&#%d;' % ord(s)
        result.append(s)

    return "".join(result)
