import pyads
from time import sleep

plc =  pyads.Connection('10.44.1.14.1.1',801)

listik = ['main_motorization.main_motorization_manager.actual_velocity_ppr']

with plc:
    while True:
        print(round(plc.read_by_name('main_motorization.main_motorization_manager.actual_velocity_ppm',pyads.PLCTYPE_LREAL),1))
        sleep(1)
