from zope.interface import Interface
from zope.schema.interfaces import ValidationError

from Products.Five.browser import BrowserView

from collective.newsletter.interfaces import IMailingListManager
from collective.newsletter.interfaces import IMailingList

from Products.CMFCore.utils import getToolByName

from collective.newsletter.browser import utils

from Products.statusmessages.interfaces import IStatusMessage
from collective.newsletter import MsgFact as _

class INewsletterSubscriptionView(Interface):
    pass

class NewsletterSubscriptionView(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.messages = IStatusMessage(self.request)
        self.mailinglist_manager = utils.get_mailinglist_manager()
        self.mailinglists = self.mailinglist_manager.mailinglists

    def subscribe(self):
        # TODO: in status messages, give a hint to which newsletters the user
        #       subscribed
        email = self.request.get('subemail', None)
        unsubscribe = self.request.get('unsubscribe', None) and True or False
        
        selected_lists = self.request.get('mailinglists', None)
        
        if len(self.mailinglists) == 1:
            # self.mailinglists is persistent list
            selected_lists = self.mailinglists
        else:
            if selected_lists\
               and not isinstance(selected_lists, list)\
               and not isinstance(selected_lists, tuple):
                selected_lists = [selected_lists]

        if selected_lists:
            for selected_list in selected_lists:
                selected_list_info = self.mailinglist_manager.\
                                   get_mailinglist_by_id(selected_list['id'])
                api = utils.get_list_api(selected_list_info['protocol'])
                if not unsubscribe:
                    try:
                        self._subscribe(email, selected_list_info['email'], api)
                        msgid = _(u"newsletter_signup_successful",
                            default="You've successfully subscribed to the list.")
                        msgtype = "info"
                    except ValidationError:
                        msgid = _(u"newsletter_signup_validation_error",
                            default="Signup failed. Please verify email-address\
                            (you submitted '${subemail}').",
                            mapping={u'subemail': email})
                        msgtype = "error"
                    except:
                        msgid = _(u"newsletter_signup_failed",
                            default="Signup failed. We're unable to process your\
                            request due to an internal error. If the problem\
                            persists, please contact the site administrator.")
                        msgtype = "error"
                        # write traceback to the logfile
                        import traceback
                        traceback.print_exc()
                else:
                    try:
                        self._unsubscribe(email, selected_list_info['email'], api)
                        msgid = _(u"newsletter_signoff_successful",
                            default="You've successfully unsubscribed from the\
                            list.")
                        msgtype = "info"
                    except ValidationError:
                        msgid = _(u"newsletter_signoff_validation_error",
                            default="Sigoff failed. Please verify email-address\
                            (you submitted '${subemail}').",
                            mapping={'subemail': email})
                        msgtype = "error"
                    except:
                        msgid = _(u"newsletter_signoff_failed",
                            default="Signoff failed. We're unable to process your\
                            request due to an internal error. If the problem\
                            persists, please contact the site administrator.")
                        msgtype = "error"
                        # write traceback to the logfile
                        import traceback
                        traceback.print_exc()

                translated = self.context.translate(msgid)
                self.messages.addStatusMessage(translated, type=msgtype)

        if not selected_lists:
            msgid = _(u"newsletter_no_selected_list",
                      default="Please select a newsletter.")
            msgtype = "error"
            translated = self.context.translate(msgid)
            self.messages.addStatusMessage(translated, type=msgtype)


        came_from = self.request.get('came_from', self.context.absolute_url())
        self.request.RESPONSE.redirect(came_from)

    def _subscribe(self, email, listemail, api):
        """Register signup with mailing list.
        """
        send_to_address, message, subject = api.subscribe(listemail)
        self._send_request(email, subject, message, send_to_address)

    def _unsubscribe(self, email, listemail, api):
        """Register signup with mailing list.
        """
        send_to_address, message, subject = api.unsubscribe(listemail)
        self._send_request(email, subject, message, send_to_address)

    def _send_request(self, email, subject, message, send_to_address):
        """Send a subscription request to the list.
        """
        # validate e-mail address
        reg_tool = getToolByName(self.context, 'portal_registration')
        if not (email and reg_tool.isValidEmail(email)):
            raise ValidationError

        # set encoding
        encoding = 'utf-8'

        # setup email parameters
        send_from_address = email
        envelope_from = '"%s" <%s>' % (send_from_address, send_from_address)

        # send mail
        host = self.context.MailHost
        host.send(message.encode(encoding),
                           subject=subject.encode(encoding),
                           mto=send_to_address.encode(encoding),
                           mfrom=envelope_from.encode(encoding),
                           charset=encoding,
                           msg_type='text/plain')