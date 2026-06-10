# Desain Arsitektur: Agent as a Service (AaaS), Sistem RSI & Pembelajaran Berbasis Pengalaman (Experiential Learning)

## 1. Filosofi: Zero-Alpha & Experiential Learning
Tujuan utama arsitektur ini adalah memindahkan kebergantungan agen dari sekadar bobot pre-training LLM (Prompt Engineering) menuju **Basis Pengetahuan Berbasis Pengalaman** (Experience Engineering).

* **Latar Belakang Masalah:** Kebanyakan data pre-training LLM bersifat statis dan tidak up-to-date.
* **Paradigma Zero-Alpha:** Terinspirasi dari AlphaGo Zero, agen belajar mandiri melalui aksi langsung (learning by doing). Setiap kesuksesan dan kegagalan eksekusi tugas di-parsing secara lokal dan disimpan sebagai data pengalaman persisten (Memori). Dengan cara ini, agen lebih mengandalkan akumulasi pengalamannya dalam suatu proyek atau persona dibandingkan bias bawaan pre-training.

---

## 2. Isolasi Memori Berbasis Persona
Untuk mencegah keruntuhan konteks (*context collapse*) dan halusinasi antar domain yang berbeda, memori disegregasi secara ketat menggunakan pendekatan Multi-Agent dengan memori masing-masing.

### A. Pembagian Persona
Setiap sub-agent mewakili persona dengan spesialisasi tertentu yang memiliki memori terisolasi:
* **Copywriter**: Memiliki memori gaya bahasa, nada bicara, dan template copywriting.
* **Researcher**: Memiliki akses memori penemuan, sumber data eksternal, dan pola query.
* **QA (Quality Assurance)**: Memiliki memori kriteria kelayakan, bug umum, dan edge cases.
* **Dev (Developer)**: Memiliki memori standar coding, framework yang disetujui, dan syntax error resolution.
* **System Architect**: Memiliki memori desain pola sistem, dependensi, dan batasan infrastruktur.

### B. Hierarki Memori & Klasifikasi
Struktur memori dibagi menjadi beberapa tingkatan logis yang diadaptasi dari jenis memori kognitif:
1. **Working Memory (Memori Kerja):** Memori jangka pendek yang aktif saat merespons instruksi spesifik (dibatasi secara ketat oleh *context window* saat ini).
2. **Episodic Memory (Memori Episodik):** Riwayat percakapan lintas sesi dan preferensi spesifik yang diambil secara dinamis. Menggunakan basis data lokal (Markdown / JSON) yang di-retrieve saat diperlukan.
3. **Semantic Memory (Memori Semantik):** Pengetahuan dasar global (fakta, bahasa, konsep pemrograman) yang sudah tertanam pada LLM ditambah basis pengetahuan proyek lokal (`AGENTS.md` / `.plans/`).
4. **Batasan Global:** Konfigurasi statis dan aturan sistem global yang tidak boleh dilanggar.

* **Mekanisme:** Saat persona tertentu dipanggil, hanya memorinya masing-masing yang dimuat ke dalam *context window*, menjaga *Semantic Memory* tetap tajam, presisi, dan efisien secara token.

---

## 3. Dinamika Konteks: Agentic RAG
Untuk menjaga pengetahuan agen tetap dinamis dan selalu baru, sistem menerapkan arsitektur **Agentic RAG** (bukan sekadar RAG pasif).

* **Cara Kerja:** Berbeda dengan RAG tradisional yang hanya mengambil dokumen statis berdasarkan kemiripan vektor, Agentic RAG memanfaatkan penalaran LLM untuk memutuskan kapan harus mencari basis data internal, menggunakan search engine (web search), atau memanggil API eksternal.
* **Kelebihan:**
  * **Pencarian Dinamis (Multi-Step):** Mampu melakukan iterasi pencarian berulang dengan mereformasi kata kunci jika hasil awal kurang relevan.
  * **Self-Correction:** Agen memverifikasi kebenaran dan kesegaran (freshness) data sebelum menyajikannya.
  * **Integrasi Alat Bantu (Tool Use):** Fleksibel menggunakan API eksternal untuk melengkapi data real-time.
* **Mitigasi Risiko:**
  * **Latensi & Token Cost:** Karena proses evaluasi berulang memakan waktu dan token, Agentic RAG hanya dipicu jika data internal dinilai kedaluwarsa atau saat query membutuhkan fakta real-time.
  * **Infinite Loop Prevention:** Dibatasi oleh parameter `max_iterations` dan evaluasi heuristik untuk memutus perulangan jika tidak ada informasi baru yang didapatkan.

---

