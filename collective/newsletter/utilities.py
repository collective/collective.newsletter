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

    def remove(self, list_id):
        self.mailinglists = filter(lambda l: str(l['id']) != list_id,
                                   self.mailinglists)

    def get_mailinglist_by_id(self, list_id):
        for mlist in self.mailinglists:
            if str(mlist['id']) == list_id:
                return mlist
        return None

    @property
    def protocols(self):
        return [{'id': 'mailman',
                 'name': 'Mailman'},
                {'id': 'google_groups',
                 'name': 'Google Groups'},
                {'id': 'sympa',
                 'name': 'Sympa'}]
