To run this code we need a host running a web server and we also need
to run python/server.py.

In a suitable <doc-root> published as http://<host>/ we put
  index.html
  js/app.js
  js/app/       - link to Projects/websocket/js containing
  js/app/main.js

  js/when/      - when module
  js/require.js - requirejs module system

We run the server in
  Projects/websocket/python/server.py

The main page, <doc-root>/index.html loads the javascript code for the
client via:

  <script src="js/require.js" data-main="js/app.js"></script>

The app.js script is a bootstrap file which loads app/main.js via:

  require(['app/main'], function(main) {});

The websocket in main.js is 'ws://' + location.hostname + '/ws/'.
(If port 9999 were forwarded we could directly use ws://<host-name>:9999/.)

Built and enabled mod_proxy_wstunnel for Apache 2.2 as per
  http://www.amoss.me.uk/2013/06/apache-2-2-websocket-proxying-ubuntu-mod_proxy_wstunnel/

Added
  ProxyPass /ws/ ws://localhost:9999/ 
to the http config.
