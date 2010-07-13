from zope import component
from zope import interface
from zope import schema

from Products.Five.browser import BrowserView

from collective.newsletter.interfaces import IPossibleNewsletter
from collective.newsletter.interfaces import INewsletterEnhanced

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

    def __call__(self):
        was_activated = self.newsletter_activated
        self.newsletter_activated = not was_activated

        if was_activated:
            msg = 'Newsletter functionality disabled.'
        else:
            msg = 'Newsletter functionality enabled.'

        response = self.request.response
        response.redirect(self.context.absolute_url() + \
                          "/view?portal_status_message=%s" % msg)

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
