
async function tarifleriGetir() {

    try {

        // Backend'den tarifleri istiyorum.
        const response =
            await fetch("/tarifler");

        // Gelen JSON verisini okuyorum.
        const tarifler =
            await response.json();

        const alan =
            document.getElementById(
                "tarifler"
            );

        alan.innerHTML = "";

        // Her tarif için bir kart oluşturuyorum.
        tarifler.forEach(tarif => {

            const kart =
                document.createElement(
                    "div"
                );

            kart.className =
                "tarif-karti";

            let malzemeListesi = "";

            // Tarifin malzemelerini ekliyorum.
            tarif.malzemeler.forEach(
                malzeme => {

                    malzemeListesi +=
                        `<li>${malzeme}</li>`;

                }
            );

            kart.innerHTML = `

                <img
                    src="${tarif.gorsel}"
                    alt="${tarif.yemek_adi}"
                >

                <div class="tarif-bilgi">

                    <h2>
                        ${tarif.yemek_adi}
                    </h2>

                    <p class="sure">
                        Pişirme Süresi:
                        ${sureyiDuzenle(
                            tarif.pisirme_suresi
                        )}
                    </p>

                    <p class="malzeme-baslik">
                        Malzemeler
                    </p>

                    <ul class="malzemeler">
                        ${malzemeListesi}
                    </ul>

                </div>
            `;

            alan.appendChild(kart);
        });

    }

    catch (hata) {

        console.error(
            "Tarifler alınırken hata oluştu:",
            hata
        );

        document.getElementById(
            "tarifler"
        ).innerHTML =
            "<p>Tarifler alınırken bir hata oluştu.</p>";
    }
}


function sureyiDuzenle(sure) {

    if (
        sure &&
        sure.startsWith("PT") &&
        sure.endsWith("M")
    ) {

        return sure
            .replace("PT", "")
            .replace("M", "")
            + " dakika";
    }

    return sure;
}


// Sayfa açıldığında tarifleri getiriyorum.
tarifleriGetir();
