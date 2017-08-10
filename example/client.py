from tester import *

client = WorkClient(*server_credentials)
client.start()
client.join()
