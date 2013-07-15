from fabric.api import run
from fabric.context_managers import cd, hide, show
from fabric.operations import put
from fabric.colors import green, red
import paramiko
import re
import os
import sys
import inspect
import subprocess
import time

OK = green('[OK]')
FAIL = red('[FAIL]')

BUILDBOT_WRANGLER = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "../../../../buildfarm/maintenance/buildbot-wrangler.py"))


def get_actions():
    current_module = sys.modules[__name__]
    for name in dir(current_module):
        attr = getattr(current_module, name)
        if inspect.isfunction(attr) and name.startswith('action_'):
            yield name.replace('action_', '')


def action_check(master):
    """Checks that the master parameters are valid"""
    with hide('stdout', 'stderr', 'running'):
        date = run('date')
        run('test -d %(bbcustom_dir)s' % master)
        run('test -d %(bbconfigs_dir)s' % master)
        run('test -d %(master_dir)s' % master)
        run('test -d %(tools_dir)s' % master)

        assert run('hg -R %(bbcustom_dir)s ident -b' % master) == \
            master['bbcustom_branch']
        assert run('hg -R %(bbconfigs_dir)s ident -b' % master) == \
            master['bbconfigs_branch']
        assert run('hg -R %(tools_dir)s ident -b' % master) == \
            master['tools_branch']
        print master['name'], date, OK


def action_checkconfig(master):
    """Runs buildbot checkconfig"""
    action_check(master)
    with hide('stdout', 'stderr'):
        with cd(master['basedir']):
            try:
                run('make checkconfig')
                print "%-14s %s" % (master['name'], OK)
            except:
                print "%-14s %s" % (master['name'], FAIL)
                raise


def action_show_revisions(master):
    """Reports the revisions of: buildbotcustom, buildbot-configs, tools, buildbot"""
    with hide('stdout', 'stderr', 'running'):
        bbcustom_rev = run('hg -R %(bbcustom_dir)s ident -i' % master)
        bbconfigs_rev = run('hg -R %(bbconfigs_dir)s ident -i' % master)
        tools_rev = run('hg -R %(tools_dir)s ident -i' % master)
        bbcustom_rev = bbcustom_rev.split()[0]
        bbconfigs_rev = bbconfigs_rev.split()[0]
        tools_rev = tools_rev.split()[0]

        bb_version = run('unset PYTHONHOME PYTHONPATH; '
                         '%(buildbot_bin)s --version' % master)
        bb_version = bb_version.replace('\r\n', '\n')
        m = re.search('^Buildbot version:.*-hg-([0-9a-f]+)-%s' %
                      master['buildbot_branch'], bb_version, re.M)
        if not m:
            print FAIL, "Failed to parse buildbot --version output:", \
                repr(bb_version)
            bb_rev = ""
        else:
            bb_rev = m.group(1)

        show_revisions_detail(master['name'], bbcustom_rev, bbconfigs_rev,
                              tools_rev, bb_rev)


def show_revisions_detail(master, bbcustom_rev, bbconfigs_rev,
                          tools_rev, buildbot_rev):
    print "%-25s %12s %12s %12s %12s" % (master, bbcustom_rev, bbconfigs_rev,
                                         tools_rev, buildbot_rev)


def show_revisions_header():
    show_revisions_detail("master", "bbcustom", "bbconfigs", "tools",
                          "buildbot")


def action_reconfig(master):
    """Performs a reconfig (only - no update or checkconfig)"""
    print "starting reconfig of %(hostname)s:%(basedir)s" % master
    with show('running'):
        with cd(master['basedir']):
            put(BUILDBOT_WRANGLER,
                '%s/buildbot-wrangler.py' % master['basedir'])
            run('rm -f *.pyc')
            run('python buildbot-wrangler.py reconfig %s' %
                master['master_dir'])
    print OK, "finished reconfig of %(hostname)s:%(basedir)s" % master


def action_restart(master):
    with show('running'):
        with cd(master['basedir']):
            put(BUILDBOT_WRANGLER, '%s/buildbot-wrangler.py' %
                master['basedir'])
            run('rm -f *.pyc')
            run('python buildbot-wrangler.py restart %s' %
                master['master_dir'])
    print OK, "finished restarting of %(hostname)s:%(basedir)s" % master


def action_graceful_restart(master):
    with show('running'):
        with cd(master['basedir']):
            put(BUILDBOT_WRANGLER, '%s/buildbot-wrangler.py' %
                master['basedir'])
            run('rm -f *.pyc')
            run('python buildbot-wrangler.py graceful_restart %s %s' %
                (master['master_dir'], master['http_port']))
    print OK, \
        "finished gracefully restarting of %(hostname)s:%(basedir)s" % master


def action_stop(master):
    with show('running'):
        with cd(master['basedir']):
            put(BUILDBOT_WRANGLER,
                '%s/buildbot-wrangler.py' % master['basedir'])
            run('python buildbot-wrangler.py stop %s' % master['master_dir'])
    print OK, "stopped %(hostname)s:%(basedir)s" % master


