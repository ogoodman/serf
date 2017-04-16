#!/usr/bin/python
"""Script to maintain serf websites and backends on an Ubuntu server.

   Supports Ubuntu 14.04 - 16.04 running Apache or Nginx.

Usage:

    site list

        Prints a list of config files for the local server type
        followed by the domains and backends defined in each.

    site show <domain>

        Prints the config file for the specified domain.

    site check

        Check webserver configs are valid. Invokes the relevant
        Apache or Nginx check.

    site add-backend <code-dir> <domain> <name> <port> <desc>

        Create a backend service at ws://<domain>/<name>/<ws>/. A
        service executable is created at <code-dir>/<name>_server.py
        and it listens on the specified <port>.

    site remove-backend <domain> <name>

        Removes the backend service and proxy-pass directives added
        by an add-backend command. The service executable (which
        might have been created by add-backend) is not removed.

    site add-site <code-dir> <domain> <name>

        Creates a demo website in <code-dir>/www
        linked from the document root of <domain> as <domain>/<name>/
        with backend service at ws://<domain>/<name>/ws/.

The remaining commands are lower level; they are invoked indirectly
by the add-backend and remove-backend commands.

    site add-proxy-pass <domain> <path> <port>

        Adds proxy-pass directive for a websocket at <domain>/<path>/
        which forwards to ws://localhost:<port>/.

    site remove-proxy-pass <domain> <path>

        Remove proxy-pass for a websocket server at <domain>/<path>/.

    site add-service <name> <program> <desc>

        Adds a service called <name> which runs <program> with
        description <desc> (which should be quoted if it contains
        more than one word). Chooses upstart or systemd based on
        the Ubuntu version.

    site remove-service <name>

        Removes the named service.

NOTE: this script does not yet create Apache or Nginx configs for
virtual hosts (domains). It may make some assumptions about the layout
of said configs.
"""

import os
import re
import sys

def rest_of_line(l):
    return l.split(None, 1)[-1]

def check_root():
    if os.popen('whoami').read().strip() == 'root':
        return True
    print 'You need to be root to do this'
    return False

# ------------------------------------------------------------

NG_PROXY_RE = """\
  location /(\\w+)/ \\{
    proxy_pass http://localhost:(\\d+);
    proxy_http_version 1.1;
    proxy_set_header Upgrade \\$http_upgrade;
    proxy_set_header Connection "upgrade";
  }
"""

NG_PROXY_TPL = """\
  location /%s/ {
    proxy_pass http://localhost:%s;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }
"""

A2_PROXY_RE = re.compile(r'/([\w/]+)/\s+ws://localhost:(\d+)/')

A2_PROXY_TPL = """\
\tProxyPass /%s/ ws://localhost:%s/
\tProxyPassReverse /%s/ ws://localhost:%s/
"""

def split_csep(s):
    return [w.strip() for w in s.split(',')]

class Apache2(object):
    SITES_AVAIL = '/etc/apache2/sites-available'

    def list_sites(self):
        sites = []
        for name in os.listdir(self.SITES_AVAIL):
            if not name.endswith('.conf'):
                continue
            path = os.path.join(self.SITES_AVAIL, name)
            conf = open(path).read()
            if not conf.startswith('<VirtualHost'):
                continue

            domains = []
            proxy_pass = []
            doc_root = None
            for l in conf.splitlines():
                if '#' in l:
                    l = l.split('#', 1)[0]
                ls = l.strip()
                if ls.startswith('ServerName'):
                    domains.extend(split_csep(rest_of_line(ls)))
                if ls.startswith('ServerAlias'):
                    domains.extend(split_csep(rest_of_line(ls)))
                if ls.startswith('ProxyPass '):
                    m = A2_PROXY_RE.match(rest_of_line(ls))
                    if m is not None:
                        proxy_pass.append(m.groups())
                if ls.startswith('DocumentRoot'):
                    doc_root = rest_of_line(ls)
            if not domains:
                continue
            sites.append({'file': path, 'domains': domains, 'proxy_pass': proxy_pass, 'doc_root': doc_root})
        return sites

    def ppass_text(self, path, port):
        return A2_PROXY_TPL % (path, port, path, port)

    def conf_end_pos(self, conf):
        return conf.rfind('\n</VirtualHost>')

    def check(self):
        os.system('apachectl -t')

