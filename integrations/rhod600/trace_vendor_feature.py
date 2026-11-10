#!/usr/bin/env python3
"""Capture only outbound 8-byte vendor HID reports from running ShinetekTools.

Requires optional free Frida Python library; no HID writes, USB driver, key
logging or Windows hook. Attaches to one user-mode process for a bounded time.
"""
import argparse
import time

AGENT = r"""
'use strict';
const hid = Process.findModuleByName('HID.DLL') || Process.findModuleByName('hid.dll');
const kernel = Process.getModuleByName('kernel32.dll');
function watch(name, addr, bufarg, lenarg) {
    if (!addr) return;
    Interceptor.attach(addr, {
        onEnter(args) {
            try {
                const len = args[lenarg].toInt32();
                if(len !== 8) return;
                const data = args[bufarg].readByteArray(8);
                if(data === null) return;
                const bytes = Array.from(new Uint8Array(data));
                if(bytes[0] !== 0x07) return;
                // Vendor feature commands only. Not keyboard input reports.
                if(bytes[1] < 0xF0) return;
                send({api:name, report:bytes.map(x => x.toString(16).padStart(2,'0')).join(' ')});
            } catch(e) { /* do not expose raw keyboard content */ }
        }
    });
}
if(hid) watch('HidD_SetFeature', hid.getExportByName('HidD_SetFeature'), 1, 2);
watch('WriteFile', kernel.getExportByName('WriteFile'), 1, 2);
send({ready:true});
"""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pid",required=True,type=int)
    ap.add_argument("--seconds",type=int,default=12)
    args=ap.parse_args()
    if not 1 <= args.seconds <= 60: raise ValueError("Allow 1–60 s")
    import frida
    session=frida.attach(args.pid)
    script=session.create_script(AGENT)
    hits=[]
    def on_message(message,data):
        if message.get("type")=="error":
            print("AGENT_ERROR",message.get("description","unknown"),flush=True)
        elif message.get("type")=="send":
            event=message.get("payload",{})
            if event.get("ready"):
                print("READY passive outbound 8-byte report monitor",flush=True)
            elif event.get("report"):
                hits.append(event)
                print(f"OUT {event.get('api')} {event.get('report')}",flush=True)
    script.on("message",on_message)
    try:
        script.load()
        print(f"OBSERVE_SECONDS={args.seconds}",flush=True)
        time.sleep(args.seconds)
    finally:
        try:script.unload()
        finally:session.detach()
    print(f"OUT_REPORTS={len(hits)}",flush=True)

if __name__=="__main__": main()
