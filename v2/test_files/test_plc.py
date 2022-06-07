import pyads
from time import sleep

plc =  pyads.Connection('10.44.1.14.1.1',801)

values =  ['fc_m1_alternatedeposit_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m1_axis4_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m1_centerer_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m1_linkup_belt_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m1_multilever_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m1_pickup_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m1_preassembly1_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m1_transportleft_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m1_transportright_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m1_transportseparator_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m2_alternatedeposit_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m2_axis4_axis_jamcontrol.actual_following_error_value_nmtr',
'fc_m2_centerer_axis_jamcontrol.actual_following_error_value_nmtr']



listik = ['main_motorization.main_motorization_manager.actual_velocity_ppr']

with plc:
    while True:
        
        print([(lambda x: round(x,3))(x) for x in plc.read_list_by_name(values).values()],sep='\n')
        sleep(0.025)