class Nginx(object):
    SITES_AVAIL = '/etc/nginx/sites-available'

    def list_sites(self):
        sites = []
        for name in os.listdir(self.SITES_AVAIL):
            if name.endswith('~'):
                continue
            path = os.path.join(self.SITES_AVAIL, name)
            conf = open(path).read()
            if not conf.startswith('server {'):
                continue

            domains = []
            doc_root = None
            for l in conf.splitlines():
                if '#' in l:
                    l = l.split('#', 1)[0]
                ls = l.strip().rstrip(';')
                if ls.startswith('server_name'):
                    domains.extend(rest_of_line(ls).split())
                if ls.startswith('root'):
                    doc_root = rest_of_line(ls)

            proxy_pass = []
            for m in re.finditer(NG_PROXY_RE, conf, re.MULTILINE):
                proxy_pass.append(m.groups())

            sites.append({'file': path, 'domains': domains, 'proxy_pass': proxy_pass, 'doc_root': doc_root})
        return sites

    def ppass_text(self, path, port, prefix=None):
        return NG_PROXY_TPL % (path, port)

    def conf_end_pos(self, conf):
        return conf.rfind('\n}')

    def check(self):
        if not check_root():
            return
        os.system('sudo nginx -t -c /etc/nginx/nginx.conf')

# ------------------------------------------------------------

UPSTART_TPL = """\
description "%s"

start on runlevel [2]
stop on runlevel [!2]
stop on pre-stop networking

console log

respawn
respawn limit 2 5

exec %s
"""

SYSTEMD_TPL = """\
[Unit]
Description=%s

[Service]
ExecStart=%s

[Install]
WantedBy=multi-user.target
"""

class SystemD(object):
    PATH = '/etc/systemd/system/%s.service'

    def type(self):
        return 'systemd'

    def add_service(self, name, prog, desc):
        conf = SYSTEMD_TPL % (desc, prog)
        path = self.PATH % name
        if not check_root():
            return
        update_file(path, conf)
        os.system('systemctl enable %s.service' % name)

    def remove_service(self, name):
        if not check_root():
            return
        os.system('service %s stop' % name)
        os.system('systemctl disable %s.service' % name)
        path = self.PATH % name
        os.unlink(path)
        os.system('systemctl daemon-reload')

class Upstart(object):
    PATH = '/etc/init/%s.conf'

    def type(self):
        return 'upstart'

    def add_service(self, name, prog, desc):
        conf = UPSTART_TPL % (desc, prog)
        path = self.PATH % name
        update_file(path, conf)

    def remove_service(self, name):
        if not check_root():
            return
        os.system('service %s stop' % name)
        path = self.PATH % name
        os.unlink(path)

def ubuntu_version():
    info = {}
    for l in os.popen('lsb_release -a 2>&1'):
        if ':' in l:
            k, v = l.split(':')
            info[k.strip()] = v.strip()
    if 'Distributor ID' not in info:
        return None
    if info['Distributor ID'] != 'Ubuntu':
        return None
    return info['Release']

def services():
    version = ubuntu_version()
    if version is None:
        return None
    if version < '15':
        return Upstart()
    else:
        return SystemD()

# ------------------------------------------------------------

SERVER_TPL = '''\
#!/usr/bin/python

"""%s"""

import sys
from serf.ws_server import serve_ws

class Ping(object):
    def ping(self):
        return 'pong'

def init_session(handler):
    handler.provide('ping', Ping())

port = int(sys.argv[1])
serve_ws(init_session, port)
'''

