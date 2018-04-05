import time

from AppKit import NSWorkspace
from Quartz import CGWindowListCopyWindowInfo
from Quartz import kCGNullWindowID
from Quartz import kCGWindowListOptionOnScreenOnly


def win():
    # todo not working correctly
    # fma = NSWorkspace.sharedWorkspace().frontmostApplication()
    # print(fma.localizedName(), fma.isActive())
    #
    # for i in NSWorkspace.sharedWorkspace().runningApplications():
    #     print(i.isActive(), i.localizedName())
    # https://stackoverflow.com/questions/25799023/how-to-retrieve-the-osx-application-that-currently-receives-key-events

    # todo this is deprecated
    curr_app = NSWorkspace.sharedWorkspace().activeApplication()
    print("XXX")
    print(curr_app.keys())
    print (curr_app['NSApplicationProcessIdentifier'],
           # curr_app['NSApplicationBundleIdentifier'],
           curr_app['NSApplicationName'],
           # curr_app['NSApplicationPath']
    )
    # curr_app_name = curr_app.localizedName()
    # print(curr_app["NSApplicationProcessIdentifier"], curr_pid)
    # print(curr_app.processIdentifier(), curr_pid)
    # print(curr_app_name)
    options = kCGWindowListOptionOnScreenOnly
    windowList = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
    # todo pid is for main process and matching all windows
    # for window in windowList:
    #     pid = window['kCGWindowOwnerPID']
    #     # print(window.keys())
    #     print(window['kCGWindowIsOnscreen'], window["kCGWindowName"],
    #           window["kCGWindowLayer"])
    # kCGWindowOwnerName
    #     if curr_pid == pid:
    #         windowNumber = window['kCGWindowNumber']
    #         ownerName = window['kCGWindowOwnerName']
    #         geometry = window['kCGWindowBounds']
    #         windowTitle = window.get('kCGWindowName', 'Unknown')
    #
    #         print("%s - %s (PID: %d, WID: %d)" % (
    #             ownerName, windowTitle.encode('ascii', 'ignore'), pid,
    #             windowNumber))
    print("---")


while True:
    win()
    time.sleep(0.5)
