from tester import *

server = WorkServer(*server_credentials)
server.start()

iterator = server.imap_unordered(simple_print, range(5))
for val in iterator:
    val

server.shutdown()
