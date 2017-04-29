ORGANISATION
============

All core python modules live at the top-level. Nothing in the core
depends on anything in the sub-packages.

NOTE: At this time all sub-packages should be treated as demo code.

They are included so that they can be imported and used for building
backend services, however it should not be assumed that they are
stable.

CORE
----

basic utilities
obj.py
publisher.py
util.py
weak_list.py

serialization
serializer.py
json_codec.py
traverse.py

rpc
proxy.py
repl_proxy.py
rpc_handler.py
bound_method.py
ws_server.py

transport
transport.py
ws_transport.py

thread model
eventlet_thread.py
synchronous.py
worker.py
thread_model.py

storage
fs_dict.py
ref.py
storage.py

c++ idl
idl_cpp_types.py
idl_parser.py
idl_types.py

testing
eventlet_test_handler.py
mock_net.py
test_data.py
test_fs.py
test_handler.py
test_object.py
test_person.py
test_time.py

model.py (belongs in po/ ?)

NON-CORE
--------
toy persistent table implementation
table/*

login and user-caps example
user/*

example persistent object classes
po/call_log.py
po/call_log_reader.py
po/data.py
po/data_log.py
po/file.py
po/group.py
po/log_file.py
po/node_observer.py (implements 'node_observer' role for node)
po/printer.py
po/vat_cap.py

full stack examples
client.py
server.py
t_client.py
t_server.py
ws_server.py

scripts
fcat.py

unused
unused/cap.py (random example)
unused/cell.py (random example)
unused/container.py
unused/dict_store.py
unused/dispatcher.py
unused/mock_proxy.py
unused/person.py (random example)
unused/segmented_log.py (work in progress?)
unused/sleeper.py (used for cli testing?)
unused/type.py
