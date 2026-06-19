# Teknologi Agen Human‑Like dan Deteksi Anti‑Bot

Artificial Intelligence (AI) browsing agents semakin populer, tetapi interaksinya dengan web memicu masalah etika dan keamanan. Bot detection seperti Cloudflare WAF, Akamai, DataDome, dan lainnya melindungi situs dari scraping berlebihan, penipuan, dan serangan. Laporan ini membahas keberadaan teknologi agen human‑like untuk browser, kemampuan deteksi seperti Cloudflare, dan langkah‑langkah konseptual untuk membangun agen yang mematuhi aturan.

## Keberadaan Teknologi Human‑Like

Beberapa penyedia mengklaim memiliki browser “stealth” yang tak terdeteksi. Artikel dari Browser Use menjelaskan bahwa mereka membuat fork Chromium dengan modifikasi di level C++ untuk menghilangkan indikator otomatisasi. Browser tersebut memastikan `navigator.webdriver` bernilai `false` bukan dengan memodifikasi JavaScript, tetapi dengan mengubah implementasi internal sehingga tidak ada perbedaan struktur prototipe【979384809166776†L70-L83】. Selain itu, Browser Use memasang infrastruktur proxy dengan IP residensial, injeksi zona waktu dan locale, dan lapisan perilaku (mouse/scroll/typing patterns) agar fingerprint yang dihasilkan konsisten dengan pengguna nyata【979384809166776†L89-L114】. Mereka juga membangun solver CAPTCHA internal untuk jenis tertentu【979384809166776†L168-L173】. 

Hermes sendiri tidak membangun browser; ia menyediakan integrasi ke beberapa provider seperti Browserbase (anti‑bot), Browser Use, Firecrawl, dan Camofox【865977386280222†L61-L91】. Browserbase menawarkan cloud browser dengan fingerprint acak, solver CAPTCHA, dan proxy residensial, sedangkan Camofox adalah server self‑hosted untuk Firefox dengan fingerprint spoofing【865977386280222†L61-L91】. Cloudflare memperkenalkan **Browser Run**, sebuah layanan yang menjalankan browser di jaringan globalnya untuk agen AI dengan fitur **Live View**, **Human in the Loop**, dan endpoint Chrome DevTools Protocol (CDP)【273621410785770†L70-L97】. Fitur *Human in the Loop* memungkinkan agen menyerahkan kendali ke manusia ketika menemukan hambatan (misal login atau CAPTCHA)【273621410785770†L85-L90】.

Penelitian terbaru di arXiv (FP‑Agent) menunjukkan bahwa meskipun banyak AI browsing agents menggunakan browser asli, pola perilaku mereka masih dapat dibedakan dari manusia. Dalam eksperimen, peneliti membandingkan tujuh agen dengan pengguna manusia dan menemukan bahwa fingerprint perilaku seperti kecepatan mengetik, scroll, dan gerakan mouse menjadi faktor pemisah utama; browser fingerprint (nilai header, navigator, canvas) kurang efektif ketika agen menggunakan browser modifikasi【877770038592623†L74-L94】. Mereka juga menunjukkan bahwa Cloudflare mendeteksi hanya satu dari tujuh agen, sedangkan classifier mereka (FP‑Agent) mendeteksi semuanya【877770038592623†L87-L94】. Hal ini menandakan bahwa deteksi anti‑bot semakin mengandalkan analisis perilaku, bukan hanya fingerprint statis.

## Etika dan Legalitas

Sebelum merancang agen yang meniru manusia, penting untuk mempertimbangkan aspek etika dan kepatuhan. Cloudflare menekankan bahwa yang penting bukan apakah klien adalah manusia atau bot, tetapi intent dan perilaku: apakah mereka melakukan serangan, scraping berlebihan, atau melanggar kebijakan【314781206605330†L70-L96】. Upaya untuk menyembunyikan identitas otomatisasi dapat melanggar Terms of Service situs dan peraturan perlindungan data. Penggunaan stealth browser sebaiknya difokuskan pada automatisasi yang sah—misalnya, memfasilitasi aksesibilitas bagi penyandang disabilitas—dengan mematuhi ketentuan situs.

## Konsep Membangun Agen Human‑Like yang Etis

Jika teknologi off‑the‑shelf tidak memenuhi kebutuhan Anda atau belum tersedia, berikut konsep untuk mengembangkan agen yang lebih mirip manusia dengan tetap mematuhi hukum:

1. **Tujuan yang Legitimate:** Definisikan secara jelas tujuan agen (misal membantu pengguna melakukan tugas pribadi di situs yang mereka miliki akses). Jangan gunakan untuk scraping massal atau pelanggaran hak cipta.

