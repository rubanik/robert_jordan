import pyads
from time import sleep

plc =  pyads.Connection('10.44.1.14.1.1',801)

with plc:
    while True:
        print(plc.read_by_name('MS_Flow1_Cut_Centering_Rear.center_abs_pos_npr',pyads.PLCTYPE_LREAL))
        sleep(1)
