# True Mouse Art: ntfy + Windows events → OpenRGB P93

**Free / open-source. Windows 10/11. Python 3. Standard library only.**

A minimal local notification bridge that subscribes to **ntfy** messages and a few selected Windows Event Log events, then sends compact ASCII event codes to the **True Mouse Art / Bloody P93 OpenRGB plugin** over `127.0.0.1:45893`.

This is a small interim integration. The eventual standalone **Vilgutaja** app and OpenRGB-wide bridge share the planned roadmap: [#6](https://github.com/liikane/openrgb-bloody-p93/issues/6), [#7](https://github.com/liikane/openrgb-bloody-p93/issues/7), [#8](https://github.com/liikane/openrgb-bloody-p93/issues/8).

## Eestikeelne lühijuhend

LAURIDELLis kasutab sild juba olemasolevat ntfy kanali seadistusfaili `Portable\Automation\Summary\settings.json`. Kanali nime või parooli **ei salvestata GitHubi projekti**. Windowsis käivitatakse taustaprogramm `pythonw.exe` abil, nii et käsureaaken ei jää ette.

### Seadistamine
1. Paigalda OpenRGB 1.1 ja [True Mouse Art plugin](../../README.et.md).
2. Ava **Settings → Bloody P93** ning märgi **Enable RGB control** ja **Enable local notification commands**.
3. Kontrolli, et ntfy server, kanal ja vajaduse korral token on kohalikus JSON-failis (aluseks `Automation/Summary/settings.json`).
4. Kontroll:

   ```powershell
   python .\integrations\ntfy\bridge.py --check
   python .\integrations\ntfy\test_bridge.py
   ```

5. Käivita:

   ```powershell
   pythonw .\integrations\ntfy\bridge.py
   ```

6. Automaatselt sisselogimisel käivitamiseks:

   ```powershell
   .\integrations\ntfy\Install-BridgeTask.ps1
   ```

7. Peatamiseks või eemaldamiseks:

   ```powershell
   .\integrations\ntfy\Uninstall-BridgeTask.ps1
   ```

Paigaldus-/eemaldusskript muudab üksnes nimega **True Mouse Art Notification Bridge** Windowsi ajastatud ülesannet. Hiire nupumakrosid, püsivara ega süsteemseid turvaseadeid ei muudeta.

### Mida ntfy sõnum teeb?

| NtFy sõnum | RGB sündmus |
|---|---|
| `Tags: success`, `p93_success` või pealkiri `valmis`/`done` | `SUCCESS` — roheline |
| `Tags: error`, `p93_error` või pealkiri `viga`/`failed` | `ERROR` — punane vilkur |
| `Tags: warning`, `p93_alert` või kõrge `Priority: 4/5` | `ALERT` — sinu A/B värvides vilkur |
| Tavaline teade (`Priority: 3`) | `NOTICE` — A/B vilkur |
| Vaikne teade (`Priority: 1/2`) | Ignoreeritakse, välja arvatud erimärgise korral |

Teavituse **teksti ja pealkirja ei saadeta hiirele ega salvestata logisse**. Sild vaatab ainult pealkirja märksõnu, silte ja prioriteeti, et valida üks viiest sündmusekoodist. ntfy tellimuse striim kasutab HTTPS-i ja olemasoleva kanali õigusi. Hiirele liigub ainult kohalik UDP sündmusekood.

### Windowsi teavitused

Esimene versioon jälgib **nelja Windowsi süsteemisündmust**, mitte kogu Windowsi teavituskeskuse (Toast) sõnumeid:

| Windowsi sündmuslogi | ID | Hiire märguanne |
|---|---:|---|
| Microsoft Defender tuvastas ohu | 1116 | `ERROR` (punane) |
| Microsoft Defender rakendas kaitsetegevuse | 1117 | `ALERT` (tähelepanu, tegevuse tulemus vajab kontrolli) |
| Windows Update paigaldas uuenduse | 19 | `SUCCESS` (roheline) |
| Windows Update paigaldus ebaõnnestus | 20 | `ERROR` (punane) |

Need tellimused kasutavad Windowsi `EvtSubscribe` liidest, **ainult tulevasi sündmusi**, ilma ketta perioodilise skannimise või sündmuste teksti lugemiseta. Jälgimise saab peatada argumendiga `--no-windows-events`. Kogu Windowsi Toast-teavituskeskuse tugi vajab eraldi pakendatud rakendust ja kasutaja selgesõnalist juurdepääsuluba — see on [roadmap issue #5](https://github.com/liikane/openrgb-bloody-p93/issues/5).

### Testimine ja veaotsing

- Lokaalse käsu test, nt `python .\integrations\ntfy\bridge.py --test ALERT` (ei vaja ntfy ühendust).
- NTFY kaudu test: saada samasse teemasse `Tags: warning` ja `Priority: 4` teade. Ka ntfy telefoniäpp võib selle vastu võtta.
- Logi asub kasutaja arvutis: `Portable\Automation\OpenRGB-Ntfy-Bridge\bridge.log` (piiratud suurusega, ainult sündmuse liik, mitte sisu).
- Kui OpenRGB ei võta teateid vastu, veendu plugina `Enable local notification commands` linnukeses ja et `127.0.0.1:45893` kuulab.
- Sild ei muuda NTFY serveris ühtegi sõnumit ega ei vaja uusi tasulisi teenuseid.
- Käivitustõrke korral loe ainult logi veatüüpi; ära avalda oma privaatset teemat, tokenit ega tooreid teavitussõnumeid.

**Tehniline piirang:** UDP ei anna kinnitust, et hiir füüsiliselt süttis. Edukat NTFY → OpenRGB → P93 rada on kontrollitud hiire HID-vastustest. Windowsi 4 sündmuse tellimist on kontrollitud, kuid tegelikke Defender/Update sündmusi ei tekitatud katse eesmärgil.
