import requests
import json
import os

from bs4 import BeautifulSoup
from flask import Flask, jsonify, send_from_directory


# Tarif sınıfını oluşturuyorum.
class Tarif:
    def __init__(self, yemek_adi, malzemeler, pisirme_suresi, gorsel):
        self.yemek_adi = yemek_adi
        self.malzemeler = malzemeler
        self.pisirme_suresi = pisirme_suresi
        self.gorsel = gorsel

    # Tarif bilgilerini ekrana yazdırıyorum.
    def TarifiGoster(self):
        print("----------------------------")
        print("Yemek:", self.yemek_adi)
        print("Malzemeler:")

        for malzeme in self.malzemeler:
            print("-", malzeme)

        print("Pişirme Süresi:", self.pisirme_suresi)
        print("Görsel:", self.gorsel)
        print("----------------------------")


# Yemek.com üzerindeki bir tarif sayfasından bilgileri çekiyorum.
def tarif_cek(url):

    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=15
    )

    soup = BeautifulSoup(response.text, "html.parser")

    # Sayfanın JSON-LD verilerini kontrol ediyorum.
    tarif_verisi = None

    json_scriptleri = soup.find_all(
        "script",
        type="application/ld+json"
    )

    for script in json_scriptleri:

        try:
            veri = json.loads(script.string or script.get_text())

            veriler = veri if isinstance(veri, list) else [veri]

            for item in veriler:

                # JSON-LD içerisinde @graph varsa onu da kontrol ediyorum.
                if isinstance(item, dict) and "@graph" in item:

                    for graph_item in item["@graph"]:

                        if isinstance(graph_item, dict):

                            tip = graph_item.get("@type", "")

                            if (
                                tip == "Recipe"
                                or (
                                    isinstance(tip, list)
                                    and "Recipe" in tip
                                )
                            ):
                                tarif_verisi = graph_item
                                break

                if tarif_verisi:
                    break

                if isinstance(item, dict):

                    tip = item.get("@type", "")

                    if (
                        tip == "Recipe"
                        or (
                            isinstance(tip, list)
                            and "Recipe" in tip
                        )
                    ):
                        tarif_verisi = item
                        break

            if tarif_verisi:
                break

        except Exception:
            continue

    # Sayfa gerçek bir yemek tarifi değilse hata veriyorum.
    if tarif_verisi is None:
        raise ValueError("Bu sayfa gerçek bir tarif değil.")

    # Yemek adını alıyorum.
    yemek_adi = tarif_verisi.get("name", "").strip()

    if not yemek_adi:
        raise ValueError("Yemek adı bulunamadı.")

    # Malzemeleri alıyorum.
    malzemeler = tarif_verisi.get(
        "recipeIngredient",
        []
    )

    if not isinstance(malzemeler, list):
        malzemeler = []

    malzemeler = [
        str(malzeme).strip()
        for malzeme in malzemeler
        if str(malzeme).strip()
    ]

    # Pişirme süresini alıyorum.
    pisirme_suresi = tarif_verisi.get(
        "cookTime",
        "Belirtilmemiş"
    )

    if not pisirme_suresi:
        pisirme_suresi = "Belirtilmemiş"

    # Yemek görselini alıyorum.
    gorsel = tarif_verisi.get(
        "image",
        ""
    )

    # Görsel liste olarak geldiyse ilk görseli alıyorum.
    if isinstance(gorsel, list):

        if len(gorsel) > 0:
            gorsel = gorsel[0]
        else:
            gorsel = ""

    # Görsel sözlük olarak geldiyse URL bilgisini alıyorum.
    if isinstance(gorsel, dict):

        gorsel = (
            gorsel.get("url")
            or gorsel.get("contentUrl")
            or ""
        )

    # Görsel URL'sinin gerçekten metin olduğundan emin oluyorum.
    if not isinstance(gorsel, str):
        gorsel = ""

    return Tarif(
        yemek_adi,
        malzemeler,
        pisirme_suresi,
        gorsel
    )


# Yemek.com tarifler sayfasından tarif bağlantılarını buluyorum.
def tarif_linklerini_getir():

    url = "https://yemek.com/tarif/"

    response = requests.get(
        url,
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

        if not href.startswith("/tarif/"):
            continue

        # Aynı site adresini oluşturuyorum.
        tam_url = "https://yemek.com" + href

        if tam_url not in tarif_url_listesi:
            tarif_url_listesi.append(tam_url)

    return tarif_url_listesi


# Tarifleri oluşturuyorum.
tarifler = []

hedef_tarif_sayisi = 10

try:

    tarif_url_listesi = tarif_linklerini_getir()

    for url in tarif_url_listesi:

        if len(tarifler) >= hedef_tarif_sayisi:
            break

        try:

            tarif = tarif_cek(url)

            tarifler.append(tarif)

            print(
                len(tarifler),
                ". tarif:",
                tarif.yemek_adi
            )

        except Exception as hata:

            # Kategori veya uygun olmayan sayfaları atlıyorum.
            print(
                "Sayfa atlandı:",
                url,
                "| Sebep:",
                hata
            )

except Exception as hata:

    print("Tarifler alınamadı:", hata)


# Flask uygulamasını oluşturuyorum.
app = Flask(__name__)


# Tarifleri JSON olarak frontend'e gönderiyorum.
@app.route("/tarifler", methods=["GET"])
def tarifleri_getir():

    veriler = []

    for tarif in tarifler:

        veriler.append({
            "yemek_adi": tarif.yemek_adi,
            "malzemeler": tarif.malzemeler,
            "pisirme_suresi": tarif.pisirme_suresi,
            "gorsel": tarif.gorsel
        })

    return jsonify(veriler)


# Ana sayfayı gösteriyorum.
@app.route("/")
def ana_sayfa():

    return send_from_directory(
        os.path.dirname(__file__),
        "index.html"
    )


# CSS ve JavaScript dosyalarını gösteriyorum.
@app.route("/<path:dosya_adi>")
def frontend_dosyasi(dosya_adi):

    return send_from_directory(
        os.path.dirname(__file__),
        dosya_adi
    )
