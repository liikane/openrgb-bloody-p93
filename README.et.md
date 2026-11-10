# Tegin hiirest vilkuri

**Bloody P93 hiire OpenRGB plugin**

*Arvuti annab hiire valgustusega märku, kui töö saab valmis või miski nõuab tähelepanu.*

Ja ingliskeelne nimi on **True Mouse Art**. Sest ega igal väikesel tehnilisel eksperimendil ei pea olema igav nimi.

Mängurihiirel oli kaheksa LED-i, aga nende peamine töö oli lihtsalt särada. Mõtlesime, et miks peaks hiir kogu aeg vait olema, kui arvuti võiks tema abil märku anda? Töö sai valmis — hiir läheb roheliseks. Midagi läks viltu — punane. Arvuti vajab tähelepanu — hiir vilgub kollaselt. Ekraanile ei ilmu tüütut hüpikakent ja klaviatuurilt ei pea käsi tõstma. Väike asi, aga paras annus *tegelikku hiirekunsti*.

Projekt on vabavaraline OpenRGB 1.1 laiendus Bloody P93 hiirele. Ingliskeelne alapealkiri on **“I Turned My Mouse into a Flashing Beacon!”**.

[**Lähtekood GitHubis**](https://github.com/liikane/openrgb-bloody-p93) · [Allalaadimine](https://github.com/liikane/openrgb-bloody-p93/releases) · [English](README.md) · [Kasutusjuhend](docs/KASUTUSJUHEND.md)

## Uus: püsiv vilkur ja tavavärvid (v0.5)

Kui arvutist eemal olles tuleb häire, jääb hiir vilkuma. Kui saabub kaks eri teadet, vahelduvad nende värvipaarid. Kinnita teated klahvidega Ctrl + Shift + F12 või OpenRGB nupuga Acknowledge all alerts. Pärast kinnitamist ei jää hiir pimedaks: kõik kaheksa LED-i näitavad pidevalt pöörlevat värvijada. [Täpsem juhend](docs/PERSISTENT_ALERTS.md).

## Kas ka teiste tootjate hiirtega?

Tasub katsetada ja uurida: eri tootjate mängurihiirtel võib olla sarnane USB/HID-kontroller ja RGB-valgustuse protokoll. Võrdle kõigepealt USB VID/PID tunnuseid, HID-kogumeid, aruannete pikkust ja tootja rakenduse valgustuskäske. **Ära saada Bloody P93 käske tundmatule hiirele.** See plugin toetab praegu ainult Bloody P93 mudelit `09DA:31DE`; muud seadmed vajavad eraldi valideeritud tuge.

## Kus hiire LED-id on?

![Hiire ülaltvaade ja LED-ide numbrid](docs/mouse-led-map.svg)

Hiirel on **8 füüsilist LED-i**. OpenRGB näitab ainult kaheksat; HID-protokolli ülejäänud värvikohad **9–15** ei vasta hiire füüsilistele tuledele.

Kõige nähtavam on **LED 1 ehk rullik**. Hiire logo valgustavad **7 ja 8 koos**.

[**LED → SLOT → HID-baitide tabel ja skeem**](docs/LED_MAP.md)

## Vilkur, mis ei ole päris politseiauto

Esialgne efekt vaheldub kahe grupi vahel:

- **A: LED 1 + 4** — rullik ja vahetult selle taga olev LED.
- **B: LED 2 + 3 + 5 + 6 + 7 + 8** — ülejäänud valgustid, sh logo.

Kollane vilgub ühes grupis, siis teises. Kiirus on seadistatav. Arvutil pole sireeni ja hiirega liikluses eelisõigust ka ei saa, aga tähelepanu suudab see küll tõmmata.

## Värvid ja vilkumiskiirus

Ava **Settings → Bloody P93**. Väljad **Group A color** ja **Group B color** avavad kumbki värvivalikudialoogi. Mõlemale vilkumisgrupile saad määrata eri värvi, näiteks A kollaseks ja B siniseks. **Beacon interval** määrab vaheldumise kiiruse 400–2000 ms; väiksem number tähendab kiiremat vilkumist. Seaded salvestatakse.

Käsitsi vilkur kasutab valitud värve. Häired vilguvad kuni kinnitamiseni oma värvipaaridega: ERROR punane-kollane, ALERT punane-sinine, SUCCESS roheline-valge ja NOTICE roheline-kollane.

## Kasutamine

1. Laadi [Releases](https://github.com/liikane/openrgb-bloody-p93/releases) lehelt sobiv `OpenRGBBloodyP93Plugin.dll`.
2. Sule OpenRGB täielikult ja kopeeri DLL kausta `%APPDATA%\OpenRGB\plugins`.
3. Käivita OpenRGB ning ava **Settings → Bloody P93** ja luba **Enable RGB control**.
4. Vaates **Devices → Bloody P93 (community)** saad kaheksat LED-i eraldi värvida.
5. Vilkumiseks märgi **Flashing beacon** ning soovi korral muuda intervalle ja LED-gruppe.

RGB-seaded säilivad. Käsitsi käivitatud vilkur ei taastu, kuid kinnitamata häired taastuvad OpenRGB käivitamisel ja vilguvad edasi.

### Teavitused

Kui lubad **Enable local notification commands**, saab mõni muu kohalik programm saata hiirele käsu:

```powershell
.\Send-P93Notification.ps1 -Event ALERT
.\Send-P93Notification.ps1 -Event ERROR
.\Send-P93Notification.ps1 -Event SUCCESS
.\Send-P93Notification.ps1 -Event ACK
```

`ALERT` vilgutab kollast, `ERROR` punast, `SUCCESS` paneb kõik kaheksa LED-i rohelise-valgega vilkuma kuni kinnitamiseni. Võimalik on siduda see ntfy või kohalike tööskriptidega. **ChatGPT vastuse valmimist plugin ise automaatselt ei tuvasta** — selleks peab eraldi sündmuse allikas käsu käivitama.

## Tehnika ja juhendid

- [Eestikeelne põhjalik kasutusjuhend](docs/KASUTUSJUHEND.md)
- [LED-numbrid, asukohad ja HID-baidid](docs/LED_MAP.md)
- [Täpsed RGB-käsud](docs/HID_PROTOCOL.md)
- [Windowsi teavitustega ühendamise plaan](docs/WINDOWS_NOTIFICATIONS.md)
- [Ingliskeelne kasutusjuhend](docs/USER_MANUAL.md)
- [Testitulemused](docs/VALIDATION.md)
- [Portfooliolugu](docs/CASE_STUDY.md)

Hiire RGB-muutus ja nupud on tegeliku seadmega kontrollitud. Uute LED-gruppide füüsilist vaheldumist tuleb eraldi kinnitada. Nupumakrosid, DPI-seadeid ega püsivara plugin ei kirjuta.

Vajalikud on **Windows ja OpenRGB 1.1**; avaliku projekti litsents on **GPL-2.0-or-later**. Tegemist on sõltumatu hobi- ja katseprojektiga, mitte Bloody ega OpenRGB ametliku tootega.

*Kui hiirest sai vilkur, siis järgmine küsimus on: mida kõike võiks klaviatuur veel meile öelda?*

## NTFY ja Windowsi süsteemiteated

Lisatud on väike **Pythonis kirjutatud taustasild**, mis kuulab olemasolevat NTFY kanalit ning nelja valitud Windowsi sündmuslogi teadet. See muudab need hiirel roheliseks kinnituseks või kollaseks/punaseks vilkuriks. Sild kasutab ainult kohalikku UDP-ühendust, ei talleta teavituste sisu ja saab käivituda Windowsisse sisselogimisel.

[Paigaldus- ja kasutusjuhend](integrations/ntfy/README.md) · [HID-iga kinnitatud test](integrations/ntfy/VALIDATION.md) · [Windowsi hüpikteavituste tulevikuplaan](docs/WINDOWS_NOTIFICATIONS.md). Windowsi sündmuslogi ei võrdu veel kogu Windowsi teavituskeskusega.
