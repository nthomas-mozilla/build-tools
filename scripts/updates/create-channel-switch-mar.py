#
## repack_nightly_mar.py
#
# for channel switching, requires python 2.7+, wget, mar utility

import logging
from os import path, makedirs, walk, getcwd, chdir
from shutil import rmtree, copytree
import site
import subprocess
import sys
import urllib

site.addsitedir(path.join(path.dirname(__file__), "../../lib/python"))
site.addsitedir(path.join(path.dirname(__file__), "../../lib/python/vendor"))

import requests
#from release.updates.snippets import createSnippet, getSnippetPaths

MAR_URL = "http://stage.mozilla.org/pub/mozilla.org/firefox/nightly/%(dir)s/firefox-%(version)s.%(locale)s.%(platform)s.complete.mar"
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
WORKDIR = 'working'
WORKDIR_NEW_FILES = path.join(WORKDIR, 'new_files')
WORKDIR_UNPACK = path.join(WORKDIR, 'unpacked')
WORKDIR_MAR = path.join(WORKDIR, 'upload', 'ftp')
WORKDIR_SNIPPETS = path.join(WORKDIR, 'upload', 'snippets')

def setup_newfiles(channel, mac=False):
    makedirs(WORKDIR_NEW_FILES)
    log.info('Creating defaults/pref/channel-prefs.js')
    makedirs(path.join(WORKDIR_NEW_FILES, 'defaults', 'pref'))
    f = open(path.join(WORKDIR_NEW_FILES, 'defaults', 'pref', 'channel-prefs.js'), 'w')
    f.write('pref("app.update.channel", "%s");\n' % channel)
    f.close()
    log.info('Creating update-settings.ini')
    f = open(path.join(WORKDIR_NEW_FILES, 'update-settings.ini'), 'w')
    f.write(
"""; If you modify this file updates may fail.
; Do not modify this file.

[Settings]
ACCEPTED_MAR_CHANNEL_IDS=%s
""" % CHANNEL_INFO[channel]['channel_id'])
    f.close()

    if mac:
        log.info('Duplicating for silly old mac')
        copytree(WORKDIR_NEW_FILES, path.join(WORKDIR_NEW_FILES, 'Contents', 'MacOS'))

    new_files = []
    for root, dir, files in walk(WORKDIR_NEW_FILES):
        for f in files:
            new_files.append( path.join(root, f)[len(WORKDIR_NEW_FILES)+1:])

    return sorted(new_files, reverse=True)

def bzipFile(file):
    return file

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

def constructUrl(channel, locale, platform, version):
    log.debug('Generating url for (%s,%s,%s)' % (channel, locale, platform))
    url = MAR_URL % {
        'dir': CHANNEL_INFO[channel]['dir'],
        'version': version,
        'locale': locale,
        'platform': platform,
    }
    log.debug('returning %s' % url)
    return url

def download_file(url, dest=WORKDIR):
    log.info('Downloading %s' % url)
    dest_dir = path.dirname(dest)
    if not path.exists(dest_dir):
        makedirs(dest_dir)
    urllib.urlretrieve(url, dest)
    return dest

def unpack_mar(file):
    # files are still bzip compressed
    log.info('Unpacking %s' % file)
    file = path.abspath(file)
    cwd = getcwd()
    chdir(WORKDIR_UNPACK)
    p = subprocess.check_output(['mar', '-x', file], stderr=subprocess.STDOUT)
    chdir(cwd)
    return

def modify_manifest(new_files):
    # one, or both of these ?
    log.info('Parsing %s' % 'uhhhhhh')
    log.info('Adding new files')
    return ['baz', 'boop']

def getFileList():
    pass

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
    mar_url = constructUrl(args.to_channel, locale, platform, args.to_version)
    mar_file = download_file(mar_url, dest=path.join(WORKDIR, 'download', path.basename(mar_url)))
    if path.exists(WORKDIR_UNPACK):
        rmtree(WORKDIR_UNPACK)
    copytree(WORKDIR_NEW_FILES, WORKDIR_UNPACK)
    unpack_mar(mar_file)
    return
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

    if path.exists(WORKDIR):
        log.debug('Removing workdir %s' % path.abspath(WORKDIR))
        rmtree(WORKDIR)
    #makedirs(WORKDIR_SNIPPETS)
    #makedirs(WORKDIR_MAR)

    args.from_version  = getVersion(args.from_channel)
    args.to_version = getVersion(args.to_channel)
    new_files = setup_newfiles(args.to_channel, mac=True)

    for locale in args.locale:
        for platform in args.platform:
            log.info('Working on %s, %s' % (locale, platform))
            repack_mar(locale, platform, new_files)

    log.info("All done.")
    