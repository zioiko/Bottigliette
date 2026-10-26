import trgenpy as tp
import winsound

client=tp.TrgenClient()
client.connect()
client.setDefaultDuration(1000)
client.sendMarker(markerNS=1,autoStart=False,LSB=True)
winsound.PlaySound("C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/giu-oppo.wav", winsound.SND_FILENAME)
client.start()