def create_server(path, desc):
    if os.path.exists(path):
        print 'Service executable already exists'
        return
    prog = SERVER_TPL % desc
    with open(path, 'w') as out:
        out.write(prog)
    os.chmod(path, 0755)
    print 'Created:', path

# ------------------------------------------------------------

def webserver():
    if os.path.exists('/etc/apache2/sites-available'):
        return Apache2()
    if os.path.exists('/etc/nginx/sites-available'):
        return Nginx()

def print_sites(sites):
    for site in sites:
        print site['file']
        for d in site['domains']:
            print '   ', d
        for pp in site['proxy_pass']:
            print '    /%s/ -> %s' % pp

def find_domain(ws, domain):
    sites = ws.list_sites()
    for site in sites:
        if domain in site['domains']:
            return site

def update_file(path, content, backup=False):
    if not check_root():
        return
    if backup and os.path.exists(path):
        os.rename(path, path + '~')
    with open(path, 'w') as out:
        out.write(content)
    print 'Updated:', path

def remove_proxy_pass(ws, domain, path):
    site = find_domain(ws, domain)
    if site is None:
        print 'domain not found:', domain
        return
    for s_path, port in site['proxy_pass']:
        if s_path == path:
            break
    else:
        print 'proxy_pass not found:', path
        return
    conf = open(site['file']).read()
    pp_text = ws.ppass_text(path, port)
    if pp_text + '\n' in conf:
        new_conf = conf.replace(pp_text + '\n', '')
    elif '\n' + pp_text in conf:
        new_conf = conf.replace('\n' + pp_text, '')
    else:
        new_conf = conf.replace(pp_text, '')
    update_file(site['file'], new_conf, backup=True)

def add_proxy_pass(ws, domain, path, port):
    site = find_domain(ws, domain)
    if site is None:
        print 'domain not found:', domain
        return
    for s_path, _ in site['proxy_pass']:
        if s_path == path:
            print 'proxy_pass already exists for:', path
            return
    pp_text = '\n' + ws.ppass_text(path, port)
    conf = open(site['file']).read()
    pos = ws.conf_end_pos(conf)
    if pos < 0:
        # Can't find where the virtual host directive is closed.
        print 'unable to parse:', site['file']
        return
    if conf[pos-1] != '\n':
        pp_text = '\n' + pp_text
    new_conf = conf[:pos] + pp_text + conf[pos:]
    update_file(site['file'], new_conf, backup=True)

def show_site(ws, domain):
    site = find_domain(ws, domain)
    if site is None:
        print 'domain not found:', domain
        return
    print open(site['file']).read(),

def add_backend(code_dir, domain, name, port, desc):
    # create websocket server at <code-dir>/<name>_server.py
    # install as service <name> listening on <port>
    # expose via proxy-pass as ws://<domain>/<name>/ws/
    if not check_root():
        return
    ws = webserver()
    if ws is None:
        print 'Unknown web-server type.'
        return
    if find_domain(ws, domain) is None:
        print 'Domain %s not configured' % domain
        return
    code_dir = os.path.abspath(code_dir)
    cd_parent = os.path.dirname(code_dir)
    if not os.path.exists(cd_parent):
        print 'Code-dir parent does not exist:', cd_parent
        return
    port = int(port)
    if not os.path.exists(code_dir):
        os.makedirs(code_dir)
    exec_path = os.path.join(code_dir, name + '_server.py')
    create_server(exec_path, desc)
    prog = '%s %d' % (exec_path, port)
    services().add_service(name, prog, desc)
    add_proxy_pass(webserver(), domain, name + '/ws', port)

def remove_backend(domain, name):
    if not check_root():
        return
    remove_proxy_pass(webserver(), domain, name + '/ws')
    services().remove_service(name)

