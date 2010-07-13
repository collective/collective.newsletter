from p4a.plonenewsletter import utilities, interfaces, GLOBALS
from p4a.common import site

from Products.CMFCore import utils as cmfutils 
from Products.Archetypes.Extensions import utils as atutils

from StringIO import StringIO

EXTENSION_PROFILE = 'p4a.plonenewsletter:default'

def setup_portal(portal):
    site.ensure_site(portal)
    setup_site(portal)
    setup_gs_profile(portal)

    # install skin
    out = StringIO()
    atutils.install_subskin(portal, out, GLOBALS)

    # setup dependencies
    qi = cmfutils.getToolByName(portal, 'portal_quickinstaller')
    qi.installProducts(['CMFonFive'])

    # setup configlet
    pc = cmfutils.getToolByName(portal, 'portal_controlpanel')
    pc.registerConfiglet('Plone4ArtistsNewsletterConfig',
                         'Newsletter configuration',
                         'string:${portal_url}/newsletter-configuration',
                         '',
                         'Manage portal',
                         'Products',
                         1,
                         'Plone4ArtistsNewsletter',
                         '++resource++p4aplonenewsletter/newsletter_icon.gif',
                         'Configure mailinglists.',
                         None)

def setup_gs_profile(portal):
    setup_tool = cmfutils.getToolByName(portal, 'portal_setup')
    
    try:
        setup_tool.setImportContext('profile-%s' % EXTENSION_PROFILE)
        setup_tool.runAllImportSteps()
        # setup_tool.setImportContext('profile-%s' % EXTENSION_PROFILE)
    except Exception, e:
        print >> out, "error while trying to GS import %s (%s, %s)" \
              % (EXTENSION_PROFILE, repr(e), str(e))

def setup_site(site):
    sm = site.getSiteManager()

    if not sm.queryUtility(interfaces.IMailingListManager, name='mailinglist_manager'):
        try:
            sm.registerUtility(utilities.MailingListManager(),
                               provided=interfaces.IMailingListManager,
                               name='mailinglist_manager')
        except TypeError:
            # BBB for Five 1.4
            sm.registerUtility(interfaces.IMailingListManager,
                               utilities.MailingListManager(),
                               'mailinglist_manager')

            
def _cleanup_utilities(site):
    raise NotImplementedError('Current ISiteManager support does not '
                              'include ability to clean up')

def uninstall(portal):
    pc = cmfutils.getToolByName(portal, 'portal_controlpanel')
    pc.unregisterConfiglet('Plone4ArtistsNewsletterConfig')
