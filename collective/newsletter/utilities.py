from zope.interface import implements
from persistent.list import PersistentList

from collective.newsletter.interfaces import IMailingListManager

from OFS.SimpleItem import SimpleItem

class MailingListManager(SimpleItem):
    implements(IMailingListManager)

    def __init__(self):
        self.mailinglists = PersistentList()
        self.id_seed = 0

    def add(self, name, email, protocol):
        self.id_seed += 1
        self.mailinglists.append({'id': self.id_seed,
                                  'name': name,
                                  'email': email,
                                  'protocol': protocol})

    @property
    def protocols(self):
        return [{'id': 'mailman',
                 'name': 'Mailman'},
                {'id': 'google_groups',
                 'name': 'Google Groups'}]
