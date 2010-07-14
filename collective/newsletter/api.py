from zope.interface import implements

from collective.newsletter.interfaces import IMailingList

def insert_before(s, char, string):
    return (string+char).join(s.split(char))

def listname(email):
    return email.split('@')[0]

class Mailman(object):
    implements(IMailingList)

    def subscribe(self, listemail):
        return (insert_before(listemail, '@', '-request'),
                u'subscribe',
                u'subscribe')

    def unsubscribe(self, listemail):
        return (insert_before(listemail, '@', '-request'),
                u'unsubscribe',
                u'unsubscribe')

class GoogleGroups(object):
    implements(IMailingList)

    def subscribe(self, listemail):
        return (insert_before(listemail, '@', '-subscribe'),
                u'subscribe',
                u'Subscription Request')

    def unsubscribe(self, listemail):
        return (insert_before(listemail, '@', '-unsubscribe'),
                u'unsubscribe',
                u'Subscription Cancellation Request')

class Sympa(object):
    implements(IMailingList)

    def subscribe(self, listemail):
        return (listemail,
                u'SUBSCRIBE ' + listname(listemail),
                u'SUBSCRIBE ' + listname(listemail))

    def unsubscribe(self, listemail):
        return (listemail,
                u'SIGNOFF ' + listname(listemail),
                u'SIGNOFF ' + listname(listemail))