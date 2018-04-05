import time

from AppKit import NSWorkspace
from Quartz import CGWindowListCopyWindowInfo
from Quartz import kCGNullWindowID
from Quartz import kCGWindowListOptionOnScreenOnly


def win():
    curr_app = NSWorkspace.sharedWorkspace().frontmostApplication()
    curr_pid = NSWorkspace.sharedWorkspace().activeApplication()[
        'NSApplicationProcessIdentifier']
    curr_app_name = curr_app.localizedName()
    print(curr_app_name)
    options = kCGWindowListOptionOnScreenOnly
    windowList = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
    for window in windowList:
        pid = window['kCGWindowOwnerPID']
        windowNumber = window['kCGWindowNumber']
        ownerName = window['kCGWindowOwnerName']
        geometry = window['kCGWindowBounds']
        windowTitle = window.get('kCGWindowName', u'Unknown')
        if curr_pid == pid:
            print("%s - %s (PID: %d, WID: %d): %s" % (
                ownerName, windowTitle.encode('ascii', 'ignore'), pid,
                windowNumber, geometry))


while True:
    win()
    time.sleep(0.5)
