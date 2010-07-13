from zope import component
from zope import interface
from zope import schema

from Products.Five.browser import BrowserView

from collective.newsletter import interfaces
from p4a.common import feature

_marker = object()

class NewsletterEnhancementToggleView(BrowserView):
    _newsletter_activated = feature.FeatureProperty(
        interfaces.IPossibleNewsletter,
        interfaces.INewsletterEnhanced,
        'context')

    def newsletter_activated(self, v=_marker):
        if v is _marker:
            if interfaces.IPossibleNewsletter.providedBy(self.context):
                return self._newsletter_activated
            return False

        if interfaces.IPossibleNewsletter.providedBy(self.context):
            self._newsletter_activated = v

    newsletter_activated = property(newsletter_activated, newsletter_activated)

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
        return not interfaces.INewsletterEnhanced.providedBy(self.context)

    @property
    def can_deactivate(self):
        return interfaces.INewsletterEnhanced.providedBy(self.context)
