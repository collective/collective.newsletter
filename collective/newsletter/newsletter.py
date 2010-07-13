from zope import component
from zope import interface
from zope.annotation import interfaces as annointerfaces
from collective.newsletter import interfaces

from Products.ATContentTypes.content import base

class NewsletterConfig(object):
    """An INewsletterConfig adapter for Archetypes content."""

    interface.implements(interfaces.INewsletterConfig)
    component.adapts(interfaces.IPossibleNewsletter)

    def __init__(self, context):
        self.context = context

    def __get_newsletter_activated(self):
        return interfaces.INewsletterEnhanced.providedBy(self.context) and \
               annointerfaces.IAttributeAnnotatable.providedBy(self.context)

    def __set_newsletter_activated(self, activated):
        ifaces = interface.directlyProvidedBy(self.context)
        if activated:
            if not interfaces.INewsletterEnhanced.providedBy(self.context):
                ifaces += interfaces.INewsletterEnhanced
            if not annointerfaces.IAttributeAnnotatable.providedBy(self.context):
                ifaces += annointerfaces.IAttributeAnnotatable
        else:
            if interfaces.INewsletterEnhanced in ifaces:
                ifaces -= interfaces.INewsletterEnhanced

        interface.directlyProvides(self.context, ifaces)

    newsletter_activated = property(__get_newsletter_activated,
                                  __set_newsletter_activated)
