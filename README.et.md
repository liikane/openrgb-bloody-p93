# Tegin hiirest vilkuri

### Bloody P93 RGB Bridge — OpenRGB 1.1 laiendus

**Veidi lapsik, aga töötab: muutsime hiire tähelepanu püüdvaks valgusmärguandeks.** OpenRGB abil saab P93 värve juhtida, kasutada eri värvikohti ja teha kahe grupi vahelduva vilkuri. Kohalikud teavitused saavad käivitada punase/kollase märguande või rohelise õnnestumissignaali.

Kood ja katseversioonid: [GitHub](https://github.com/liikane/openrgb-bloody-p93) · [Allalaadimine](https://github.com/liikane/openrgb-bloody-p93/releases)

**Päris hiirega kinnitatud 10.11.2026:** OpenRGB näitab Bloody P93 seadet, muudab värvi ning nupud töötavad. Uue v0.2 mitme LED-koha, vilkuri ja teavituste toe riistvarakatse on veel pooleli.

### Kuidas kasutada?

1. Paigalda OpenRGB 1.1 ja [lisa DLL](https://github.com/liikane/openrgb-bloody-p93/releases) kausta `%APPDATA%\OpenRGB\plugins\`.
2. Taaskäivita OpenRGB ning luba **Settings → Bloody P93 → Enable RGB control**.
3. Sakis **Devices → Bloody P93 (community)** vali üks 15 HID-värvikohast ja muuda selle värvi.
4. Vaates **Settings → Bloody P93** kasuta nuppu **Identify next LED slot**, et näha, milline päris LED millisele järjekorranumbrile vastab.
5. Vilkuri jaoks määra grupid A/B (vaikimisi 1–7 ja 8–15), kiirus ning märgi **Flashing beacon**.
6. Teavituste jaoks märgi **Enable local notification commands** ning käivita näiteks:

```powershell
.\Send-P93Notification.ps1 -Event ALERT
.\Send-P93Notification.ps1 -Event ERROR
.\Send-P93Notification.ps1 -Event SUCCESS
```

Rakendus võtab sündmusi vastu üksnes sama arvuti pordil `127.0.0.1:45893`. E-posti, ntfy või ChatGPT-ga ühendamiseks peab vastav sündmuseallikas eraldi seda käsku käivitama.

**Täispikk dokumentatsioon:** [Kasutusjuhend](docs/KASUTUSJUHEND.md) · [HID-käskude kirjeldus (EN)](docs/HID_PROTOCOL.md) · [English Manual](docs/USER_MANUAL.md).

**Ohutus:** plugin muudab ainult RGB-valgustust, mitte hiirenuppe, makrosid ega püsivara. Värv võib pärast programmi sulgemist alles jääda; varasema režiimi taastamiseks kasuta salvestatud Bloody WorkShop 8 profiili. Projekt ei ole Bloody ega OpenRGB ametlik toode. GPL-2.0-or-later.

## Uus: v0.2.1 säilitab seadistused

Pärast OpenRGB taaskäivitamist taastatakse **Enable RGB control**, viimati valitud 15 värvikohta, vilkuri grupid ja kiirus ning kohalike teavituste lubamine. Vilkur ise **ei käivitu automaatselt**; see tuleb soovi korral uuesti sisse lülitada. Kasutaja saab RGB-juhtimise linnukese eemaldamisega salvestatult välja lülitada.

Tarkvara kasutab Windowsi Winsocki ega nõua eraldi Qt Network DLL-i. Seaded salvestatakse kohalikku kasutajaprofiili INI-faili. Uue versiooni funktsioonide tegelik käitumine tuleb enne ametlikku avaldamist hiirel kontrollida.
