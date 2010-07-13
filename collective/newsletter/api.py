from zope.interface import implements

from collective.newsletter.interfaces import IMailingList

def insert_before(s, char, string):
    return (string+char).join(s.split(char))

class Mailman(object):
    implements(IMailingList)

    def subscribe(self):
        return (lambda email: insert_before(email, '@', '-request'),
                u'subscribe',
                u'subscribe')

    def unsubscribe(self):
        return (lambda email: insert_before(email, '@', '-request'),
                u'unsubscribe',
                u'unsubscribe')

class GoogleGroups(object):
    implements(IMailingList)

    def subscribe(self):
        return (lambda email: insert_before(email, '@', '-subscribe'),
                u'subscribe',
                u'Subscription Request')

    def unsubscribe(self):
        return (lambda email: insert_before(email, '@', '-unsubscribe'),
                u'unsubscribe',
                u'Subscription Cancellation Request')

