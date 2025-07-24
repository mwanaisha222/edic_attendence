import nfc
from nfc.clf import RemoteTarget
import time

def read_nfc(timeout=10):
    try:
        with nfc.ContactlessFrontend('usb') as clf:
            target = clf.sense(RemoteTarget('106A'), 
                              RemoteTarget('106B'), 
                              RemoteTarget('212F'), 
                              iterations=10, 
                              interval=0.1)
            if target:
                tag = nfc.tag.activate(clf, target)
                return tag.identifier.hex()
    except Exception as e:
        print(f"Reader error: {e}")
    return None