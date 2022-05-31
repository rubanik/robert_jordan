import pyads

plc =  pyads.Connection('10.44.1.14.1.1',801)

plc.open()
plc.close()