INDEX_HTML_TPL = """\
<html>
  <head>
    <meta charset="utf-8">
    <title>%s</title>
    <script src="/js/serf/promise.js" type="text/javascript"></script>
    <script src="/js/serf/rpc.js" type="text/javascript"></script>
    <script src="js/index.js" type="text/javascript"></script>
  </head>
  <body>
    <h3>%s</h3>
    <p><input type="button" value="ping" id="ping"> <input type="text" id="response">
    <p>Status: <span id="status" style="color:orange;">connecting</span>
  </body>
</html>
"""

INDEX_JS_TPL = """\
window.onload = function() {
    var server = new rpc.WSServer('ws://' + location.hostname + '/%s/ws/');

    // Show connection status.
    var st = document.getElementById('status');
    server.onopen = function() {
        st.style.color = 'green';
        st.textContent = 'connected';
    };
    server.onclose = function() {
        st.style.color = 'red';
        st.textContent = 'disconnected';
    };

    var ping_prx = server.getProxy('ping', ['ping']); // object-id, methods

    var button = document.getElementById('ping');
    var response = document.getElementById('response');

    // Click to call ping_prx.ping() and display response.
    button.onclick = function() {
        ping_prx.ping().done(function(r) {
            response.value = r;
        });
    };

    server.connect();
};
"""

def add_site(code_dir, domain, name):
    # builds demo site in <code_dir>/www/
    # hosted at <domain>/<name>/
    # connecting to <domain>/<name>/ws/
    ws = webserver()
    site = find_domain(ws, domain)
    if site is None:
        print 'Abort: cannot find config for %s' % domain
        return
    if site['doc_root'] is None:
        print 'Abort: cannot find document root for %s' % domain
        return
    if not check_root():
        return
    code_dir = os.path.abspath(code_dir)
    www_dir = os.path.join(code_dir, 'www')
    www_main = os.path.join(www_dir, 'index.html')
    js_dir = os.path.join(www_dir, 'js')
    js_main = os.path.join(js_dir, 'index.js')
    if os.path.exists(www_main):
        print 'Skipping: site already exists'
    else:
        os.makedirs(js_dir)
        html = INDEX_HTML_TPL % (name, name)
        open(www_main, 'w').write(html)
        print 'Wrote:', www_main
        js = INDEX_JS_TPL % name
        open(js_main, 'w').write(js)
        print 'Wrote:', js_main
    doc_link = os.path.join(site['doc_root'], name)
    if os.path.exists(doc_link):
        os.unlink(doc_link)
    os.symlink(www_dir, doc_link)
    print 'Linked: %s -> %s' % (doc_link, www_dir)

# ------------------------------------------------------------
# Commands
# ------------------------------------------------------------

def list_cmd():
    print_sites(webserver().list_sites())

def remove_proxy_pass_cmd():
    domain, path = sys.argv[2:]
    remove_proxy_pass(webserver(), domain, path)

def add_proxy_pass_cmd():
    domain, path, port = sys.argv[2:]
    add_proxy_pass(webserver(), domain, path, port)

def show_cmd():
    domain = sys.argv[2]
    show_site(webserver(), domain)

def check_cmd():
    webserver().check()

def add_service_cmd():
    name, prog, desc = sys.argv[2:]
    services().add_service(name, prog, desc)

def remove_service_cmd():
    name = sys.argv[2]
    services().remove_service(name)

def add_backend_cmd():
    code_dir, domain, name, port, desc = sys.argv[2:]
    add_backend(code_dir, domain, name, port, desc)

def remove_backend_cmd():
    domain, name = sys.argv[2:]
    remove_backend(domain, name)

def add_site_cmd():
    code_dir, domain, name = sys.argv[2:]
    add_site(code_dir, domain, name)

def main():
    if '-h' in sys.argv:
        print __doc__
        return
    cmd = sys.argv[1]
    fn = globals().get(cmd.replace('-', '_') + '_cmd')
    if fn is None:
        print 'Unknown command:', cmd
        return
    fn()

if __name__ == '__main__':
    main()
