"""Funcions de potenciòmetre per al Mode Teclat - mòdul separat per estalviar RAM"""


def update_parameters(kbd, pot_values, force_update=False):
    if len(pot_values) < 3:
        return
    if kbd.arp_mode_active:
        apply_arp_pot_function(kbd, 'arp_pot_x', pot_values[1], force_update=force_update)
        apply_arp_pot_function(kbd, 'arp_pot_y', pot_values[0], force_update=force_update)
        apply_arp_pot_function(kbd, 'arp_pot_z', pot_values[2], force_update=force_update)
    else:
        apply_pot_function(kbd, 'pot_x', pot_values[1], force_update=force_update)
        apply_pot_function(kbd, 'pot_y', pot_values[0], force_update=force_update)
        apply_pot_function(kbd, 'pot_z', pot_values[2], force_update=force_update)


def apply_pot_function(kbd, pot_name, pot_value, force_update=False):
    if pot_name == 'pot_x':
        function = kbd.pot_x_function
    elif pot_name == 'pot_y':
        function = kbd.pot_y_function
    elif pot_name == 'pot_z':
        function = kbd.pot_z_function
    else:
        return

    threshold = 0 if force_update else 2

    if function in ('Brillantor', 'Velocity', 'Brightness (CC74)'):
        kbd.velocity = max(20, min(127, pot_value))

    elif function == 'Velocity/Arp Speed (dual)':
        kbd.velocity = max(20, min(127, pot_value))
        if kbd.arp_mode_active:
            speed_value = max(0, min(127, pot_value))
            kbd.arp_speed = 0.5 - (speed_value / 127.0) * 0.49

    elif function in ('Modulació', 'Modulation', 'Modulation (CC1)'):
        kbd._send_cc_if_changed(1, pot_value, threshold=threshold)

    elif function == 'Pitch Bend':
        if pot_value < 5:
            pitch_value = 0
        else:
            pitch_value = int((pot_value / 127.0) * 8191)
        kbd._send_pitch_bend(pitch_value)

    elif function in ('Volum', 'Volume', 'Expression (CC11)'):
        kbd._send_cc_if_changed(7, pot_value, threshold=threshold)

    elif function in ('Sustain', 'Sustain (CC64)'):
        old_hold = kbd.sustain_hold_enabled
        kbd.sustain_hold_value = pot_value

        if pot_value >= 125:
            kbd.sustain_hold_enabled = True
            effective_value = 127
        else:
            kbd.sustain_hold_enabled = False
            effective_value = pot_value

            if old_hold and not kbd.sustain_hold_enabled:
                kbd.stop_all_notes()

        if force_update or 64 not in kbd.cc_values or kbd.cc_values[64] != effective_value:
            kbd._send_cc(64, effective_value)
            kbd.sustain_level = effective_value

    elif function in ('Gate', 'Gate Length'):
        if pot_value < 10:
            kbd.gate_enabled = False
            kbd._send_cc(11, 127)
        else:
            kbd.gate_enabled = True
            kbd.gate_period = 0.5 - (pot_value / 127.0) * 0.45
            kbd.gate_min_expr = 0
            kbd.gate_duty = 0.5

    elif function == 'Expression (CC11)':
        kbd._send_cc_if_changed(11, pot_value, threshold=threshold)

    elif function == 'Pan (CC10)':
        kbd._send_cc_if_changed(10, pot_value, threshold=threshold)

    elif function == 'Reverb (CC91)':
        kbd._send_cc_if_changed(91, pot_value, threshold=threshold)

    elif function == 'Chorus (CC93)':
        kbd._send_cc_if_changed(93, pot_value, threshold=threshold)

    elif function == 'Release (CC72)':
        kbd._send_cc_if_changed(72, pot_value, threshold=threshold)

    if force_update and function not in ('Velocity/Arp Speed (dual)', 'Brillantor', 'Sustain', 'Modulació', 'Volum'):
        print(f"🎹 Teclat Pot: {function}")


def apply_arp_pot_function(kbd, pot_name, pot_value, force_update=False):
    if pot_name == 'arp_pot_x':
        function = kbd.arp_pot_x_function
    elif pot_name == 'arp_pot_y':
        function = kbd.arp_pot_y_function
    elif pot_name == 'arp_pot_z':
        function = kbd.arp_pot_z_function
    else:
        return

    threshold = 0 if force_update else 2

    if function in ('Velocitat (BPM)', 'Arp Speed (BPM)'):
        bpm = 30 + (pot_value / 127.0) * 1970
        kbd.arp_speed = 60.0 / bpm

    elif function in ('Patró De Direcció', 'Arp Pattern Selector'):
        if len(kbd.available_arp_modes) > 0:
            last_val = kbd._arp_pat_sel_last_val
            if last_val is None:
                kbd._arp_pat_sel_last_val = pot_value
            elif abs(pot_value - last_val) >= 3:
                kbd._arp_pat_sel_last_val = pot_value
                num_modes = len(kbd.available_arp_modes)
                mode_idx = int((pot_value / 128.0) * num_modes)
                mode_idx = min(mode_idx, num_modes - 1)
                new_mode = kbd.available_arp_modes[mode_idx]
                if new_mode != kbd.arp_mode_index:
                    kbd.arp_mode_index = new_mode
                    kbd.arp_index = 0
                    kbd.arp_direction = 1
                    print(f"🎶 Arpeggiador (pot): {kbd._get_arp_name(kbd.arp_mode_index)}")

    elif function in ('Brillantor', 'Velocity'):
        kbd.velocity = max(20, min(127, pot_value))

    elif function in ('Volum', 'Volume'):
        kbd._send_cc_if_changed(7, pot_value, threshold=threshold)

    elif function in ('Modulació', 'Modulation', 'Modulation (CC1)'):
        kbd._send_cc_if_changed(1, pot_value, threshold=threshold)

    elif function == 'Pitch Bend':
        if pot_value < 5:
            pitch_value = 0
        else:
            pitch_value = int((pot_value / 127.0) * 8191)
        kbd._send_pitch_bend(pitch_value)

    elif function in ('Gate', 'Gate Length'):
        if pot_value < 10:
            kbd.gate_enabled = False
            kbd._send_cc(11, 127)
        else:
            kbd.gate_enabled = True
            kbd.gate_period = 0.5 - (pot_value / 127.0) * 0.45
            kbd.gate_min_expr = 0
            kbd.gate_duty = 0.5

    if force_update and function not in ('Velocitat (BPM)', 'Arp Speed (BPM)', 'Patró De Direcció', 'Arp Pattern Selector'):
        print(f"🎹 Arp Pot: {function}")
