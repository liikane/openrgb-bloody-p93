"""Strict Windows HID adapter for the owner-confirmed Genesis Rhod 600 color command.

No arbitrary HID/raw write API is exposed. Validates full USB interface and HID caps.
Only report family 07 FF 70 ... 03 00 is allowed.
"""
from __future__ import annotations
import ctypes as C
from ctypes import wintypes as W
import os
from protocol import report_for_areas

VID_PID = "vid_1a2c&pid_8000"
INTERFACE = "mi_01&col07"
REPORT_ID = 7
OUTPUT_LENGTH = 8
FEATURE_LENGTH = 8

class RhodDeviceError(RuntimeError):
    pass


class GUID(C.Structure):
    _fields_ = [("Data1", W.DWORD), ("Data2", W.WORD), ("Data3", W.WORD),
                ("Data4", C.c_ubyte * 8)]

class InterfaceData(C.Structure):
    _fields_ = [("cbSize", W.DWORD), ("InterfaceClassGuid", GUID),
                ("Flags", W.DWORD), ("Reserved", C.c_void_p)]

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


def _apis():
    if os.name != "nt":
        raise RhodDeviceError("Rhod600 USB/HID adapter requires Windows")
    hid = C.WinDLL("hid.dll", use_last_error=True)
    setup = C.WinDLL("setupapi.dll", use_last_error=True)
    kernel = C.WinDLL("kernel32.dll", use_last_error=True)
    hid.HidD_GetHidGuid.argtypes = [C.POINTER(GUID)]
    setup.SetupDiGetClassDevsW.argtypes = [C.POINTER(GUID), W.LPCWSTR, W.HWND, W.DWORD]
    setup.SetupDiGetClassDevsW.restype = C.c_void_p
    setup.SetupDiEnumDeviceInterfaces.argtypes = [
        C.c_void_p, C.c_void_p, C.POINTER(GUID), W.DWORD, C.POINTER(InterfaceData)]
    setup.SetupDiEnumDeviceInterfaces.restype = W.BOOL
    setup.SetupDiGetDeviceInterfaceDetailW.argtypes = [
        C.c_void_p, C.POINTER(InterfaceData), C.c_void_p, W.DWORD,
        C.POINTER(W.DWORD), C.c_void_p]
    setup.SetupDiGetDeviceInterfaceDetailW.restype = W.BOOL
    setup.SetupDiDestroyDeviceInfoList.argtypes = [C.c_void_p]
    setup.SetupDiDestroyDeviceInfoList.restype = W.BOOL
    kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p, W.DWORD, W.DWORD, W.HANDLE]
    kernel.CreateFileW.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.CloseHandle.restype = W.BOOL
    hid.HidD_GetPreparsedData.argtypes = [W.HANDLE, C.POINTER(C.c_void_p)]
    hid.HidD_GetPreparsedData.restype = W.BOOL
    hid.HidD_FreePreparsedData.argtypes = [C.c_void_p]
    hid.HidD_FreePreparsedData.restype = W.BOOL
    hid.HidP_GetCaps.argtypes = [C.c_void_p, C.POINTER(HID_CAPS)]
    hid.HidP_GetCaps.restype = C.c_long
    hid.HidD_SetFeature.argtypes = [W.HANDLE, C.c_void_p, W.DWORD]
    hid.HidD_SetFeature.restype = W.BOOL
    return hid, setup, kernel


def _check_caps(fd, hid):
    pre = C.c_void_p()
    if not hid.HidD_GetPreparsedData(fd, C.byref(pre)):
        raise RhodDeviceError("HidD_GetPreparsedData failed")
    try:
        caps=HID_CAPS()
        status=hid.HidP_GetCaps(pre,C.byref(caps))
        if status<0:
            raise RhodDeviceError("Invalid HID caps NTSTATUS")
        if (caps.UsagePage != 0xFF01 or caps.Usage != 1
                or caps.FeatureReportByteLength != FEATURE_LENGTH
                or caps.OutputReportByteLength != OUTPUT_LENGTH
                or caps.InputReportByteLength != 0):
            raise RhodDeviceError("HID identity or report lengths do not match Rhod600")
        return {"usage_page": caps.UsagePage, "usage": caps.Usage,
                "feature_len": caps.FeatureReportByteLength,
                "output_len": caps.OutputReportByteLength}
    finally:
        hid.HidD_FreePreparsedData(pre)


