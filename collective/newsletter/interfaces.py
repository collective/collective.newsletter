from zope import interface
from zope import schema
from collective.newsletter import MsgFact as _

class IPossibleNewsletter(interface.Interface):
    """A marker interface for representing what *could* be a newsletter.
    """

class INewsletterEnhanced(interface.Interface):
    """A marker interface to indicate an item that has newsletter
    functionality.
    """

class IBasicNewsletterSupport(interface.Interface):
    """Provides certain information about newsletter support."""

    can_activate = schema.Bool(title=u'Can activate newsletter?',
                               required=True,
                               readonly=True)

    can_deactivate = schema.Bool(title=u'Can deactivate newsletter?',
                                 required=True,
                                 readonly=True)

class IMailingListManager(interface.Interface):
    mailinglists = schema.Iterable(
        title=(u"Mailinglists"),
        description=_(u"Available mailinglists"),
        )
    protocols = schema.Iterable(
        title=(u"Mailinglist protocols"),
        description=_(u"Available mailinglist protocols"),
        )
    def add(name, email, protocol):
        pass
    def remove(list_id):
        pass
    def get_mailinglist_by_id(list_id):
        pass

class IMailingList(interface.Interface):
    def subscribe(listemail, subemail):
        pass

    def unsubscribe(listemail, subemail):
        pass