2. **Pemanfaatan Browser Autentik:** Gunakan browser nyata melalui Chrome DevTools Protocol (CDP) atau integrasi `agent-browser` sehingga agen berjalan seperti pengguna normal, bukan headless. Menghubungkan Hermes ke browser lokal via CDP membuat agen mengikuti rendering normal dan menampilkan UI【273621410785770†L130-L169】.

3. **Profil dan Fingerprint Konsisten:** Jika membutuhkan penyamaran, gunakan library seperti Camofox atau Browser Use yang menyediakan fingerprint acak dan proxy residensial【865977386280222†L61-L91】. Namun, pastikan IP, timezone, locale, GPU, dan API availability konsisten agar tidak mencurigakan【979384809166776†L94-L114】.

4. **Simulasi Perilaku Manusia:**
   - Tambahkan jitter pada gerakan mouse, waktu delay antar klik, dan variasi kecepatan mengetik.
   - Gunakan script untuk scroll secara bertahap dan acak layaknya orang membaca.
   - Pastikan interaksi UI seperti klik tombol “Login” atau “Next” mengikuti pola wajar, bukan eksekusi instan.
   Penyesuaian ini dapat dibuat dalam kode agen (misal memodifikasi `agent-browser` atau `browser-use` untuk memasukkan random delay). Jangan lupa bahwa deteksi berbasis AI (seperti FP‑Agent) memanfaatkan distribusi statistik; variasi natural membantu tetapi tidak menjamin anonim.

5. **Human‑in‑the‑Loop:** Terima bahwa tidak semua tahap dapat diotomatisasi. Cloudflare mendorong *human‑in‑the‑loop* di Browser Run: agen dapat menyerahkan kontrol kepada manusia untuk menyelesaikan captcha atau login【273621410785770†L85-L90】. Pendekatan ini bukan hanya etis tetapi juga cenderung diterima oleh platform.

6. **Kepatuhan terhadap Kebijakan Situs:** Pastikan agen membaca `robots.txt` dan Terms of Service. Hindari scraping konten yang dilarang, dan gunakan API resmi saat tersedia.

## Eksekusi Teknis (Garis Besar)

1. **Riset Fingerprint:** Kumpulkan dataset interaksi pengguna manusia (gerakan mouse, kecepatan mengetik) pada berbagai perangkat. Gunakan dataset ini untuk melatih model generatif atau heuristik yang menghasilkan pola interaksi.
2. **Integrasi ke Browser Automation:** Perluas library browser (Playwright, Puppeteer, agent-browser) agar menjalankan pola interaksi yang dihasilkan. Pastikan modul ini tetap kompatibel dengan Hermes (via Tool Gateway).
3. **Pengelolaan Identitas Jaringan:** Integrasikan proxy residensial untuk IP yang konsisten; injeksikan timezone/locale; dan jalankan di environment yang sesuai (Windows, macOS, Linux) agar fingerprint hardware masuk akal【979384809166776†L94-L114】.
4. **Monitoring dan Audit:** Implementasikan logging untuk mengetahui kapan agen diblokir atau menampilkan tantangan (CAPTCHA). Gunakan perekaman sesi (seperti fitur *Session Recordings* di Browser Run) untuk menganalisis kegagalan【273621410785770†L103-L106】.
5. **Evaluasi Terhadap Detektor:** Uji agen terhadap layanan deteksi populer (Cloudflare, DataDome) dengan izin. Perbandingkan false positive/false negative dan iterasi pola interaksi untuk mengurangi deteksi tanpa melanggar kebijakan.

## Kesimpulan

Teknologi agen human‑like sedang berkembang pesat. Browser Use, Browserbase, Camofox, dan layanan Browser Run menawarkan fingerprint acak, solver CAPTCHA, dan human‑in‑the‑loop untuk membantu agen mengakses situs web【865977386280222†L61-L91】【273621410785770†L70-L97】. Penelitian FP‑Agent menunjukkan bahwa perilaku (scroll, klik, ketik) merupakan indikator utama untuk membedakan agen AI dari manusia【877770038592623†L74-L94】. Membangun agen yang benar‑benar tidak terdeteksi membutuhkan pendekatan multi‑lapis—pengelolaan IP, konsistensi fingerprint, simulasi perilaku, dan human‑in‑the‑loop—serta kepatuhan terhadap etika dan Terms of Service. Alih‑alih fokus pada bypass, pengguna harus memanfaatkan teknologi ini untuk automatisasi yang sah dan berkelanjutan.