from zope.interface import Interface
from zope.component import getUtility
from zope.schema.interfaces import ValidationError

from Products.Five.browser import BrowserView

from collective.newsletter.interfaces import IMailingListManager
from collective.newsletter.interfaces import IMailingList

from Products.CMFCore.utils import getToolByName

class INewsletterSubscriptionView(Interface):
    def getMailingLists():
        pass

class NewsletterSubscriptionView(BrowserView):
    @property
    def manager(self):
        return getUtility(IMailingListManager, 'mailinglist_manager')

    def getListAPI(self, name):
        return getUtility(IMailingList, name)

    def getMailingListById(self, list_id):
        for ml in self.getMailingLists():
            if str(ml['id']) == list_id:
                return ml

    def getMailingLists(self):
        return self.manager.mailinglists

    def subscribe(self):
        email = self.request.get('subemail', None)

        # get list api
        index = self.request['list']
        selected_list = self.getMailingListById(index)

        api = self.getListAPI(selected_list['protocol'])

        try:
            self._subscribe(email, selected_list['email'], api)
            message = self.context.translate(
                msgid='newsletter_signup_successful',
                domain='collective.newsletter',
                default="You've successfully subscribed to the list.")
        except ValidationError:
            message = self.context.translate(
                msgid='newsletter_signup_validation_error',
                domain='collective.newsletter',
                default="Signup failed. Please verify email-address (you submitted '${subemail}').",
                mapping={'subemail': email})
        except:
            message = self.context.translate(
                msgid='newsletter_signup_failed',
                domain='collective.newsletter',
                default="Signup failed. We're unable to process your request due to an internal error. If the problem persists, please contact the site administrator.")

            # write traceback to the logfile
            import pdb, traceback, sys
            traceback.print_exc()

        came_from = self.request.get('came_from', self.context.absolute_url())
        self.request.RESPONSE.redirect('%s?portal_status_message=%s' % (came_from, message))

    def _subscribe(self, email, send_to_address, api):
        """Register signup with mailing list."""

        transform, message, subject = api.subscribe()
        self._send_request(email, subject, message, transform(send_to_address), subscribe=True)

    def _send_request(self, email, subject, message, send_to_address, subscribe):
        """Send a subscription request to the list."""

        context = self.context

        # validate e-mail address
        reg_tool = getToolByName(context, 'portal_registration')
        if not (email and reg_tool.isValidEmail(email)):
            raise ValidationError

        site_properties = getToolByName(context, 'portal_properties').site_properties

        # set encoding
        encoding = 'utf-8'

        # setup email parameters
        send_from_address = email
        envelope_from = '"%s" <%s>' % (site_properties.email_from_name, site_properties.email_from_address)

        # send mail
        host = self.context.MailHost

        result = host.secureSend(message.encode(encoding),
                                 send_to_address.encode(encoding),
                                 envelope_from.encode(encoding),
                                 subject=subject.encode(encoding),
                                 subtype='plain',
                                 charset=encoding,
                                 debug=False,
                                 From=send_from_address.encode(encoding))
