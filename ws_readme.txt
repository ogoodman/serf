Main page and JavaScript
========================
In a suitable <doc-root> published as http://<host>/ we put

  Prerequisites:

  js/require.js  - requirejs module system
  js/when/       - when module
  js/serf/       - link to serf/js

  Demo:

  ws_demo.html   - link to serf/ws_demo.html
  js/ws_demo.js  - link to serf/js/ws_demo.js

The main page, <doc-root>/ws_demo.html loads the javascript code for the
client via:

  <script src="js/require.js" data-main="js/ws_demo.js"></script>

The websocket in main.js is 'ws://' + location.hostname + '/ws/'.
(If port 9999 were forwarded we could directly use ws://<host-name>:9999/.)

Server-side setup
=================

For apache add
  ProxyPass /ws/ ws://localhost:9999/ 
to the http config.

Run the server in
  serf/python/ws_server.py

To run it as a service, update the path to ws_server.py in
  serf/python/ws_server.conf
and copy to /etc/init/ws_server.conf. Then
  sudo initctl reload-configuration
  sudo initctl start ws_server
to run it.
