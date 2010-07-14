# -*- coding: utf-8 -*-
#
# GNU General Public License (GPL)
#
__author__ = """Johannes Raggam <johannes@raggam.co.at>"""
__docformat__ = 'plaintext'

from zope.formlib import form
from zope.interface import implements
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from collective.newsletter import MsgFact as _

class ISubscriptionPortlet(IPortletDataProvider):
    pass

class Assignment(base.Assignment):
    implements(ISubscriptionPortlet)

    @property
    def title(self):
        return _(u"Newsletter Subscription Portlet")

class AddForm(base.NullAddForm):
    form_fields = form.Fields(ISubscriptionPortlet)
    label = _(u"Add Newsletter Subscription Portlet")
    description = _(u"This portlet allows subscription to newsletters.")
    def create(self):
        return Assignment()

class Renderer(base.Renderer):
    render = ViewPageTemplateFile('subscription_portlet.pt')
