# Bloody P93 RGB Bridge – kasutusjuhend

**Süsteem:** Windows 10/11, OpenRGB **1.1**, Bloody **P93**.  
**Plugin:** [GitHub – liikane/openrgb-bloody-p93](https://github.com/liikane/openrgb-bloody-p93)  
**Allalaadimine:** [Releases](https://github.com/liikane/openrgb-bloody-p93/releases)  
**Staatus:** kogukonna loodud lisand, Windowsi pärisseadmel proovitud. Pole Bloody või OpenRGB ametlik tarkvara.

## 1. Mida see teeb?

Lisab OpenRGB seadmete loendisse **Bloody P93 (community)**, et muuta hiire RGB-valgustuse **15 HID-värvikohta** OpenRGB kasutajaliidesest. Plugin kasutab Windowsi olemasolevat HID-liidest ega vaja eraldi USB-draiverit. See **ei kirjuta ümber hiire nupumakrosid, DPI-d ega püsivara**.

Testitud seadme USB ID on `09DA:31DE`, kasutatav HID-liides `MI_02/COL04`. Teisi Bloody mudeleid see plugin ei juhi.

## 2. Paigaldamine

1. Laadi alla oma OpenRGB 1.1-ga sobiv Windowsi `OpenRGBBloodyP93Plugin.dll` faili versioon [GitHub Releasesist](https://github.com/liikane/openrgb-bloody-p93/releases). Kontrolli, et tegemist oleks selle projekti avaldatud väljalaskega.
2. Sule OpenRGB **täielikult**, ka süsteemisalvest. Vajaduse korral vali tray-ikooni menüüst **Exit**.
3. Kopeeri DLL järgmisse kausta (aadressirea kaudu):
   
   `%APPDATA%\OpenRGB\plugins\`

   Vajaduse korral loo `plugins` kaust. Alternatiivina kasuta OpenRGB enda **Settings → Plugins** importimist.
4. Käivita OpenRGB uuesti. Plugin lisab seadistustesse vaate **Bloody P93** ning seadmete hulka **Bloody P93 (community)**, kui vastav hiir on ühendatud.

DLL-i ei ole vaja registreerida Windowsi süsteemikaustas. Pluginat pole tarvis käivitada administraatorina.

## 3. Esimene kasutuskord

1. Ava OpenRGB-s **Settings → Bloody P93**.
2. Veendu, et näidatakse `Bloody P93 connected`. Kui hiirt ei leita, vajuta **Retry device detection**.
3. Märgi **Enable RGB control (experimental)**. Alles see lubab valgustuskäskude saatmise.
4. Mine sakile **Devices** ja vali vasakult **Bloody P93 (community)**.
5. Vali keskel **All RGB lights** ala (värviline ruut).
6. Vali parempoolsest värvirattast värv või sisesta **Hex** väljale näiteks `A000FF` (lilla).
7. Vajuta **Apply Colors To Selection**. Kui kogu valik on juba aktiivne, võib värv muutuda kohe. **Apply All Devices** muudab ka teisi OpenRGB seadmeid, seega kasuta seda vaid teadlikult.

Näide: lilla = `#A000FF` = R 160, G 0, B 255.

## 4. LED-ide eraldi juhtimine ja vilkur

Uus v0.2 plugin näitab OpenRGB **Devices** vaates 15 värvikohta nimega **HID slot 1–15**. Värvikohti saab USB-aruandes eraldi määrata, kuid nende vastavus hiire füüsilistele LED-idele vajab kaardistamist.

1. Ava **Settings → Bloody P93**, luba RGB juhtimine.
2. Vajuta **Identify next LED slot (yellow)**. Hiire üks protokollikoht süttib kollaselt ja kuvatakse selle number. Korda kuni 15. kohani, märkides üles, milline füüsiline valgus millise numbriga muutub.
3. Sisesta **Beacon group A** ja **Beacon group B** väljadesse vastavalt hiire kahe külje tegelikud LED-numbrid, eraldades need komadega. Algväärtused on 1–7 ja 8–15; need ei pruugi vastata hiire vasakule ja paremale küljele.
4. Muuda **Beacon interval** (120–2000 ms) ja märgi **Flashing beacon**. Kollane vilkur vaheldub kahe LED-grupi vahel.
5. Lõpetamiseks eemalda vilkuri märge ja vajuta vajadusel **Restore selected OpenRGB colors**.

**Teavituste ühendamine:** märgi eraldi **Enable local notification commands**, mis avab ainult sama arvuti pordi `127.0.0.1:45893`. Projekti kaustas käivita PowerShelliga näiteks:

```powershell
.\Send-P93Notification.ps1 -Event ALERT    # Kollane vahelduv vilkumine 5 s
.\Send-P93Notification.ps1 -Event ERROR    # Punane vahelduv vilkumine 5 s
.\Send-P93Notification.ps1 -Event SUCCESS  # Roheline valgus 1,8 s
.\Send-P93Notification.ps1 -Event STOP     # Taasta OpenRGB valitud värvid
```

Nii saab näiteks ntfy sõnumit töötlev kohalik skript hiire märguande käivitada. Plugin ise ei ühendu ntfy serveriga ega tuvasta automaatselt ChatGPT vastuse valmimist.

Vaata ka [täielikku HID-käskude kirjeldust](HID_PROTOCOL.md).

## 5. Nupud, valgusrežiimid ja profiilid

- **Direct** võimaldab nüüd määrata 15 HID-kohta eri värvi. Füüsiliste LED-ide ja värvikohtade täpne vastavus vajab testimist.
- **Speed** ja **Brightness** on OpenRGB Direct-režiimis hallid. Vilguri kiirus on eraldi seadistatav **Beacon interval** väljal.
- OpenRGB **Save Profile** salvestab OpenRGB tarkvaralise profiili; teade **Saving Not Supported** tähendab, et plugin ei salvesta valgustust hiire püsiprofiili.
- Pluginat **välja lülitades** peatuvad uued värvikäsud, kuid viimati seatud värv võib jääda hiirele. Endise valgusrežiimi taastamiseks kasuta oma salvestatud **Bloody WorkShop 8** profiili.
- Ära muuda samaaegselt Bloody WorkShop 8-s ja OpenRGB-s hiire valgustust: käsud võivad üksteist üle kirjutada. Bloody ekraanipildi- ja nupumakrosid pole vaja ümber seadistada.

## 6. Ohutu kiire test

- [ ] `Settings → Bloody P93` näitab ühendatud hiirt.
- [ ] Pärast `Enable RGB control` märkimist muutub näiteks lilla `A000FF` punaseks `FF0000` ja tagasi.
- [ ] Hiire põhiklahvid, rullik ja olemasolev ekraanipildi makro töötavad.
- [ ] Plugina keelamisel ei muudeta enam uut värvi.
- [ ] Pärast OpenRGB taaskäivitamist saab plugina uuesti lubada.
- [ ] Soovi korral kontrolli uuesti pärast Windowsi taaskäivitust.

**Päristest 10.11.2026:** kasutaja kinnitas, et hiir ilmub OpenRGB-s, **värv muutub ja hiirenupud töötavad**. Uue v0.2 LED-ide erijuhtimise ja vilkuri päristest on veel tegemata.

## 7. Tõrkeotsing

| Probleem | Kontroll |
| --- | --- |
| Pluginat pole Settingsi all | Veendu, et DLL on `%APPDATA%\OpenRGB\plugins\` kaustas ja OpenRGB 1.1 on pärast kopeerimist täielikult taaskäivitatud |
| `Bloody P93 (community)` ei ilmu | Kontrolli, kas kasutad päriselt Bloody P93 mudelit (USB `09DA:31DE`); pluginaseadetes kasuta **Retry device detection** |
| Näed hiirt, kuid värv ei muutu | Märgi **Enable RGB control**, vali värviline LED-ruut ja vajuta **Apply Colors To Selection** |
| Värv muutub tagasi | Teine RGB-programm (nt Bloody WorkShop 8) võib samal ajal valgustust kirjutada; kontrolli, et ainult üks juhiks valgustust |
| PawnIO / I2C hoiatus | Bloody P93 HID-juhtimine ei vaja PawnIO-d; hoiatust võib selle kasutusjuhtumi puhul ignoreerida |
| DLL blokeeritakse Windowsis | Kontrolli faili päritolu ja väljalaske kontrollsummat. Ära lülita üksnes plugina pärast Smart App Controli üldiselt välja |
| Hiire valgus jäi soovimatuks | Lülita plugin välja ja taasta valgustus Bloody WorkShop 8-s salvestatud profiilist |
| Hiir ei reageeri | Sulge OpenRGB, ühenda hiir uuesti ning proovi; kui viga püsib, eemalda plugin ja ava probleemiraport |

Diagnostikalogid: `%APPDATA%\OpenRGB\logs\`. Nendes ei pruugi olla kirjutatavate RGB-pakettide sisu. Ära lisa veateatele terviklikku USB-liikluse logi ega paroole sisaldavaid andmeid.

## 8. Eemaldamine

1. Sulge OpenRGB täielikult.
2. Kustuta ainult `%APPDATA%\OpenRGB\plugins\OpenRGBBloodyP93Plugin.dll` (või eemalda plugin OpenRGB seadete kaudu).
3. Käivita OpenRGB uuesti.
4. Taasta soovi korral varasem valgus Bloody WorkShop 8 salvestatud profiilist. **Hiire nupumakrode taastamist tavaliselt vaja ei ole**, sest plugin neid ei kirjuta.

## 9. Arendajale

Lähtekood, lähtefailid, CI-ehitused ja väljalasked on [GitHubis](https://github.com/liikane/openrgb-bloody-p93). Kasutusel on OpenRGB 1.1 Plugin API 5, Qt 6.8.3 ja Windowsi HID Feature-reporti pikkusega 64 baiti.

Probleemid ja täiendusettepanekud: [GitHub Issues](https://github.com/liikane/openrgb-bloody-p93/issues). Uut HID seadmetuge ei tohiks katsetada tundmatute käskudega ega firmware uuendustega. Litsents: GPL-2.0-or-later.

## Seadistuste taastamine pärast OpenRGB taaskäivitamist (v0.2.1)

Plugin jätab meelde **Enable RGB control** valiku, kõik 15 HID-värvi, vilkuri grupid, kiiruse ja kohalike teavituste lubamise. Need taastatakse järgmisel OpenRGB käivitamisel, kui hiir on ühendatud. RGB-juhtimise linnukese eemaldamine jätab sätte välja ka järgmiseks käivituseks.

**Vilkur ei käivitu automaatselt** pärast OpenRGB taaskäivitamist, et vältida ootamatut vilkumist. Vajaduse korral märgi uuesti **Flashing beacon**. Teavituste kuulamine toimub ainult kasutaja lubamisel.

Seaded hoitakse kasutaja profiili kohalikus INI-failis. Plugin kasutab Windowsi Winsocki ja ei vaja eraldi Qt Network DLL-i.
