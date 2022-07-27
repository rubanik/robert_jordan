import pyads
from time import sleep

plc =  pyads.Connection('10.44.1.14.1.1',801)

values =  ["Camera_GPVS_PC_1.GPVS_camera_0_apps_variables.measure_array_real[0]",
"Camera_GPVS_PC_1.GPVS_camera_0_apps_variables.measure_array_real[1]",
"Camera_GPVS_PC_1.GPVS_camera_0_apps_variables.measure_array_real[2]",
"Camera_GPVS_PC_1.GPVS_camera_0_apps_variables.measure_array_real[3]",
"Camera_GPVS_PC_1.GPVS_camera_0_apps_variables.measure_array_real[4]",
"main_motorization.main_motorization_manager.actual_velocity_ppm"]

with plc:
    while True:
        
        print(list(plc.read_list_by_name(values).values()))
        sleep(1)
        