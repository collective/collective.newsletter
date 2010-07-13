from p4a.plonenewsletter import utilities, interfaces, GLOBALS
from p4a.common import site

from Products.CMFCore import utils as cmfutils
from Products.Archetypes.Extensions import utils as atutils

from StringIO import StringIO

EXTENSION_PROFILE = 'p4a.plonenewsletter:default'

def setup_portal(portal):
    site.ensure_site(portal)

def _cleanup_utilities(site):
    raise NotImplementedError('Current ISiteManager support does not '
                              'include ability to clean up')

def uninstall(portal):
    pc = cmfutils.getToolByName(portal, 'portal_controlpanel')
    pc.unregisterConfiglet('Plone4ArtistsNewsletterConfig')
