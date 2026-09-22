import trgenpy as tp
import time
# ===========================================================
# Parallel Port through NEW trigger box
# ============================================================
client = tp.TrgenClient()
client.connect()
isAavailable = client.is_available()


client.setDefaultDuration(250)
#client.sendMarker(markerNS= 56)
#client.start()
client.sendTrigger([tp.TrgenPin.NS0])
time.sleep(0.5)
client.sendTrigger([tp.TrgenPin.NS1])
time.sleep(0.5)
client.sendTrigger([tp.TrgenPin.NS2])
time.sleep(0.5)
client.sendTrigger([tp.TrgenPin.NS3])
time.sleep(0.5)
client.sendTrigger([tp.TrgenPin.NS4])
time.sleep(0.5)
client.sendTrigger([tp.TrgenPin.NS5])
time.sleep(0.5)
client.sendTrigger([tp.TrgenPin.NS6])
time.sleep(0.5)
client.sendTrigger([tp.TrgenPin.NS7])
