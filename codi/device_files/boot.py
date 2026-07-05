import storage

# Canal de dades USB (usb_cdc.data): el fa servir el mode CONTROLADOR del firmware
# (l'app web pren el control del dispositiu per WebSerial des del Simulador).
# Innocu per a la resta: la consola REPL continua al primer port CDC.
try:
    import usb_cdc
    usb_cdc.enable(console=True, data=True)
except Exception:
    pass

try:
    with open('/config/disk_label.txt', 'r') as f:
        label = f.read().strip()[:11].upper()
    if label:
        m = storage.getmount("/")
        m.label = label
except Exception:
    pass

try:
    with open('/config/device_name.txt', 'r') as f:
        name = f.read().strip()
    if name:
        import supervisor
        supervisor.set_usb_identification(product=name)
except Exception:
    pass
