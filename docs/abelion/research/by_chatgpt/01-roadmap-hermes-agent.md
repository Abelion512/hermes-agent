# Perencanaan Masa Depan Hermes Agent

## Gambaran Umum Hermes Agent

Hermes Agent adalah kerangka kerja agen AI open‑source dari Nous Research yang dirilis pada Februari 2026. Platform ini bukan sekadar chatbot; ia menjalankan proses belajar mandiri. Saat menjalankan tugas yang kompleks, Hermes menulis *skill document* yang dapat digunakan kembali untuk memori jangka panjang dan mengingat konteks antar sesi. Agen ini memiliki antarmuka terminal penuh, kemampuan persistent memory, pembuatan skill otomatis, integrasi multi‑platform (Telegram, Discord, Slack, WhatsApp, Signal, CLI), scheduler untuk tugas berkala, sub‑agen paralel, dan integrasi browser untuk pencarian web serta kontrol penuh halaman【379018934104739†L533-L569】. Situs resmi menjelaskan bahwa Hermes mendukung banyak penyedia LLM, mulai dari Nous Portal, OpenRouter, OpenAI hingga penyedia lain seperti Kimi, NovitaAI, NIM/NVIDIA, dan layanan self‑host seperti vLLM【379018934104739†L541-L547】. Dokumentasi juga menyoroti beberapa fitur kunci:

- **Memori Persisten dan Skill Otomatis:** Hermes mengingat preferensi, proyek, dan lingkungan di seluruh sesi. Saat agent menyelesaikan sebuah masalah, ia menulis skill baru sehingga tidak lupa bagaimana menyelesaikannya【340288179040835†L40-L49】.
- **Gateway Multi‑Platform:** Agent dapat terkoneksi ke Telegram, Discord, Slack, WhatsApp, Signal, dan CLI melalui gateway tunggal, memungkinkan percakapan dilanjutkan pada platform berbeda【340288179040835†L52-L55】.
- **Scheduling Otomatis:** Hermes memiliki scheduler bawaan untuk menghasilkan laporan, backup, dan audit dalam bahasa alami yang berjalan tanpa pengawasan【340288179040835†L58-L61】.
- **Delegasi dan Sub‑agen:** Agent dapat memunculkan sub‑agen yang terisolasi untuk menjalankan alur kerja paralel dan mengeksekusi skrip Python melalui RPC, mengurangi overhead konteks【340288179040835†L62-L65】.
- **Browser Automation dan Vision Tools:** Mendukung web search, navigasi, klik, form filling, screenshot, analisis gambar, text‑to‑speech, dan reasoning multi‑model【340288179040835†L68-L72】.
- **Keamanan dan Privasi:** Hermes bersifat self‑hosted, semua memori disimpan di `~/.hermes/` pada mesin pengguna, tanpa telemetri dan dengan hardening container【340288179040835†L156-L167】.

## Tantangan dan Tren

1. **Kebutuhan Model Lebih Baik:** Hermes bersifat model‑agnostik; pengguna bebas memilih LLM melalui Nous Portal atau API lain【379018934104739†L541-L547】. Namun, kualitas agent bergantung pada kemampuan model—terutama kemampuan memanggil tools. Tren terbaru menunjukkan bahwa model generasi baru seperti Qwen 3.5 27B, Kimi 3.6, atau GPT‑5.5 memberikan peningkatan signifikan dalam reasoning dan tool‑calling【667953570341297†L81-L90】. Ke depan, Hermes perlu mengoptimalkan pipeline pembuatan skill dan memori agar dapat memanfaatkan model super‑besar tanpa membebani resource.

2. **Skalabilitas dan Penyimpanan Memori:** Semakin banyak tugas dan sesi, semakin besar memori yang dibutuhkan. Hermes sudah menawarkan kompresi trajectory untuk fine‑tuning dan ekspor【340288179040835†L200-L213】, tetapi penyimpanan jangka panjang yang efisien akan menjadi fokus penting. Integrasi database atau store eksternal (contoh: vector store) dapat memungkinkan pencarian memori yang lebih cepat dan hemat sumber daya.

3. **Orkestrasi Multi‑Agen:** Walaupun Hermes mendukung sub‑agen, ekosistem AI bergerak ke arah orkestrasi multi‑agen yang kompleks. Framework seperti CrewAI menekankan kolaborasi antara beberapa agen dengan peran berbeda【357636931925459†L117-L133】. Hermes dapat mengadopsi modul orkestrasi yang memungkinkan agen spesialis (coder, researcher, planner) bekerja bersama secara terkoordinasi.

4. **Integrasi Browser Lebih Human‑Like:** Studi penelitian menunjukkan bahwa AI browsing agent mudah dibedakan dari manusia berdasarkan fingerprint perilaku seperti kecepatan mengetik, pola scroll, dan gerakan mouse【877770038592623†L74-L94】. Dokumen Browser Run dari Cloudflare memperkenalkan fitur *human‑in‑the‑loop*, live view, dan kemampuan CDP langsung untuk kontrol browser yang lebih halus【273621410785770†L70-L97】. Hermes dapat mengintegrasikan teknologi seperti Browser Run atau Browser Use untuk memberikan pengalaman browsing yang realistis sekaligus aman.

