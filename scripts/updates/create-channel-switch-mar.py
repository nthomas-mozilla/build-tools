#
## repack_nightly_mar.py
#
# for channel switching, requires python 2.7+, wget, mar utility

import logging
from os import path, makedirs
from shutil import rmtree
import sys
import site

site.addsitedir(path.join(path.dirname(__file__), "../../lib/python"))
site.addsitedir(path.join(path.dirname(__file__), "../../lib/python/vendor"))

import requests
#from release.updates.snippets import createSnippet, getSnippetPaths

MAR_URL = "http://ftp.mozilla.org/pub/mozilla.org/firefox/nightly/%(dir)s/firefox-%(version)s.%(locale)s.%(platform)s.complete.mar"
CHANNEL_INFO = {
    'nightly':
        {
            'dir': 'latest-mozilla-central-l10n',
            'channel_id': 'firefox-mozilla-central',
            'version_url': 'http://hg.mozilla.org/mozilla-central/raw-file/default/browser/config/version.txt',
        },
    'aurora':
        {
            'dir': 'latest-mozilla-aurora-l10n',
            'channel_id': 'firefox-mozilla-aurora',
            'version_url': 'http://hg.mozilla.org/releases/mozilla-aurora/raw-file/default/browser/config/version.txt',
        }
}
WORKDIR = 'upload'
WORKDIR_SNIPPETS = path.join(WORKDIR, 'snippets')
WORKDIR_MAR = path.join(WORKDIR, 'ftp')

def setup_newfiles(channel, mac=False):
    log.info('Creating defaults/pref/channel-prefs.js')
    log.info('Creating update-settings.ini')
    if mac:
        log.info('Duplicating for silly old mac')
    return ['foo', 'bar']

def getVersion(channel):
    log.debug('Getting version for channel %s' % channel)
    try:
        url = CHANNEL_INFO[channel]['version_url']
        r = requests.get(url)
        r.raise_for_status()
        version = r.content.strip()
        return version
    except KeyError:
        log.error('Channel %s not setup, add it to CHANNEL_INFO' % channel)
        sys.exit(1)

def getUrl(channel, locale, platform, version):
    log.debug('Generating url for (%s,%s,%s)' % (channel, locale, platform))
    url = MAR_URL % {
        'dir': CHANNEL_INFO[channel]['dir'],
        'version': version,
        'locale': locale,
        'platform': platform,
    }
    log.debug('returning %s' % url)
    return url

def download_mar(url):
    log.info('Downloading %s' % url)
    # call wget, use requests ?
    return 'some-file'

def unpack_mar(file):
    log.info('Unpacking %s' % file)

def modify_manifest(new_files):
    # one, or both of these ?
    log.info('Parsing %s' % 'uhhhhhh')
    log.info('Adding new files')
    return ['baz', 'boop']

def create_mar(mar_file, files):
    log.info('Creating %s' % mar_file)
    # call out to mar
    if args.sign:
        log.info('Signing new mar')

def create_snippet(mar_file):
    log.info('Creating snippet for %s' % mar_file)
    # call snippet func we already have

def repack_mar(locale, platform, new_files):
    # create tmp dir
    mar_url = getUrl(args.to_channel, locale, platform, args.to_version)
    r = requests.head(mar_url)
    r.raise_for_status()
    return
    #mar_file = download_mar(mar_url)
    #unpack_mar(mar_file)
    #for f in new_files:
    #    log.info('Copying in %s' % f)
    #file_list = modify_manifest(new_files)
    #new_mar_file = os.path.join(UPLOAD_DIR, os.path.basename(mar_url))
    #create_mar(new_mar_file, file_list)
    #create_snippet(new_mar_file)
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--platform", dest="platform", action='append',
                        choices=['win32', 'mac', 'linux-i686', 'linux-x86_64'],
                        help="platform(s) to repack")
    parser.add_argument("-l", "--locale", dest="locale", 
                        action='append', required=True,
                        help="locale(s) to repack")
    parser.add_argument("-f", "--from-channel", default="nightly",
                        help="channel where the users are now")
    parser.add_argument("-t", "--to-channel", default="aurora",
                        help="repo where the users should be moved")
    parser.add_argument("-s", "--sign", action='store_true',
                        help="sign the mar file")
    parser.add_argument("-b", "--base-url",
                        default="http://ftp.mozilla.org/pub/mozilla.org/firefox/nightly/channel-switch/",
                        help="base url to host the mar files at")
#    parser.add_argument("-V", "--version", default="100.0",
#                        help="Version to sign file with")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="verbose messages")

    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(name)s.%(funcName)s#%(lineno)s: %(message)s")
    log = logging.getLogger()

    if args.sign:
        # get token
        # delete left over nonce
        pass

    args.from_version  = getVersion(args.from_channel)
    args.to_version = getVersion(args.to_channel)
    new_files = setup_newfiles(args.to_channel)

    if path.exists(WORKDIR):
        log.debug('Removing workdir' % path.abspath(WORKDIR))
        rmtree(WORKDIR)
    makedirs(WORKDIR_SNIPPETS)
    makedirs(WORKDIR_MAR)

    for locale in args.locale:
        for platform in args.platform:
            repack_mar(locale, platform, new_files)
        
    