import storage

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
