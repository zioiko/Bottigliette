import trgenpy as tp

# ===========================================================
# Parallel Port through NEW trigger box
# ============================================================
client = tp.TrgenClient()
client.connect()
isAavailable = client.is_available()


client.setDefaultDuration(250)
#client.sendMarker(markerNS= 56, autoStart=False)
client.sendTrigger([tp.TrgenPin.NS1])