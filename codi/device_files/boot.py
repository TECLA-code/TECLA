try:
    with open('/config/device_name.txt', 'r') as f:
        name = f.read().strip()
    if name:
        import supervisor
        supervisor.set_usb_identification(product=name)
except Exception:
    pass
