import pyads

plc =  pyads.Connection('10.44.1.14.1.1',801)

plc.open()

try:
    plc.read_by_name(pself.cl_path,pyads.)

plc.close()