5. **Privasi dan Keamanan:** Dengan meningkatnya penggunaan agen, masalah privasi (perizinan data, akses API, dan keamanan cookie) menjadi krusial. Hermes harus memastikan pemisahan konteks sesi dan menggunakan enkripsi untuk menyimpan state login【372162304856941†L135-L173】. Selain itu, modul untuk mematuhi Terms of Service situs target perlu disediakan untuk menghindari pelanggaran.

## Rencana dan Tujuan Hermes Agent

1. **Optimalisasi Pemilihan Model dan Routing:**
   - Mengembangkan *model router* adaptif yang memilih model terbaik berdasarkan tugas (contoh: model besar untuk reasoning, model kecil untuk respon cepat). Integrasi dengan penyedia seperti Nous Portal, Groq, OpenRouter, dan Google AI Studio harus memungkinkan rotasi otomatis sesuai ketersediaan free tier【667953570341297†L41-L50】.
   - Memanfaatkan vLLM atau Ollama lokal untuk tugas internal sensitif, dengan fallback ke cloud ketika resource lokal terbatas.

2. **Framework Multi‑Agen dan Kolaborasi:**
   - Menambahkan modul orkestrasi agar Hermes dapat bekerja bersama agen lain seperti CrewAI untuk proyek kolaboratif. Sub‑agen dapat didelegasikan ke spesialis (penulis, penerjemah, analis data), sedangkan agen utama bertindak sebagai koordinator.
   - Mendukung antarmuka *webMCP* dan *MCP Client* sebagaimana diperkenalkan Cloudflare untuk memfasilitasi interaksi agen–agen dan situs web【273621410785770†L94-L101】.

3. **Peningkatan Browser Automation:**
   - Implementasi modul *human‑like browsing* menggunakan library seperti `browser-use` atau `camofox` yang memiliki fingerprint acak, CAPTCHA solving, dan interaksi mouse/keyboard yang menyerupai manusia【865977386280222†L61-L91】. Integrasi dengan Browser Run Cloudflare untuk sesi dengan pengawasan (live view) dapat meningkatkan keandalan.
   - Mendukung penggunaan profil Chrome pengguna melalui `--profile` atau persistent session sehingga agen dapat memanfaatkan akun nyata tanpa memulai sesi bersih setiap saat【372162304856941†L85-L122】.

4. **Memori dan Skill Management:**
   - Menyediakan tools untuk menganalisis dan merangkum memori jangka panjang agar tidak terjadi bloat. Implementasi vector store opsional untuk pencarian semantik.
   - Meningkatkan format `SKILL.md` menjadi modul versioned, sehingga pembaruan skill terarsip dan reversible. Komunitas dapat berbagi skill melalui repositori seperti agentskills.io【340288179040835†L146-L154】.

5. **Lokalisasi dan Aksesibilitas:**
   - Menambahkan antarmuka multi‑bahasa (contoh: bahasa Indonesia, Cina, Sundanese) untuk melayani pengguna global. Hermes sudah menyediakan dokumentasi multibahasa, namun antarmuka CLI dan pesan agen dapat disesuaikan otomatis.
   - Menyediakan integrasi dengan platform lokal (Telegram, WeChat, Feishu, Enterprise WeChat) seperti yang dideskripsikan dalam panduan Tencent Cloud【448071785777366†L80-L82】.

6. **Model Fine‑Tuning dan MLOps:**
   - Menawarkan pipeline RLHF atau DPO internal menggunakan data interaksi pengguna (trajectory export) agar agen semakin disesuaikan dengan preferensi pengguna【340288179040835†L200-L213】.
   - Mengadopsi format ShareGPT untuk menyimpan interaksi dan melatih model baru; menyediakan skrip untuk fine‑tuning via vLLM atau Hugging Face.

7. **Ecosystem dan Komunitas:**
   - Mendorong kontribusi open‑source melalui issue, PR, dan modul skill. Menyusun pedoman kontribusi yang jelas untuk mempermudah pengembang baru.
   - Menyediakan *marketplace* skill atau modul plug‑and‑play yang diverifikasi (mirip VS Code extension) agar pengguna dapat menambah kemampuan agen dengan aman.

### Kesimpulan

Hermes Agent sudah memposisikan dirinya sebagai platform agen AI yang self‑hosted dengan memori persisten dan kemampuan belajar. Perencanaan ke depan perlu fokus pada optimalisasi pemilihan model, peningkatan orkestrasi multi‑agen, browser automation yang lebih human‑like, serta manajemen memori dan skill. Dengan roadmap ini, Hermes dapat berkembang menjadi ekosistem agen AI yang fleksibel, aman, dan siap untuk beradaptasi dengan tantangan baru di era agen AI.