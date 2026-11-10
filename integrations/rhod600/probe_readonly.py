# Read-only Windows HID report capability inventory. Never reads keystrokes or sends reports.
import ctypes as C
from ctypes import wintypes as W

class GUID(C.Structure):
    _fields_ = [("Data1", W.DWORD), ("Data2", W.WORD), ("Data3", W.WORD), ("Data4", C.c_ubyte * 8)]

class InterfaceData(C.Structure):
    _fields_ = [("cbSize", W.DWORD), ("InterfaceClassGuid", GUID), ("Flags", W.DWORD), ("Reserved", C.c_void_p)]

class HID_CAPS(C.Structure):
    _fields_ = [
        ("Usage", W.USHORT), ("UsagePage", W.USHORT),
        ("InputReportByteLength", W.USHORT), ("OutputReportByteLength", W.USHORT),
        ("FeatureReportByteLength", W.USHORT), ("Reserved", W.USHORT * 17),
        ("NumberLinkCollectionNodes", W.USHORT),
        ("NumberInputButtonCaps", W.USHORT), ("NumberInputValueCaps", W.USHORT),
        ("NumberInputDataIndices", W.USHORT), ("NumberOutputButtonCaps", W.USHORT),
        ("NumberOutputValueCaps", W.USHORT), ("NumberOutputDataIndices", W.USHORT),
        ("NumberFeatureButtonCaps", W.USHORT), ("NumberFeatureValueCaps", W.USHORT),
        ("NumberFeatureDataIndices", W.USHORT)
    ]

hid = C.WinDLL("hid.dll")
hidp = C.WinDLL("hid.dll")
setup = C.WinDLL("setupapi.dll")
kernel = C.WinDLL("kernel32.dll", use_last_error=True)
hid.HidD_GetHidGuid.argtypes = [C.POINTER(GUID)]
setup.SetupDiGetClassDevsW.argtypes = [C.POINTER(GUID), W.LPCWSTR, W.HWND, W.DWORD]
setup.SetupDiGetClassDevsW.restype = C.c_void_p
setup.SetupDiEnumDeviceInterfaces.argtypes = [C.c_void_p, C.c_void_p, C.POINTER(GUID), W.DWORD, C.POINTER(InterfaceData)]
setup.SetupDiEnumDeviceInterfaces.restype = W.BOOL
setup.SetupDiGetDeviceInterfaceDetailW.argtypes = [C.c_void_p, C.POINTER(InterfaceData), C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.c_void_p]
setup.SetupDiGetDeviceInterfaceDetailW.restype = W.BOOL
setup.SetupDiDestroyDeviceInfoList.argtypes = [C.c_void_p]
kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p, W.DWORD, W.DWORD, W.HANDLE]
kernel.CreateFileW.restype = W.HANDLE
kernel.CloseHandle.argtypes = [W.HANDLE]
hid.HidD_GetPreparsedData.argtypes = [W.HANDLE, C.POINTER(C.c_void_p)]
hid.HidD_GetPreparsedData.restype = W.BOOL
hid.HidD_FreePreparsedData.argtypes = [C.c_void_p]
hid.HidD_GetFeature.argtypes = [W.HANDLE, C.c_void_p, W.DWORD]
hid.HidD_GetFeature.restype = W.BOOL
hidp.HidP_GetCaps.argtypes = [C.c_void_p, C.POINTER(HID_CAPS)]
hidp.HidP_GetCaps.restype = C.c_long
hidp.HidP_GetValueCaps.argtypes = [C.c_int, C.c_void_p, C.POINTER(W.USHORT), C.c_void_p]
hidp.HidP_GetValueCaps.restype = C.c_long

g=GUID()
hid.HidD_GetHidGuid(C.byref(g))
h=setup.SetupDiGetClassDevsW(C.byref(g),None,None,0x12)
if h == C.c_void_p(-1).value:
    raise OSError("SetupDiGetClassDevsW")
try:
    idx=0
    while True:
        dat=InterfaceData()
        dat.cbSize=C.sizeof(InterfaceData)
        if not setup.SetupDiEnumDeviceInterfaces(h,None,C.byref(g),idx,C.byref(dat)):
            break
        idx+=1
        length=W.DWORD(0)
        setup.SetupDiGetDeviceInterfaceDetailW(h,C.byref(dat),None,0,C.byref(length),None)
        buf=C.create_string_buffer(length.value)
        C.cast(buf,C.POINTER(W.DWORD)).contents.value=8
        if not setup.SetupDiGetDeviceInterfaceDetailW(h,C.byref(dat),C.cast(buf,C.c_void_p),length,C.byref(length),None):
            continue
        path=C.wstring_at(C.addressof(buf)+4)
        low=path.lower()
        if "vid_1a2c&pid_8000" not in low:
            continue
        short=low.split("#")[2] if "#" in low else low
        print("HID", "RHOD600", short,flush=True)
        fd=kernel.CreateFileW(path,0,0x3,None,3,0,None)
        if fd == C.c_void_p(-1).value:
            print("  READONLY OPEN FAILED",C.get_last_error(),flush=True)
            continue
        try:
            pre=C.c_void_p()
            if not hid.HidD_GetPreparsedData(fd,C.byref(pre)):
                print("  PREPARSED FAIL",C.get_last_error(),flush=True)
                continue
            try:
                caps=HID_CAPS()
                status=hidp.HidP_GetCaps(pre,C.byref(caps))
                if status < 0:
                    print("  CAPS NTSTATUS",hex(status & 0xffffffff),flush=True)
                else:
                    print(f"  UsagePage=0x{caps.UsagePage:04x} Usage=0x{caps.Usage:04x} IN={caps.InputReportByteLength} OUT={caps.OutputReportByteLength} FEATURE={caps.FeatureReportByteLength} OUT_BUTTON={caps.NumberOutputButtonCaps} OUT_VALUE={caps.NumberOutputValueCaps} FEATURE_BUTTON={caps.NumberFeatureButtonCaps} FEATURE_VALUE={caps.NumberFeatureValueCaps}",flush=True)
                    if caps.OutputReportByteLength or caps.FeatureReportByteLength:
                        for rtype, label in [(1, "OUTPUT"), (2, "FEATURE")]:
                            data = C.create_string_buffer(1024)
                            n = W.USHORT(8)
                            ret = hidp.HidP_GetValueCaps(rtype, data, C.byref(n), pre)
                            if ret >= 0 and n.value:
                                raw = bytes(data)[:42]
                                print(f"    {label} valuecaps={n.value} UsagePage=0x{int.from_bytes(raw[:2],'little'):04x} ReportID={raw[2]} descriptor_prefix={raw.hex(' ')}",flush=True)
                            else:
                                print(f"    {label} valuecaps status=0x{ret & 0xffffffff:08x} count={n.value}",flush=True)
                        if "vid_1a2c&pid_8000" in low and "col07" in low:
                            buf7 = (C.c_ubyte * 8)()
                            buf7[0] = 7
                            ok7 = hid.HidD_GetFeature(fd, C.cast(buf7,C.c_void_p), 8)
                            print("    GET_FEATURE report7 (no changes sent):", bytes(buf7).hex(' ') if ok7 else f"unavailable, WindowsError={C.get_last_error()}",flush=True)
            finally:
                hid.HidD_FreePreparsedData(pre)
        finally:
            kernel.CloseHandle(fd)
finally:
    setup.SetupDiDestroyDeviceInfoList(h)
