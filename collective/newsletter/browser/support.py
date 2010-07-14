from zope import interface

from Products.Five.browser import BrowserView

from collective.newsletter.interfaces import IPossibleNewsletter
from collective.newsletter.interfaces import INewsletterEnhanced

from Products.statusmessages.interfaces import IStatusMessage
from collective.newsletter import MsgFact as _

class NewsletterEnhancementToggleView(BrowserView):

    # merged functionality with p4a.common.feature.FeatureProperty
    def get_newsletter_state(self):
        if IPossibleNewsletter.providedBy(self.context):
            return INewsletterEnhanced.providedBy(self.context)
        return False
    def set_newsletter_state(self, state):
        if IPossibleNewsletter.providedBy(self.context):
            ifaces = interface.directlyProvidedBy(self.context)
            if state and not INewsletterEnhanced.providedBy(self.context):
                interface.alsoProvides(self.context, INewsletterEnhanced)
            elif not state and INewsletterEnhanced in ifaces:
                interface.directlyProvides(self.context, ifaces - INewsletterEnhanced)
    newsletter_activated = property(get_newsletter_state, set_newsletter_state)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.messages = IStatusMessage(self.request)


    def __call__(self):
        was_activated = self.newsletter_activated
        self.newsletter_activated = not was_activated

        if was_activated:
            msgid = _(u"newsletter_disabled",
                      default="Newsletter functionality disabled.")
        else:
            msgid = _(u"newsletter_enabled",
                      default="Newsletter functionality enabled.")

        translated = self.context.translate(msgid)
        self.messages.addStatusMessage(translated, type="info")

        response = self.request.response
        response.redirect(self.context.absolute_url())

class Support(object):
    """A view that returns certain information regarding newsletter status."""
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def can_activate(self):
        return not INewsletterEnhanced.providedBy(self.context)

    @property
    def can_deactivate(self):
        return INewsletterEnhanced.providedBy(self.context)
