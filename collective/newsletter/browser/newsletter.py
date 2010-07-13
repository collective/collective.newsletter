from stoneagehtml import compactify
from collective.newsletter.browser.utils import relative_to_absolute_url_transform, escape_to_entities

from collective.newsletter.interfaces import IMailingListManager
from collective.newsletter.interfaces import IMailingList

from Products.Five.browser import BrowserView
from Products.Five.browser import pagetemplatefile

from zope.schema.interfaces import ValidationError
from zope.component import getUtility, getAdapter

from Products.CMFCore.utils import getToolByName

from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault

from lxml import etree
from StringIO import StringIO

class DefaultNewsletterRenderer(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get_rendered_snippet(self, element_id):
        rendered_html = self.get_rendered_template()
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(rendered_html), parser)
        part = tree.xpath('//*[@id="' + element_id + '"]')
        if len(part) > 0:
            result = etree.tostring(part[0], pretty_print=True, method="html")
            return result
        return None

    def get_rendered_template(self):
        # TODO: may get template via multiadapter-lookup to get the correctly
        #       zcml registered template?
        # TODO: has base_url to be changed this: like base_url here/absolute_url
        #       like in newsletter_wrapper.pt
        return getattr(self.context,
                       self.getTargetObjectLayout(self.context), None)()

    def __call__(self):
        plone_view = self.context.restrictedTraverse('@@plone')

        portal_url = getToolByName(self.context, 'portal_url')()
        context_path = plone_view.getCurrentFolderUrl()

        return relative_to_absolute_url_transform(compactify(self.index()),
                                                  context_path,
                                                  portal_url)

    def test(self):
        return lambda a, b, c: a and b or c

    def getTargetObjectLayout(self, target):
        """
        Returns target object 'view' action page template
        """
        if ISelectableBrowserDefault.providedBy(target):
            return target.getLayout()
        else:
            return 'base_view'

class SendNewsletterView(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def manager(self):
        return getUtility(IMailingListManager, 'mailinglist_manager')

    def getListAPI(self, name):
        return getUtility(IMailingList, name)

    def getMailingLists(self):
        return self.manager.mailinglists

    def getMailingListById(self, list_id):
        for ml in self.getMailingLists():
            if str(ml['id']) == list_id:
                return ml

    def __call__(self):
        """
        Depending on mode-parameter, send newsletter to either a single
        recipient, the mailinglist or return a preview.

        If mode is not set, just display form.
        """

        #assert self.request['REQUEST_METHOD'] == 'POST'

        mode = self.request.get('mode', None)

        # MSN Hotmail and various older e-mail clients do not support UTF-8
        # We opt for latin-1 for the time being for maximum compatibility

        # encoding = getToolByName(self.context, 'plone_utils').getSiteEncoding()
        encoding = 'latin-1'
        self.request.response.setHeader('Content-Type', 'text/html;charset=%s' % encoding)

        renderer = self.context.restrictedTraverse('@@view-as-newsletter')

        if mode == 'preview':
            try:
                return renderer()
            except:
                # write traceback to the logfile
                import pdb, traceback, sys
                traceback.print_exc()
        try:
            title = self.context.title_or_id()

            if mode == 'single':
                email = self.request.get('email')
                self._send_newsletter(email, renderer, title=title, encoding=encoding)
                self.request.set('portal_status_message', 'Newsletter sent to a single recipient.')
            elif mode == 'send':
                list_id = self.request.get('list')
                ml = self.getMailingListById(list_id)

                email = ml['email']

                # set up unsubscription parameters
                api = self.getListAPI(ml['protocol'])
                transform, message, subject = api.unsubscribe()
                self.request['unsubscribe_email'] = transform(email)
                self.request['unsubscribe_message'] = message
                self.request['unsubscribe_subject'] = subject

                self._send_newsletter(email, renderer, title=title, encoding=encoding)
                self.request.set('portal_status_message', 'Newsletter sent.')
        except ValidationError:
            message = self.context.translate(
                msgid='send_newsletter_validation_error',
                domain='collective.newsletter',
                default="Failed sending newsletter. Please verify email-address (you submitted '${email}').",
                mapping={'email': email})
            self.request.set('portal_status_message', message)
        except:
            message = self.context.translate(
                msgid='send_newsletter_failed',
                domain='collective.newsletter',
                default="Failed sending newsletter. We're unable to process your request due to an internal error. If the problem persists, please contact the site administrator.")
            self.request.set('portal_status_message', message)

            # write traceback to the logfile
            import pdb, traceback, sys
            traceback.print_exc()

        return self.index()

    def _send_newsletter(self, email, renderer, title='', encoding=None):
        """Send newsletter using template."""

        context = self.context

        # validate e-mail address
        reg_tool = getToolByName(context, 'portal_registration')
        if not (email and reg_tool.isValidEmail(email)):
            raise ValidationError

        site_properties = getToolByName(context, 'portal_properties').site_properties

        # setup email parameters
        send_from_address = '"%s" <%s>' % (site_properties.email_from_name, site_properties.email_from_address)

        subject = title

        # set encoding
        site_encoding = getToolByName(self.context, 'plone_utils').getSiteEncoding()
        if not encoding:
            encoding = site_encoding

        message = renderer().decode(site_encoding)

        # convert special characters to HTML entities
        message = escape_to_entities(message)

        # recode
        message = message.encode(encoding)

        # general parameters
        send_to_address = email.encode(encoding)

        # send mail
        host = self.context.MailHost

        result = host.secureSend(message,
                                 send_to_address,
                                 send_from_address,
                                 subject=subject,
                                 subtype='html',
                                 charset=encoding,
                                 debug=False,
                                 From=send_from_address)

class NewsletterConfig(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        submitted = self.request.get('form.submitted')

        if submitted == 'add':
            # add new mailinglist
            name = self.request.get('name', None)
            email = self.request.get('email', None)
            protocol = self.request.get('protocol', None)

            if name and email and protocol:
                self.addMailingList(name, email, protocol)
            else:
                self.request.set('portal_status_message',
                                 'Could not add new mailing list. Please fill out all fields.')
        if submitted == 'remove':
            lists = self.request.get('remove', [])
            for list_id in lists:
                self.removeMailingList(list_id)

        return self.index()

    @property
    def manager(self):
        return getUtility(IMailingListManager, 'mailinglist_manager')

    def getMailingLists(self):
        return self.manager.mailinglists

    def addMailingList(self, name, email, protocol):
        self.manager.add(name, email, protocol)

    def removeMailingList(self, list_id):
        self.manager.mailinglists = filter(lambda l: str(l['id']) != list_id,
                                           self.manager.mailinglists)

    def getProtocols(self):
        return self.manager.protocols