## 4. Toleransi Kesalahan Multi-Agen & Hierarki
Sistem menggunakan struktur hierarki **CEO -> Agen Divisi -> Agen Pekerja (Worker)** dengan pengamanan berlapis.

### A. Fault Tolerance & Exception Handling
* **Crash pada Tingkat Worker/Divisi:** Jika sub-agen mengalami crash, timeout, atau mengembalikan data sampah, CEO menangkap exception tersebut tanpa ikut crash.
* **Timeout karena Task Terlalu Panjang:** Jika pemanggilan sub-agent atau mekanisme fallback mengalami timeout (karena task yang terlalu besar), sistem akan melakukan pemecahan tugas (*task splitting*) menjadi sub-task yang lebih kecil secara dinamis, menyimpan *checkpoint* progres ke disk, dan melanjutkan eksekusi dari checkpoint tersebut.
* **Crash pada Tingkat CEO (Trial Case):** Jika CEO sendiri mengalami crash:
  1. Proses supervisor (eksternal CLI/Host) akan menangkap signal crash.
  2. Sistem melakukan *automatic rollback* status transaksi terakhir.
  3. Memulihkan status dari *state persistence file* terakhir yang disimpan di disk, lalu mengeskalasi kondisi ke pengguna melalui CLI untuk konfirmasi manual sebelum mencoba ulang.

### B. Sistem Umpan Balik (Feedback Loop)
* **Pencatatan Kegagalan:** Kegagalan tidak dicatat secara mentah (*raw logs*), melainkan diproses terlebih dahulu oleh agen kurator (*Curator/Advisor Agent*).
* **Format Catatan:** Disimpan dalam bentuk analisis kegagalan terstruktur: `[Kondisi Input] -> [Tindakan yang Salah] -> [Error Trace/Penyebab] -> [Rekomendasi Perbaikan (Lesson Learned)]`.
* **Metode Pelatihan:** Catatan hasil kurasi ini diinjeksikan sebagai memori episodik (*few-shot examples* dalam prompt) pada sesi berikutnya, sehingga sub-agent tidak mengulangi kesalahan yang sama.

---

## 5. Manajemen Sumber Daya Interaktif (Gaya Codex-CLI)
Kehabisan token, limit API (Rate Limits), atau error API tidak akan lagi mengakibatkan hard crash.

* **Interupsi Interaktif:** Saat limit tercapai di tengah tugas yang memakan waktu lama, perulangan (loop) akan di-pause secara aman.
* **Opsi CLI yang Ditampilkan ke Pengguna:**
  1. **Tunggu (Wait) [Tidak Direkomendasikan untuk Jangka Panjang]:** Menahan state di memori. Mengingat limit rate-limit bisa mencapai 5 jam dan berisiko laptop mati/system ter-close, opsi ini dilengkapi dengan **State Serialization** (menyimpan seluruh state ke disk secara otomatis agar proses bisa di-resume dari checkpoint saat sistem dijalankan kembali).
  2. **Ganti Model (Switch Model):** Mengganti provider/model secara langsung (*hot-swap*) berdasarkan model yang terdeteksi aktif dan tersedia di API endpoint.
  3. **Batal/Reset [Tidak Direkomendasikan]:** Membuang konteks saat ini dan memulai dari awal. Hanya digunakan jika tidak ada alternatif checkpoint yang valid.

---

## 6. Efisiensi Sumber Daya (RAM & Caching)
Dioptimalkan untuk lingkungan Linux dengan RAM 4GB dan integrasi API proxy/endpoint gratis.

* **Resource Management (9router):** Mendukung hot-swapping antar endpoint/API yang terdeteksi di 9router, termasuk: *oauth ag, gemini-cli, api gemini, api openrouter, opencode free, groq free, nvidia free, ollama free,* dan *kiro free*.
* **Memory Leak & Invisible Loop Prevention:**
  * Selain pemanggilan `gc.collect()` setelah tugas selesai untuk RAM tanpa referensi, sistem menerapkan monitoring proses secara aktif.
  * Setiap sub-task berjalan di bawah pengawasan worker thread/process dengan timeout absolut level OS (SIGKILL untuk zombie process) guna mencegah *invisible infinite loops* memakan memori.
* **Caching Universal:**
  * Dukungan untuk **Anthropic Cache-Control** (`{"cache_control": {"type": "ephemeral"}}`).
  * Dukungan untuk **OpenAI Prefix Caching**: Inti *System Prompt* dibekukan (statis), sedangkan variabel dinamis diletakkan di akhir prompt untuk memaksimalkan *cache hit* lintas proxy.
* **Smart Compression:** Mengompres konteks menggunakan tag `<memory-context>` tanpa membuang informasi penting, mencegah pembengkakan memori.
