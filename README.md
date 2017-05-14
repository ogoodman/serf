Serf - Serialization Framework
==============================

Overview
--------

Serialization is required for remote procedure call systems and for
object persistence.

The fact that this project implements its own serialization system and
RPC protocol was partly just an exercise but also reflects our view
that JSON is too simple and inflexible, while XML brings too much baggage.
We do like `msgpack` though.

The aim of this project is to provide a blueprint for
internet-scale networks of persistent objects. One possible
application for such networks would be fully-decentralized social
networking.

Meanwhile, objects require user interfaces and the quickest path to
providing cross-platform interfaces is web technology. Or, to look at
it another way, web-apps require back-ends.

Demos
-----

This project contains a number of demos.

* `demos/ws` shows how to develop a backend for a single-page web app,
  using only the most basic Apache or Nginx configurations.

* `demos/chat` provides a realistic example.

* `demos/simple` demonstrates the basic mechanics of persistent objects
  and their links. It uses only the Serf protocol.

* Further examples show how to connect user interface elements to
  objects and how the object-capability model can be used to create
  secure multi-user apps.
