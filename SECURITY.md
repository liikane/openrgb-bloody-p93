# Security notes

This plugin only supports the exact Bloody P93 USB identity and HID collection
(`VID_09DA/PID_31DE, MI_02/COL04, FF32:0218`).

No driver installation, firmware writes, button/macro configuration or
keystroke logging are used. Only previously verified 64-byte RGB Feature
reports are sent, and only after the user enables RGB control.

Please report unexpected effects via a GitHub issue, without attaching raw
USB capture files that may contain sensitive input data.

A DLL produced by an unverified build should not be distributed as an
official release.
