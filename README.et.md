# Tegin hiirest vilkuri

**Bloody P93 hiire OpenRGB plugin**

*Arvuti annab hiire valgustusega märku, kui töö saab valmis või miski nõuab tähelepanu.*

Ja ingliskeelne nimi on **True Mouse Art**. Sest ega igal väikesel tehnilisel eksperimendil ei pea olema igav nimi.

Mängurihiirel oli kaheksa LED-i, aga nende peamine töö oli lihtsalt särada. Mõtlesime, et miks peaks hiir kogu aeg vait olema, kui arvuti võiks tema abil märku anda? Töö sai valmis — hiir läheb roheliseks. Midagi läks viltu — punane. Arvuti vajab tähelepanu — hiir vilgub kollaselt. Ekraanile ei ilmu tüütut hüpikakent ja klaviatuurilt ei pea käsi tõstma. Väike asi, aga paras annus *tegelikku hiirekunsti*.

Projekt on vabavaraline OpenRGB 1.1 laiendus Bloody P93 hiirele. Ingliskeelne alapealkiri on **“I Turned My Mouse into a Flashing Beacon!”**.

[**Lähtekood GitHubis**](https://github.com/liikane/openrgb-bloody-p93) · [Allalaadimine](https://github.com/liikane/openrgb-bloody-p93/releases) · [English](README.md) · [Kasutusjuhend](docs/KASUTUSJUHEND.md)

## Kus hiire LED-id on?

![Hiire ülaltvaade ja LED-ide numbrid](docs/mouse-led-map.svg)

Hiirel on **8 füüsilist LED-i**. OpenRGB näitab ainult kaheksat; HID-protokolli ülejäänud värvikohad **9–15** ei vasta hiire füüsilistele tuledele.

Kõige nähtavam on **LED 1 ehk rullik**. Hiire logo valgustavad **7 ja 8 koos**.

[**LED → SLOT → HID-baitide tabel ja skeem**](docs/LED_MAP.md)

## Vilkur, mis ei ole päris politseiauto

Esialgne efekt vaheldub kahe grupi vahel:

- **A: LED 1 + 4** — rullik ja kolme lisanupu alune piirkond.
- **B: LED 2 + 3 + 5 + 6 + 7 + 8** — ülejäänud valgustid, sh logo.

Kollane vilgub ühes grupis, siis teises. Kiirus on seadistatav. Arvutil pole sireeni ja hiirega liikluses eelisõigust ka ei saa, aga tähelepanu suudab see küll tõmmata.

## Kasutamine

1. Laadi [Releases](https://github.com/liikane/openrgb-bloody-p93/releases) lehelt sobiv `OpenRGBBloodyP93Plugin.dll`.
2. Sule OpenRGB täielikult ja kopeeri DLL kausta `%APPDATA%\OpenRGB\plugins\`.
3. Käivita OpenRGB ning ava **Settings → Bloody P93** ja luba **Enable RGB control**.
4. Vaates **Devices → Bloody P93 (community)** saad kaheksat LED-i eraldi värvida.
5. Vilkumiseks märgi **Flashing beacon** ning soovi korral muuda intervalle ja LED-gruppe.

RGB-lubamine ja värvid jäetakse taaskäivitamisel meelde. Vilkur ise ei hakka automaatselt uuesti vilkuma, sest hiir ei pea omanikku öösel ehmatama.

### Teavitused

Kui lubad **Enable local notification commands**, saab mõni muu kohalik programm saata hiirele käsu:

```powershell
.\Send-P93Notification.ps1 -Event ALERT
.\Send-P93Notification.ps1 -Event ERROR
.\Send-P93Notification.ps1 -Event SUCCESS
.\Send-P93Notification.ps1 -Event STOP
```

`ALERT` vilgutab kollast, `ERROR` punast, `SUCCESS` paneb kõik kaheksa LED-i ajutiselt roheliselt särama. Võimalik on siduda see ntfy või kohalike tööskriptidega. **ChatGPT vastuse valmimist plugin ise automaatselt ei tuvasta** — selleks peab eraldi sündmuse allikas käsu käivitama.

## Tehnika ja juhendid

- [Eestikeelne põhjalik kasutusjuhend](docs/KASUTUSJUHEND.md)
- [LED-numbrid, asukohad ja HID-baidid](docs/LED_MAP.md)
- [Täpsed RGB-käsud](docs/HID_PROTOCOL.md)
- [Ingliskeelne kasutusjuhend](docs/USER_MANUAL.md)
- [Testitulemused](docs/VALIDATION.md)
- [Portfooliolugu](docs/CASE_STUDY.md)

Hiire RGB-muutus ja nupud on tegeliku seadmega kontrollitud. Uute LED-gruppide füüsilist vaheldumist tuleb eraldi kinnitada. Nupumakrosid, DPI-seadeid ega püsivara plugin ei kirjuta.

Vajalikud on **Windows ja OpenRGB 1.1**; avaliku projekti litsents on **GPL-2.0-or-later**. Tegemist on sõltumatu hobi- ja katseprojektiga, mitte Bloody ega OpenRGB ametliku tootega.

*Kui hiirest sai vilkur, siis järgmine küsimus on: mida kõike võiks klaviatuur veel meile öelda?*
