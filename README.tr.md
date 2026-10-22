# tr-pii

tr-pii, Türkçe metindeki kişisel verileri bilgisayarınızda bulan ve maskeleyen, çalışma zamanı bağımlılığı olmayan bir Python kütüphanesi ve komut satırı aracıdır.

[![CI](https://github.com/YusufBeratZengin/tr-pii/actions/workflows/ci.yml/badge.svg)](https://github.com/YusufBeratZengin/tr-pii/actions/workflows/ci.yml)
[![Lisans: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[English](README.md)

## Neden

Bir LLM'e veya başka bir servise metin göndermeden önce kimlik bilgilerini kendi bilgisayarınızda temizleyin. Türkiye'ye özgü kontroller, TCKN, VKN ve TR IBAN'larını rastgele sayılardan ayırmaya yardımcı olur. Kütüphane ağ çağrısı yapmaz; telemetri ve hazır isim sözlüğü içermez.

```python
from tr_pii import fake, mask

# Sentetik veri, yalnız test için. Üretilen numaraları gerçek kimlik olarak kullanmayın.
text = f"Test kaydı: TCKN {fake.tckn(seed=7)}; dummy@example.invalid"
safe_text = mask(text)
assert safe_text == "Test kaydı: TCKN [TCKN]; [EMAIL]"
# Dış servise göndermeden önce safe_text içeriğini gözden geçirin.
```

## Kurulum

Python 3.10 veya üzeri gerekir. Depoyu indirdikten sonra:

```sh
python -m pip install .
tr-pii --version
```

Paket Hatchling ile derlenir. Kurulan kütüphane yalnız Python standart kütüphanesini kullanır. Kurulum sırasında derleme aracı için internet gerekebilir; metin işlenirken ağ bağlantısı kullanılmaz.

## Hızlı başlangıç

```python
from tr_pii import find, mask

text = "Test e-posta: dummy@example.invalid"
matches = find(text, types=["EMAIL"])
assert matches[0].type == "EMAIL"
assert text[matches[0].start:matches[0].end] == matches[0].value
assert mask(text) == "Test e-posta: [EMAIL]"
assert mask(text, style="stars") == "Test e-posta: " + "*" * 21
```

Varsayılan `tag` biçimi her bulguyu tür etiketiyle değiştirir. `stars`, ayraçlar dahil bulgunun bütün karakterlerini yıldızlar. `partial`, TCKN, VKN, posta kodu ve plakanın son iki rakamını; telefon, IBAN ve kartın son dört rakamını bırakır. E-posta, IP ve özel terimleri tamamen maskeler.

```python
from tr_pii import mask

assert mask("İZİN ve IŞIK", custom_terms=["izin", "ışık"]) == "[CUSTOM] ve [CUSTOM]"

# Bu tuz yalnız herkese açık örnek içindir. Kendi tuzunuzu çalışma anında verin.
one = mask("dummy@example.invalid", style="hash", salt="public-demo-salt")
two = mask("dummy@example.invalid", style="hash", salt="public-demo-salt")
assert one == two  # [EMAIL:<16 küçük harfli onaltılık karakter>]
```

Hash biçimi boş olmayan bir tuz ister. Tuz, tür ve ortak biçime dönüştürülen değer, uzunluklarıyla birlikte SHA-256 girdisine eklenir. Sayı ayraçları, telefon önekleri, IBAN/plaka harf boyutu, aynı IP'nin farklı yazımları ve özel terimlerin Türkçeye uygun harf değişimleri aynı etiketi verir. E-postada alan adı küçük harfe çevrilir; `@` öncesindeki harfler korunur. Tuz değişince etiketler de değişir. Bu yöntem takma adlandırmadır: kısa hash'ler çakışabilir, tekrar eden değerler ilişkilendirilebilir, tuz biliniyorsa dar bir değer kümesi tahmin yoluyla taranabilir. Tuzu gizli tutun ve sürüm kontrolüne eklemeyin.

## Komut satırı

```sh
tr-pii scan input.txt
tr-pii mask input.txt --style tag --types TCKN,VKN,IBAN,PHONE,EMAIL
tr-pii mask - --style stars < input.txt
tr-pii mask input.txt --terms-file test-terms.txt
```

`scan`, her bulgu için `type`, `start`, `end`, `value` ve `confidence` alanlarını taşıyan bir JSON satırı üretir. Çıktı ham kişisel veriyi içerir; girdiyle aynı özenle korunmalıdır. `mask`, sonuna yeni satır eklemeden maskelenmiş metni yazar. İki komut da UTF-8 dosya veya standart girdi için `-`, virgülle ayrılmış `--types` ve satır başına bir özel terim içeren UTF-8 `--terms-file` alır. Terim dosyasındaki boş satırlar atlanır. `python -m tr_pii`, `tr-pii` ile aynı şekilde çalışır.

`--style hash` için tuzu yerel ortamınızdan veya sır yöneticinizden `TR_PII_SALT` ortam değişkenine verin. Tuzun komut satırı geçmişine girmemesi için ayrı bir komut satırı seçeneği yoktur. Gerçek tuzu örneklere veya commit'lenen dosyalara yazmayın.

| Çıkış kodu | Anlamı |
| --- | --- |
| `0` | Bulgu yok |
| `3` | En az bir bulgu var; başarılı maskeleme de bu kodu döndürür |
| `2` | Geçersiz seçenek, okunamayan/UTF-8 olmayan girdi veya eksik hash tuzu |

`3` kodu sayesinde `scan`, CI kontrolü olarak kullanılabilir. Betiklerde `mask` için `3` kodunu, bulgu içeren başarılı işlem olarak ele alın. Dosya hataları, girdi yollarını veya değerlerini açığa çıkarmamak için genel bir mesajla bildirilir.

## API özeti

```python
find(text, types=None, *, custom_terms=()) -> list[Match]
mask(text, style="tag", types=None, salt=None, *, custom_terms=()) -> str
```

`Match`, değiştirilemeyen bir dataclass'tır: `type: str`, `start: int`, `end: int`, `value: str`, `confidence: float`. Konumlar özgün Python metnindeki Unicode kod noktalarını sayar; `end` eşleşmeye dahil değildir. Sonuçlar başlangıç konumuna göre sıralıdır ve çakışmaz. Çakışmada önce güven puanı yüksek olan; eşitlikte daha uzun olan, daha önce başlayan ve tür adı alfabetik olarak önce gelen kazanır. Güven puanı sabit bir öncelik ölçüsüdür; ölçülmüş olasılık değildir.

`types=None` bütün türleri açar; boş bir koleksiyon bütün türleri kapatır. Tür adlarında büyük/küçük harf ayrımı yoktur. Bilinmeyen tür, tür/terim koleksiyonu yerine tek bir metin, boş özel terim, geçersiz maskeleme biçimi ve eksik hash tuzu `ValueError` üretir. Özel terimler sözcük sınırlarıyla, düz metin olarak eşleşir; Türkçedeki `i ↔ İ` ve `ı ↔ I` çiftleri doğru ele alınır. Kütüphane isim tahmin etmez. Yalnız kendi sözlüğünüzü taramak için `types=["CUSTOM"]` kullanın.

| Tür | Algılama ve açık doğrulayıcı |
| --- | --- |
| `TCKN` | İlk hanesi sıfır olmayan 11 ASCII rakam ve iki kontrol hanesi; bitişik veya aynı ayraçla 3-3-3-2 boşluk/nokta grupları. `validate_tckn` |
| `VKN` | 10 ASCII rakam ve konuma göre ağırlıklandırılan vergi kontrol hanesi. `validate_vkn` |
| `IBAN` | `TR` + 24 rakam, yatay boşluklar, sıfır rezerv hanesi, ülke uzunluğu ve MOD 97-10. `validate_tr_iban` |
| `PHONE` | TR cep `5xx` veya bilinen sabit hat alan kodu; `+90`, `0090`, `0`, boşluk, tire ve parantez. Öneksiz ve bitişik 10 haneli sayılarda öncesinde `telefon`, `tel`, `cep` veya `gsm` gerekir. `validate_phone` |
| `EMAIL` | Yaygın, tırnaksız ASCII e-posta biçimi ve noktalı alan adı; DNS sorgusu yoktur. `validate_email` |
| `CREDIT_CARD` | 13–19 rakam, isteğe bağlı boşluk/tire, Luhn; tek rakamın tekrarından oluşan değerler reddedilir. `validate_credit_card` |
| `PLATE` | `01`–`81` il kodu; 1 harf + 4 rakam, 2 harf + 3–4 rakam veya 3 harf + 2–3 rakam; bitişik/boşluklu. `validate_plate` |
| `IP` | `ipaddress` ile doğrulanan IPv4/IPv6; bağlam etiketi gerekmez. `validate_ip` |
| `POSTAL_CODE` | İlk iki hanesi `01`–`81` olan beş rakam; yalnız `posta kodu` veya `PK` sonrasında. `validate_postal_code` |
| `CUSTOM` | Yalnız kullanıcının verdiği terimler. `validate_custom_term(value, term)` |

Doğrulayıcılar hem `tr_pii` üzerinden hem kendi modüllerinden (`tckn`, `vkn`, `iban`, `phone`, `email`, `credit_card`, `plate`, `ip`, `postal_code`, `custom`) kullanılabilir. `bool` döndürürler; telefon/posta kodu doğrulayıcıları tek başına verilen değeri inceler, algılama bağlamını aramaz. `validate_iban`, ayrıca genel IBAN biçimini, kayıtlı ülke uzunluğunu ve kontrol hanesini denetler; TR dışındaki ulusal BBAN kurallarını denetlemez. **Metinde otomatik IBAN algılama yalnız TR içindir.** `TYPES`, `Match` ve `Style` tür takma adı dışa açıktır. Paket `py.typed` içerir.

## Sentetik test verisi

```python
from tr_pii import fake, validate_tckn, validate_vkn, validate_tr_iban, validate_credit_card

assert validate_tckn(fake.tckn(seed=1))
assert validate_vkn(fake.vkn(seed=1))
assert validate_tr_iban(fake.tr_iban(seed=1))
assert validate_credit_card(fake.credit_card(seed=1, length=19))
```

**Yalnız test için.** Üreticiler geçerli kontrol haneleri oluşturur; kayıtlı kimlik veya kullanılabilir ödeme bilgisi sağlamaz. Üretilen değerler rezerve değildir ve atanmış numaralarla tesadüfen çakışabilir. Sahte TR IBAN'larında banka alanı `00000`, kartlarda varsayılan önek `999` olur. Aynı tohum (`seed`) aynı test verisini üretir. Bu değerleri gerçek servislere göndermeyin.

## Sınırlar ve uyarılar

- Algılama %100 garanti değildir. Hassas metni paylaşmadan önce sonucu gözden geçirin. Bu kütüphane tek başına mevzuata uyum veya geri döndürülemez anonimleştirme sağlamaz.
- İsimler için kendi sözlüğünüz gerekir. Adresler, sözlük dışı isimler, OCR hataları, gizlenmiş yazımlar, yazıyla belirtilen sayılar ve Unicode rakam benzerleri kapsam dışıdır. Konumları korumak için Unicode normalleştirmesi yapılmaz.
- Kontrol hanesi, sahipliği veya atanmış olmayı doğrulamaz. Geçerli kontrol haneli bir fatura numarası, özellikle tek kontrol haneli VKN ile karışabilir. Sıkı sözcük sınırları nedeniyle ürün koduna gömülü numaralar atlanır.
- Telefon algılama, etiketsiz ve biçimlendirilmemiş öneksiz 10 haneli sayıları bilerek atlar. Mobil numara tahsisi ve hattın durumu kontrol edilmez. Coğrafi olmayan servis numaraları kapsam dışıdır.
- Plaka algılama yukarıdaki olağan 2–4 rakamlı birleşimleri kapsar. Tek harfli beş rakamlı seriler, diplomatik/özel biçimler ve il bazında harf tahsisleri kapsam dışıdır. Q/W/X ve Türkçeye özgü işaretli harfler reddedilir. Boşluklu plakalarda harfler büyük olmalıdır (küçük harf yalnız bitişik yazımda kabul edilir); böylece "42 at 100" gibi düz metin plaka sayılmaz.
- E-posta algılama tırnaklı yerel bölümleri, Unicode e-postaları ve IP biçimli alan adlarını kapsamaz. Posta kodunda PTT tahsis listesi yerine il kodu biçimi kontrol edilir. IP doğrulayıcısı yalın adres alır; algılayıcı köşeli parantez veya CIDR içinden adresi ayırabilir.
- SWIFT kayıtları hesap alanında harflere de izin verse de TR IBAN'ları bu projenin sayısal kapsamına göre denetlenir. Genel IBAN doğrulaması ulusal BBAN yapısını ve banka tahsislerini denetlemez. Ülke uzunluğu tablosunun zamanla güncellenmesi gerekebilir.
- `scan` ham değerleri döndürür. Kısmi maskeleme bazı rakamları bilerek açık bırakır; tuzlu hash, değerler arasındaki ilişkileri korur. Bu bilgi açığa çıkmamalıysa `tag` veya `stars` kullanın.
- Dosyalar bütün olarak belleğe alınır. Hedef, tipik bir geliştirme bilgisayarında 1 MB metni bir saniyenin altında işlemektir; donanım, bulgu yoğunluğu ve büyük özel sözlükler süreyi etkiler. Bu bir hedef olup gecikme garantisi değildir.

## Geliştirme ve katkı

```sh
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m mypy
python -m build
python scripts/benchmark.py
```

Geliştirme paketleri olmadan da depo içinden standart kütüphaneyle test çalıştırılabilir:

```sh
PYTHONPATH=src python -m unittest discover -v
PYTHONPATH=src python scripts/benchmark.py
```

PowerShell'de Python komutlarından önce `$env:PYTHONPATH = "src"` ayarlayın. CI, Python 3.10–3.14 üzerinde test, lint, sıkı tür denetimi ve paket derlemesi çalıştırır. Testler kontrol haneli veriyi üretir; ayrılmış e-posta/IP örnekleri kullanır. Katkı süreci için [CONTRIBUTING.md](CONTRIBUTING.md), değişiklikler için [CHANGELOG.md](CHANGELOG.md) dosyasına bakın.

## Teknik kaynaklar

- [TCMB IBAN tebliği](https://www.tcmb.gov.tr/wps/wcm/connect/EN/TCMB%2BEN/Bottom%2BMenu/IBAN/Communique): TR yapısı ve MOD 97-10.
- [SWIFT IBAN kaydı](https://www.swift.com/resource/iban-registry-pdf): ülke uzunlukları (Sürüm 103, Eylül 2026).
- [BTK ulusal numaralandırma planı](https://btk.gov.tr/ulusal-numaralandirma-plani): mobil ve coğrafi numara yapıları.
- [Resmî Gazete, plaka harf/rakam grupları, Madde 55](https://resmigazete.gov.tr/eskiler/2014/02/20140219-8.htm).

## Lisans

[MIT](LICENSE). Copyright (c) 2026 Yusuf Berat Zengin.

