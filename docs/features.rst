Features
========

Distributed Test Support
~~~~~~~~~~~~~~~~~~~~~~~~

Whimsy has support for distributed testing baked in. This system supports
running multiple tests on the same computer or running on both a server
a multiple clients. 

.. note:: The support for remote clients is not particularly fault tolerant. If
    a client disconnects before completing its currently assigned task the
    server is likely to hang. This is one area for further development.

In order to run the test suite in a multithreaded manner. The server and client
should both have the same filesystem structure. (It would be simpliest to share
a nfs mount, but copies will work just fine.) In both the client and server
a `credentials.ini` file must exist in the current working directory. The file
should contain the information to start the server and for the client to
connect to it.

The `credentials.ini` should be formatted as follows:

.. code:: ini

    [Credentials]
    hostname=localhost
    port=11111
    passkey=password

Then when you wish to begin testing start up the client and server:

Client:
.. code:: bash

    whimsy client -j 8

Server:
.. code:: bash

    whimsy run -j 8

.. note:: It is required that the server be started with the flag `-j2`
    or more in order for multithreading support to be enabled.


This support allows non `lazy_init` :class:`whimsy.fixture.Fixture` objects to
be built once and shared across test clients. I.E. expensive setup items like
SCons targets will be built once and all test clients will be able to share
them (assuming a client has the gem5 build attached via nfs).

This distributed support is provisional and may possibly need to be modified to
fit users solutions. Modders will find the currently implemented support in the
:mod:`whimsy.runner.parallel` and :mod:`whimsy.runner.runner` modules.