def action_graceful_stop(master):
    with show('running'):
        with cd(master['basedir']):
            put(BUILDBOT_WRANGLER,
                '%s/buildbot-wrangler.py' % master['basedir'])
            run('rm -f *.pyc')
            run('python buildbot-wrangler.py graceful_stop %s %s' %
                (master['master_dir'], master['http_port']))
    print OK, "gracefully stopped %(hostname)s:%(basedir)s" % master


def start(master):
    with show('running'):
        with cd(master['basedir']):
            put(BUILDBOT_WRANGLER,
                '%s/buildbot-wrangler.py' % master['basedir'])
            run('rm -f *.pyc')
            run('python buildbot-wrangler.py start %s' % master['master_dir'])
    print OK, "started %(hostname)s:%(basedir)s" % master


def action_update(master):
    with show('running'):
        with cd(master['basedir']):
            run('source bin/activate && make update')
    print OK, "updated %(hostname)s:%(basedir)s" % master


def action_update_buildbot(master):
    with show('running'):
        buildbot_dir = os.path.dirname(master['buildbot_setup'])
        with cd(buildbot_dir):
            run('hg pull')
            run('hg update -r %s' % master['buildbot_branch'])
            run('unset PYTHONHOME PYTHONPATH; %s setup.py install' %
                master['buildbot_python'])
    print OK, "updated buildbot in %(hostname)s:%(basedir)s" % master


def action_fix_makefile_symlink(master):
    with show('running'):
        run('rm -f %(basedir)s/Makefile' % master)
        run('ln -s %(bbconfigs_dir)s/Makefile.master %(basedir)s/Makefile' %
            master)
    print OK, "updated Makefile symlink in %(hostname)s:%(basedir)s" % master


def action_add_esr17_symlinks(master):
    with show('running'):
        run('ln -s %(bbconfigs_dir)s/mozilla/release-firefox-mozilla-esr17.py '
            '%(master_dir)s/' % master)
        run('ln -s %(bbconfigs_dir)s/mozilla/l10n-changesets_mozilla-esr17 '
            '%(master_dir)s/' % master)
        run('ln -s %(bbconfigs_dir)s/mozilla/release-thunderbird-comm-esr17.py '
            '%(master_dir)s/' % master)
        run('ln -s %(bbconfigs_dir)s/mozilla/l10n-changesets_thunderbird-esr17 '
            '%(master_dir)s/' % master)
    print OK, "Added esr17 symlinks in %(hostname)s:%(basedir)s" % master


def per_host(fn):
    fn.per_host = True
    return fn


@per_host
def action_update_queue(host):
    with show('running'):
        queue_dir = "/builds/buildbot/queue"
        tools_dir = "%s/tools" % queue_dir
        with cd(tools_dir):
            run('hg pull -u')
    print OK, "updated queue in %s" % host


@per_host
def action_retry_dead_queue(host):
    for q in 'commands', 'pulse':
        cmd = "find /dev/shm/queue/%s/dead -type f" % q
        for f in run(cmd).split("\n"):
            f = f.strip()
            if not f:
                continue
            with show('running'):
                run("mv %s /dev/shm/queue/%s/new" % (f, q))


class IgnoreMissingHostKey(paramiko.MissingHostKeyPolicy):
    def missing_host_key(self, *args, **kwargs):
        return


def action_unstick_slaves(master):
    # Use the manhole to unstick slaves
    # Log with regular ssh to set up forwarding
    print "Starting ssh tunnel to", master['hostname']
    ssh_tunnel = subprocess.Popen(
        ["ssh", "-l", "cltbld",
         '-o', 'StrictHostKeyChecking=no',
         '-L%s:localhost:%s' % (master['ssh_port'], master['ssh_port']),
         master['hostname'], 'sleep 60'])

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(IgnoreMissingHostKey())
    print "Connecting to manhole via tunnel"

    for _ in range(10):
        try:
            assert ssh_tunnel.poll() is None
            client.connect(hostname='localhost', port=master['ssh_port'], username='cltbld', password='password')
            break
        except Exception:
            time.sleep(0.5)
    else:
        raise IOError("couldn't connect")

    magic = """\
for s in master.botmaster.slaves.values():
    if s.slave and s.slave_status.getGraceful():
        if len([sb for sb in s.slavebuilders.values() if sb.isBusy()]) == 0:
            print "stopping", s.slavename
            s.slave.callRemote("shutdown")

# SENTINAL
"""
    transport = client.get_transport()
    session = transport.open_session()
    session.set_combine_stderr(True)
    session.get_pty(term='screen')
    session.invoke_shell()

    session.sendall("\n")
    f = session.makefile()
    print "Sending magic"
    session.sendall(magic + "\n\n")
    session.close()

    stopped_slaves = []
    while True:
        line = f.readline()
        if line:
            m = re.match("stopping (\S+)", line)
            if m:
                stopped_slaves.append(m.group(1))
        if "# SENTINAL" in line:
            break
        time.sleep(0.1)

    for s in sorted(stopped_slaves):
        print "stopped", s
    ssh_tunnel.kill()
    ssh_tunnel.wait()
