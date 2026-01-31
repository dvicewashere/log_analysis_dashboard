# Altay - Log Analiz


SOC projesi. Log dosyalarını okuyup analiz eder, kurallara göre uyarı üretir

Projenin web tabanlı olma sebebi herkes için daha anlaşılır olması istenildiğinden yapılmıştır.

## Özellikler

- **Özet:** Log dosyalarının içeriği okunur, gereksiz ifadeler parse edilir ve kurallara göre anlamlı uyarılar üretilir (dosya bazlı analiz).
- auth.log, syslog, nginx access.log, ufw.log dosyalarını okuyup bu özeti çıkartır.
- Gerçek zamanlı tail modu - yeni satırlar gelince kurallardan geçirilip anlamlı uyarı üretir.
- CSV olarak dışa aktarır

## Çalıştırma

Docker ile çalışır:

```
docker-compose up -d --build
```

Tarayıcıdan **http://localhost:5000** a gidilerek proje çalıştırılır.

## Dashboard

- Özet: log kaynakları listesi; özet = log içeriği parse edilip anlamlı uyarıya dönüştürülür.
- Analiz: kaynak seç, analiz et - okunan satırlar parse edilir, kurallarla eşleşenler anlamlı uyarı olarak gösterilir
- Uyarılar: anlık uyarılar (tail modu)
- Kurallar
- CSV indir: kaynak seçip csv indirir, son raporlar listesi görüntülenir.

## Kurallar

config/rules.yaml veya rules.json da:
- id, name, description
- enabled: true/false
- severity: low, medium, high, critical
- sources: auth, syslog, nginx_access, ufw (boş = hepsi)
- patterns: aranacak kelimeler veya regex
- pattern_type: substring veya regex

şeklinde yapılandırılmıştır.

## Proje yapısı

- **Dockerfile**, **docker-compose.yml** – container tanımı ve çalıştırma
- **requirements.txt** – Python bağımlılıkları, gerekli kütüphaneler
- **app/** – Python kodu (main.py, config, parsers, rules, tailer, reports)
- **config/** – rules.yaml, rules.json (kural tanımları)
- **static/**, **templates/** – web arayüzü (CSS, JS, HTML)
- **logs/** – örnek loglar (docker-compose ile ./logs → /var/log mount)
- **reports/** – CSV rapor çıktıları