def discover() -> list[tuple[str,dict]]:
    """Read-only enumeration. Does not open the keyboard for write."""
    hid,setup,kernel=_apis()
    guid=GUID()
    hid.HidD_GetHidGuid(C.byref(guid))
    info=setup.SetupDiGetClassDevsW(C.byref(guid),None,None,0x12)
    invalid=C.c_void_p(-1).value
    if info==invalid:
        raise RhodDeviceError("HID class enumeration failed")
    result=[]
    try:
        index=0
        while index < 1024:
            detail=InterfaceData()
            detail.cbSize=C.sizeof(InterfaceData)
            if not setup.SetupDiEnumDeviceInterfaces(info,None,C.byref(guid),index,C.byref(detail)):
                break
            index+=1
            needed=W.DWORD()
            setup.SetupDiGetDeviceInterfaceDetailW(info,C.byref(detail),None,0,C.byref(needed),None)
            if needed.value<10 or needed.value>65536:
                continue
            raw=C.create_string_buffer(needed.value)
            C.cast(raw,C.POINTER(W.DWORD)).contents.value=8
            if not setup.SetupDiGetDeviceInterfaceDetailW(info,C.byref(detail),
                              C.cast(raw,C.c_void_p),needed,C.byref(needed),None):
                continue
            path=C.wstring_at(C.addressof(raw)+4)
            lowered=path.lower()
            if VID_PID not in lowered or INTERFACE not in lowered:
                continue
            fd=kernel.CreateFileW(path,0,0x3,None,3,0,None)
            if fd==invalid:
                raise RhodDeviceError("Matching HID interface cannot be opened read-only")
            try:
                caps=_check_caps(fd,hid)
                result.append((path,caps))
            finally:
                kernel.CloseHandle(fd)
    finally:
        setup.SetupDiDestroyDeviceInfoList(info)
    return result


def vendor_software_running() -> bool:
    """Use the Windows process snapshot API, without reading keystrokes."""
    if os.name!="nt":return False
    kernel=C.WinDLL("kernel32.dll",use_last_error=True)
    class PROCESSENTRY32W(C.Structure):
        _fields_=[
            ("dwSize",W.DWORD),("cntUsage",W.DWORD),("th32ProcessID",W.DWORD),
            ("th32DefaultHeapID",C.c_void_p),("th32ModuleID",W.DWORD),
            ("cntThreads",W.DWORD),("th32ParentProcessID",W.DWORD),
            ("pcPriClassBase",W.LONG),("dwFlags",W.DWORD),("szExeFile",W.WCHAR*260)
        ]
    kernel.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD]
    kernel.CreateToolhelp32Snapshot.restype=W.HANDLE
    kernel.Process32FirstW.argtypes=[W.HANDLE,C.POINTER(PROCESSENTRY32W)]
    kernel.Process32FirstW.restype=W.BOOL
    kernel.Process32NextW.argtypes=[W.HANDLE,C.POINTER(PROCESSENTRY32W)]
    kernel.Process32NextW.restype=W.BOOL
    kernel.CloseHandle.argtypes=[W.HANDLE]
    snap=kernel.CreateToolhelp32Snapshot(0x2,0)
    if snap==C.c_void_p(-1).value:
        raise RhodDeviceError("Cannot verify that the vendor software is not running")
    try:
        pe=PROCESSENTRY32W()
        pe.dwSize=C.sizeof(pe)
        if kernel.Process32FirstW(snap,C.byref(pe)):
            while True:
                if pe.szExeFile.lower()=="shinetektools.exe":
                    return True
                if not kernel.Process32NextW(snap,C.byref(pe)):
                    break
    finally:
        kernel.CloseHandle(snap)
    return False


def set_colors(areas: tuple[int,...] | list[int], *, enabled: bool=False) -> bytes:
    """Write exactly one known lighting report, opt-in only. Never writes macros."""
    data=report_for_areas(areas)  # fail before opening device if not six allowed colors
    if not enabled:
        raise RhodDeviceError("HID writes are disabled; pass enabled=True after verification")
    if vendor_software_running():
        raise RhodDeviceError("Close ShinetekTools.exe before using the Rhod RGB adapter")
    target=discover()
    if len(target)!=1:
        raise RhodDeviceError(f"Expected exactly one verified Rhod600 COL07 device, got {len(target)}")
    path,_=target[0]
    hid,setup,kernel=_apis()
    fd=kernel.CreateFileW(path,0xC0000000,0x3,None,3,0,None)
    if fd==C.c_void_p(-1).value:
        raise RhodDeviceError(f"Rhod HID write access unavailable (Win32 {C.get_last_error()})")
    try:
        _check_caps(fd,hid)
        raw=(C.c_ubyte*8)(*data)
        if not hid.HidD_SetFeature(fd,C.cast(raw,C.c_void_p),8):
            raise RhodDeviceError(f"HidD_SetFeature failed (Win32 {C.get_last_error()})")
        return data
    finally:
        kernel.CloseHandle(fd)
