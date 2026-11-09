# Bloody P93 OpenRGB plugin – eesti keeles

Selle projekti eesmärk on kuvada Bloody P93 hiir **OpenRGB 1.1** seadmete nimekirjas ja juhtida selle valgustust, säilitades olemasolevad nupumakrod.

Windowsi masinal LAURIDELL on juba edukalt testitud otse-HID käsud: lilla püsivalgus ning punased/rohelised vilgutused. Plugin on nendest katsetest lähtuv **esialgne C++ arendus**.

## Kasutamine pärast DLL-i edukat ehitamist

1. Laadi [GitHubi avalikust katseversioonist v0.1.1-alpha.1](https://github.com/liikane/openrgb-bloody-p93/releases/tag/v0.1.1-alpha.1) DLL `OpenRGBBloodyP93Plugin.dll`.
2. Paigalda see OpenRGB pluginate halduris.
3. Ava **Bloody P93 RGB Bridge** seaded.
4. Lülita sisse **Enable RGB control (experimental)**.
5. Vali seadmete hulgast **Bloody P93 (community)** ja värv.

Plugin ei saada alguses hiirele ühtegi käsku. Testi käivitamiseks tuleb juhtimine eraldi lubada. Värvirežiimi seadmine võib muuta hiire senist valgustust; salvesta Bloody WorkShop 8 profiil enne esimest proovimist.

**NB!** See on uus katseline plugin, mitte ametliku OpenRGB galerii juba avaldatud täiendus. Ametlikus kataloogis ilmumine nõuab selle haldajate heakskiitu.

Lähtekoodi litsents: GPL-2.0-or-later.
