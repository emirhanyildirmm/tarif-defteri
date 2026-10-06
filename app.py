
import requests
import json

from bs4 import BeautifulSoup
from flask import Flask, jsonify, send_from_directory


# ============================================================
# TARİF SINIFI
# ============================================================

class Tarif:

    def __init__(
        self,
        yemek_adi,
        malzemeler,
        pisirme_suresi,
        gorsel
    ):
        self.yemek_adi = yemek_adi
        self.malzemeler = malzemeler
        self.pisirme_suresi = pisirme_suresi
        self.gorsel = gorsel

    def TarifiGoster(self):

        print("----------------------------")
        print("Yemek:", self.yemek_adi)

        print("Malzemeler:")

        for malzeme in self.malzemeler:
            print("-", malzeme)

        print(
            "Pişirme Süresi:",
            self.pisirme_suresi
        )

        print(
            "Görsel:",
            self.gorsel
        )

        print("----------------------------")


# ============================================================
# YEMEK.COM'DAN TARİF ÇEKİYORUM
# ============================================================

def tarif_cek(url):

    # Web sitesine istek gönderiyorum.
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=15
    )

    # Gelen HTML kodunu okuyorum.
    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # Tarif adını buluyorum.
    baslik = soup.find("h1")

    if not baslik:
        raise Exception(
            "Tarif adı bulunamadı."
        )

    yemek_adi = baslik.get_text(
        strip=True
    )


    # Malzeme başlığını buluyorum.
    malzeme_basligi = soup.find(
        lambda tag:
        tag.name in ["h2", "h3"]
        and
        "malzeme"
        in tag.get_text(
            " ",
            strip=True
        ).lower()
    )

    malzemeler = []

    if malzeme_basligi:

        malzeme_listesi = (
            malzeme_basligi.find_next("ul")
        )

        if malzeme_listesi:

            for li in malzeme_listesi.find_all(
                "li"
            ):

                malzeme = li.get_text(
                    " ",
                    strip=True
                )

                if malzeme:
                    malzemeler.append(
                        malzeme
                    )


    # JSON-LD verisini buluyorum.
    json_verisi = soup.find(
        "script",
        type="application/ld+json"
    )

    if not json_verisi:
        raise Exception(
            "Tarif JSON verisi bulunamadı."
        )


    try:

        tarif_verisi = json.loads(
            json_verisi.string
        )

    except Exception:

        raise Exception(
            "JSON verisi okunamadı."
        )


    # Bazı sitelerde JSON-LD tek nesne,
    # bazı durumlarda liste olabilir.
    if isinstance(
        tarif_verisi,
        list
    ):

        tarif_verisi = next(
            (
                veri
                for veri in tarif_verisi
                if isinstance(
                    veri,
                    dict
                )
                and
                veri.get(
                    "@type"
                )
                in [
                    "Recipe",
                    ["Recipe"]
                ]
            ),
            tarif_verisi[0]
        )


    pisirme_suresi = tarif_verisi.get(
        "cookTime",
        "Belirtilmemiş"
    )


    gorsel = tarif_verisi.get(
        "image",
        ""
    )


    if isinstance(
        gorsel,
        list
    ):

        if len(gorsel) > 0:
            gorsel = gorsel[0]
        else:
            gorsel = ""


    return Tarif(
        yemek_adi,
        malzemeler,
        pisirme_suresi,
        gorsel
    )


# ============================================================
# TARİF LİNKLERİNİ BULUYORUM
# ============================================================

def tarifleri_getir():

    ana_url = (
        "https://yemek.com/tarif/"
    )

    # Tarifler sayfasına istek gönderiyorum.
    response = requests.get(
        ana_url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=15
    )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    linkler = soup.find_all(
        "a",
        href=True
    )

    tarif_url_listesi = []


    for link in linkler:

        href = link["href"]

        if href.startswith(
            "/tarif/"
        ):

            tam_url = (
                "https://yemek.com"
                + href
            )

            if tam_url not in tarif_url_listesi:

                tarif_url_listesi.append(
                    tam_url
                )


    tarifler = []


    for url in tarif_url_listesi:

        if len(tarifler) >= 10:
            break

        try:

            tarif = tarif_cek(url)

            tarifler.append(
                tarif
            )

        except Exception:

            continue


    return tarifler


# ============================================================
# FLASK
# ============================================================

app = Flask(
    __name__
)


@app.route(
    "/tarifler",
    methods=["GET"]
)
def tarifleri_api():

    tarifler = tarifleri_getir()

    veriler = []


    for tarif in tarifler:

        veriler.append({

            "yemek_adi":
                tarif.yemek_adi,

            "malzemeler":
                tarif.malzemeler,

            "pisirme_suresi":
                tarif.pisirme_suresi,

            "gorsel":
                tarif.gorsel

        })


    return jsonify(
        veriler
    )


@app.route("/")
def ana_sayfa():

    return send_from_directory(
        ".",
        "index.html"
    )


@app.route(
    "/<path:dosya_adi>"
)
def frontend_dosyasi(
    dosya_adi
):

    return send_from_directory(
        ".",
        dosya_adi
    )
