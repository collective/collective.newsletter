# -*- coding: utf-8 -*-
#
# GNU General Public License (GPL)
#
from zope.component import getMultiAdapter
from zope.component import ComponentLookupError

from stoneagehtml import compactify
from collective.newsletter.browser import utils

from collective.newsletter.interfaces import IMailingListManager
from collective.newsletter.interfaces import IMailingList

from Products.Five.browser import BrowserView

from zope.schema.interfaces import ValidationError

from Products.CMFCore.utils import getToolByName

from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault

from lxml import etree
from StringIO import StringIO

from Products.statusmessages.interfaces import IStatusMessage
from collective.newsletter import MsgFact as _
import logging
logger = logging.getLogger('collective.newsletter')

class DefaultNewsletterRenderer(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        #self.encoding = getToolByName(self.context,
        #                              'plone_utils').getSiteEncoding()
        # play it safe - and ignore chars outside unicodeverse
        self.encoding = 'ascii'

    @property
    def stylesheets(self):
        # TODO: don't make use of yield cause that's not cacheable
        # TODO: check why css ++resources cant got inline in POST MODE
        #       AttributeError: 'DirContainedFileResource6' object has no
        #                        attribute 'POST'
        #       Products.ResourceRegistries.CssRegistry
        #       Products.ResourceRegistries.BaseRegistry
        portal_css = getToolByName(self.context, 'portal_css')
        stylesheets = portal_css.getEvaluatedResources(self.context)
        for stylesheet in stylesheets:
            try:
                stylesheet_info = {}
                # encode stylesheet according to site's encoding and ignore
                # gracefully any encoding errors
                stylesheet_info['styles'] = str(
                    portal_css.getInlineResource(stylesheet.getId(),
                                                 self.context).encode(
                                                     self.encoding, 'ignore'))
                get_media = getattr(stylesheet, 'getMedia', None)
                stylesheet_info['media'] = get_media and get_media() or 'screen'
                get_rendering = getattr(stylesheet, 'getRendering', None)
                stylesheet_info['rendering'] = get_rendering and\
                               get_rendering() or 'link'
                yield stylesheet_info
            except AttributeError as detail:
                logger.error("AttributeError: " + str(detail))
                logger.error("failed stylesheet: " + stylesheet.getId())
            except UnicodeEncodeError as detail:
                logger.error("UnicodeEncodeError: " + str(detail))
                logger.error("failed stylesheet: " + stylesheet.getId())

    @property
    def newsletter_css(self):
        ccss = self.context.restrictedTraverse('++resource++collective_newsletter.css')
        # also see Products.ResourceRegistries.tools.BaseRegistry.BaseRegistryTool.getResourceContent
        ### NO! due to redirection, there is some magic involved,
        ### so that only an empty string is returned
        # return ccss.browserDefault(self.request)[0]()
        fileobj = open(ccss.context.path)
        data = fileobj.read()
        fileobj.close()
        return data

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
        # TODO: has base_url to be changed this: like base_url here/absolute_url
        #       like in newsletter_wrapper.pt
        view_name = self.get_target_object_layout(self.context)

        try:
            view = getMultiAdapter((self.context, self.request), name=view_name)
        except ComponentLookupError:
            view = getattr(self.context, view_name, None)

        return view()

    def __call__(self):
        plone_view = self.context.restrictedTraverse('@@plone')

        portal_url = getToolByName(self.context, 'portal_url')()
        context_path = plone_view.getCurrentFolderUrl()

        return utils.relative_to_absolute_url_transform(
            compactify(self.index(), media=(u'screen',u'print',)),
                context_path, portal_url)

    def get_target_object_layout(self, target):
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
        self.messages = IStatusMessage(self.request)
        self.mailinglist_manager = utils.get_mailinglist_manager()
        self.mailinglists = self.mailinglist_manager.mailinglists

    def __call__(self):
        """
        Depending on mode-parameter, send newsletter to either a single
        recipient, the mailinglist or return a preview.

        If mode is not set, just display form.
        """

        ## POST DOES NOT WORK WITH CSS FILES AS BROWSER RESOURCES
        ## so we have to use get instead
        #assert self.request['REQUEST_METHOD'] == 'POST'

        mode = self.request.get('mode', None)

        # MSN Hotmail and various older e-mail clients do not support UTF-8
        # We opt for latin-1 for the time being for maximum compatibility

        # encoding = getToolByName(self.context,
        #                          'plone_utils').getSiteEncoding()
        encoding = 'latin-1'
        self.request.response.setHeader('Content-Type', 'text/html;charset=%s'
                                        % encoding)

        if mode == 'preview':
            self.request.response.redirect('@@view-as-newsletter')
        try:
            renderer = self.context.restrictedTraverse('@@view-as-newsletter')
            title = self.context.title_or_id()

            if mode == 'single':
                email = self.request.get('email')
                self._send_newsletter(email,
                                      renderer,
                                      title=title,
                                      encoding=encoding)

                msgid = _(u"newsletter_sent_single",
                          default=u"Newsletter sent to a single recipient.")
                translated = self.context.translate(msgid)
                self.messages.addStatusMessage(translated, type="info")

            elif mode == 'send':
                list_id = self.request.get('list')
                mlist = self.mailinglist_manager.get_mailinglist_by_id(list_id)
                email = mlist['email']

                # set up unsubscription parameters
                api = utils.get_list_api(mlist['protocol'])
                unsubscribe_email, message, subject = api.unsubscribe(email)
                self.request['unsubscribe_email'] = unsubscribe_email
                self.request['unsubscribe_message'] = message
                self.request['unsubscribe_subject'] = subject

                self._send_newsletter(email,
                                      renderer,
                                      title=title,
                                      encoding=encoding)

                msgid = _(u"newsletter_sent",
                          default=u"Newsletter sent.")
                translated = self.context.translate(msgid)
                self.messages.addStatusMessage(translated, type="info")

        except ValidationError:
            msgid = _(u"send_newsletter_validation_error",
                default=u"Failed sending newsletter. Please verify\
                email-address (you submitted '${email}.",
                mapping={u'email': email})
            translated = self.context.translate(msgid)
            self.messages.addStatusMessage(translated, type="error")
        except:
            msgid = _(u"send_newsletter_failed",
                default="Failed sending newsletter. We're unable to process\
                your request due to an internal error. If the problem persists,\
                please contact the site administrator.")
            translated = self.context.translate(msgid)
            self.messages.addStatusMessage(translated, type="error")

            # write traceback to the logfile
            import traceback
            traceback.print_exc()

        return self.index()

    def _send_newsletter(self, email, renderer, title='', encoding=None):
        """Send newsletter using template."""

        context = self.context

        # validate e-mail address
        reg_tool = getToolByName(context, 'portal_registration')
        if not (email and reg_tool.isValidEmail(email)):
            raise ValidationError

        site_properties = getToolByName(context,
                                        'portal_properties').site_properties
        if not (site_properties.email_from_name and
                site_properties.email_from_address and
                reg_tool.isValidEmail(site_properties.email_from_address)):
            raise ValidationError

        # setup email parameters
        send_from_address = '"%s" <%s>' % (site_properties.email_from_name,
                                           site_properties.email_from_address)

        subject = title

        # set encoding
        site_encoding = getToolByName(self.context,
                                      'plone_utils').getSiteEncoding()
        if not encoding:
            encoding = site_encoding

        message = renderer().decode(site_encoding)

        # convert special characters to HTML entities
        message = utils.escape_to_entities(message)

        # recode
        message = message.encode(encoding)

        # general parameters
        send_to_address = email.encode(encoding)

        # send mail
        host = self.context.MailHost
        host.send(message,
                subject=subject,
                mto=send_to_address,
                mfrom=send_from_address,
                charset=encoding,
                msg_type='text/html')


class NewsletterConfig(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.messages = IStatusMessage(self.request)
        self.mailinglist_manager = utils.get_mailinglist_manager()
        self.mailinglists = self.mailinglist_manager.mailinglists
        self.protocols = self.mailinglist_manager.protocols

    def __call__(self):
        submitted = self.request.get('form.submitted')

        if submitted == 'add':
            # add new mailinglist
            name = self.request.get('name', None)
            email = self.request.get('email', None)
            protocol = self.request.get('protocol', None)

            if name and email and protocol:
                self.mailinglist_manager.add(name, email, protocol)
            else:
                msgid = _(u"config_add_mailinglist_failed",
                    default="Could not add new mailing list. Please fill out\
                    all fields.")
                translated = self.context.translate(msgid)
                self.messages.addStatusMessage(translated, type="error")

        if submitted == 'remove':
            lists = self.request.get('remove', [])
            for list_id in lists:
                self.mailinglist_manager.remove(list_id)

        return self.index()
