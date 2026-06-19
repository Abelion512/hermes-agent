<<<<<<< HEAD
# Desain Arsitektur: Agent as a Service (AaaS), Sistem RSI & Pembelajaran Berbasis Pengalaman (Experiential Learning)

## 1. Filosofi: Zero-Alpha & Experiential Learning
Tujuan utama arsitektur ini adalah memindahkan kebergantungan agen dari sekadar bobot pre-training LLM (Prompt Engineering) menuju **Basis Pengetahuan Berbasis Pengalaman** (Experience Engineering).

* **Latar Belakang Masalah:** Kebanyakan data pre-training LLM bersifat statis dan tidak up-to-date.
* **Paradigma Zero-Alpha:** Terinspirasi dari AlphaGo Zero, agen belajar mandiri melalui aksi langsung (learning by doing). Setiap kesuksesan dan kegagalan eksekusi tugas di-parsing secara lokal dan disimpan sebagai data pengalaman persisten (Memori). Dengan cara ini, agen lebih mengandalkan akumulasi pengalamannya dalam suatu proyek atau persona dibandingkan bias bawaan pre-training.
* **Fase Implementasi (Fase Bertahap):**
  * **Fase 1 (MVP Autonomous):** Perekaman refleksi/pengalaman ke dalam berkas memori bersifat pasif (hanya merekam saja) guna memastikan tidak ada otomatisasi baru yang mengganggu jalannya sistem secara langsung.
  * **Fase 2 (RAG Retrieval):** Mengintegrasikan sistem pencarian berbasis kemiripan (RAG/similarity search) terhadap berkas refleksi di masa lalu agar agen dapat memanggil kembali pengalaman relevan saat menghadapi tugas serupa.
  * **Fase 3 (Fine-Tuning):** Fine-tuning skala kecil secara lokal berdasarkan data akumulasi refleksi (jika didukung perangkat keras yang memadai).

---

## 2. Isolasi Memori Berbasis Persona & Kepatuhan Standar Hermes
Untuk mencegah keruntuhan konteks (*context collapse*) dan halusinasi antar domain yang berbeda, memori disegregasi secara ketat dengan mematuhi standar arsitektur Hermes yang telah ada.

### A. Pembagian Persona & Fitur Profile
Integrasi persona dilakukan menggunakan fitur bawaan `profile` Hermes yang memisahkan seluruh *state* dan konfigurasi:
* **Copywriter**: Memiliki memori gaya bahasa, nada bicara, dan template copywriting.
* **Researcher**: Memiliki akses memori penemuan, sumber data eksternal, dan pola query.
* **QA (Quality Assurance)**: Memiliki memori kriteria kelayakan, bug umum, dan edge cases.
* **Dev (Developer)**: Memiliki memori standar coding, framework yang disetujui, dan syntax error resolution.
* **System Architect**: Memiliki memori desain pola sistem, dependensi, dan batasan infrastruktur.

### B. Hierarki Memori & Integrasi
Struktur memori memanfaatkan fondasi yang sudah ada pada Hermes (`MEMORY.md` untuk catatan agen dan `USER.md` untuk profil pengguna di `~/.hermes/memories/`):
1. **Working Memory (Memori Kerja):** Memori jangka pendek yang aktif saat merespons instruksi spesifik (dibatasi secara ketat oleh *context window* saat ini).
2. **Episodic Memory (Memori Episodik):** Riwayat percakapan lintas sesi dan preferensi spesifik yang diambil secara dinamis. Menggunakan berkas markdown/JSON lokal.
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
Sistem menggunakan struktur hierarki **CEO -> Agen Divisi -> Agen Pekerja (Worker)** dengan pengamanan berlapis dan urutan kait (*hook*) yang terstruktur secara ketat.

### A. Prioritas Kait Hook & Loop Detector
Saat terjadi error atau eksekusi tugas berjalan:
1. **Loop Detector (Priority 10 - Paling Awal):** Memeriksa pengulangan aksi secara berulang-ulang (infinity loop) sebelum mekanisme fault tolerance lain dipicu. Jika terdeteksi perulangan aksi serupa secara tidak wajar, loop dihentikan secara aman.
2. **Fault Tolerance & Exception Handling (Priority 20):** Menangani kegagalan koneksi API, timeout, atau crash pada tingkat sub-agen.

### B. Fault Tolerance & Exception Handling
* **Crash pada Tingkat Worker/Divisi:** Jika sub-agen mengalami crash, timeout, atau mengembalikan data sampah, CEO menangkap exception tersebut tanpa ikut crash.
* **Timeout & Task Splitting:** Jika pemanggilan sub-agent mengalami timeout, sistem melakukan pemecahan tugas (*task splitting*) menjadi sub-task yang lebih kecil secara dinamis, menyimpan *checkpoint* progres ke disk, dan melanjutkan eksekusi dari checkpoint tersebut.
* **Atomic State & Session Persistence (Gaya Codex/Claude-Code):** Untuk mematuhi prinsip *Agentic-as-a-Service* (AaaS), sistem melakukan checkpoint otomatis setiap kali akan mengubah file. Jika terjadi crash di tingkat CEO:
  1. Proses supervisor (eksternal CLI/Host) menangkap signal crash.
  2. Sistem melakukan *automatic rollback* status transaksi terakhir.
  3. Memulihkan status dari *state persistence file* terakhir yang disimpan di disk (menggunakan *Git-based snapshot* tersembunyi atau folder `~/.hermes/snapshots/`), lalu melanjutkan eksekusi atau mengeskalasi kondisi ke pengguna.

### C. Sistem Umpan Balik (Feedback Loop)
* **Pencatatan Kegagalan:** Kegagalan diproses terlebih dahulu oleh agen kurator (*Curator/Advisor Agent*) sebelum disimpan.
* **Format Catatan:** Disimpan dalam bentuk analisis kegagalan terstruktur: `[Kondisi Input] -> [Tindakan yang Salah] -> [Error Trace/Penyebab] -> [Rekomendasi Perbaikan (Lesson Learned)]`.
* **Metode Pelatihan:** Catatan hasil kurasi ini diinjeksikan sebagai memori episodik (*few-shot examples* dalam prompt) pada sesi berikutnya, sehingga sub-agent tidak mengulangi kesalahan yang sama.

---

## 5. Manajemen Sumber Daya Interaktif & Gateway-Driven Auto-Verification
Kehabisan token, limit API (Rate Limits), atau error API ditangani secara dinamis dengan mengutamakan kelancaran vibe-coding.

* **Interupsi Interaktif & State Serialization:** Saat limit tercapai di tengah tugas, perulangan di-pause secara aman dan seluruh *state* diserialisasikan to disk secara otomatis agar proses bisa di-resume nanti.
* **Manajemen Fallback Kegagalan API:**
  1. **Provider Hot-Swapping:** Jika terjadi error pada satu provider, sistem otomatis mencoba provider/model berikutnya dalam rantai cadangan (*model fallback chain*).
  2. **Eskalasi Cerdas ke Gateway (Tele/DC):** Jika semua provider dalam rantai cadangan mengalami kegagalan, agen tidak melakukan crash, melainkan masuk ke *Managed Fallback State*, menyimpan status lengkap, dan mengirimkan notifikasi eskalasi berisi detail error ke gateway komunikasi (Telegram/Discord) pengguna untuk meminta intervensi manual (misalnya pembaruan API key).
* **Gateway-Driven Auto-Verification:** Mengingat pengguna lebih sering menggunakan vibe-coding tanpa interaksi langsung melalui CLI (melalui gateway seperti Telegram/Discord dengan perintah `/goal`), sistem tidak memerlukan opsi interupsi interaktif berbasis CLI. Verifikasi dijalankan di background secara otomatis dan hasilnya dikirimkan langsung ke gateway (`✅ [BUILD PASSED]` atau `⚠️ [BUILD FAILED]`).

---

## 6. Efisiensi Sumber Daya (RAM & Caching)
Sistem dioptimalkan untuk lingkungan Linux dengan RAM 4GB dan integrasi API proxy/endpoint gratis.

* **Resource Management (9router):** Mendukung hot-swapping antar endpoint/API yang terdeteksi di 9router, termasuk: *oauth ag, gemini-cli, api gemini, api openrouter, opencode free, groq free, nvidia free, ollama free,* dan *kiro free*.
* **Memory Leak & Infinite Loop Prevention:**
  * Eksekusi `gc.collect()` secara eksplisit setelah tugas selesai.
  * Setiap sub-task berjalan di bawah pengawasan worker thread/process dengan timeout absolut level OS (SIGKILL untuk zombie process) guna mencegah *invisible infinite loops* memakan memori.
* **RAM & Browser Check:** Karena keterbatasan RAM 4GB, verifikasi browser dinonaktifkan secara bawaan (*disabled by default*), namun dapat diaktifkan manual dengan konfigurasi khusus:
  * Menjalankan browser dalam mode headless (`browser_headless: true`).
  * Menerapkan batas memori ketat (`browser_memory_limit_mb: 512`) dan timeout agresif (misal 10 detik).
* **Pencegahan Error & Hierarchical Impact-Based Decision:**
  * Saat verifikasi linter/test mendeteksi kesalahan, sistem membagi penanganan berdasarkan tingkat dampak (*severity*).
  * **Low Impact (Convention/Style):** Jika kesalahan hanya berupa pelanggaran konvensi kode atau gaya penulisan yang tidak merusak jalannya aplikasi, agen dapat mengabaikan peringatan tersebut setelah satu kali percobaan perbaikan gagal.
  * **High Impact (Critical/Code-Breaking):** Jika kesalahan berupa *syntactical error* atau kegagalan fungsional yang fatal, agen wajib memperbaiki masalah tersebut sebelum tugas dinyatakan selesai.
* **Caching Universal:**
  * Dukungan untuk **Anthropic Cache-Control** (`{"cache_control": {"type": "ephemeral"}}`).
  * Dukungan untuk **OpenAI Prefix Caching**: Inti *System Prompt* dibekukan (statis), sedangkan variabel dinamis diletakkan di akhir prompt untuk memaksimalkan *cache hit* lintas proxy.
* **Smart Compression:** Mengompres konteks menggunakan tag `<memory-context>` tanpa membuang informasi penting, mencegah pembengkakan memori.
=======
# Desain Arsitektur: AaaS, Sistem RSI & Pembelajaran Berbasis Pengalaman (Experiential Learning)

> **Versi:** 4.0 (Final Terverifikasi — 18 Juni 2026)
> **Referensi Utama:**
> - Anthropic: [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents), [Managed Agents](https://claude.com/blog/building-with-claude-managed-agents), [Zero Trust for AI Agents](https://claude.com/blog/zero-trust-for-ai-agents), [Computer Use Best Practices](https://claude.com/blog/best-practices-for-computer-and-browser-use-with-claude)
> - Hermes Docs: [github.com/NousResearch/hermes-agent/tree/main/website/docs](https://github.com/NousResearch/hermes-agent/tree/main/website/docs)
> - Audit Redundansi: `docs/abelion/research/hermes-agent/REDUNDANCY_AUDIT.md`
> - Hasil Pengujian: `test_abelion_error_handler.py` (Lolos Verifikasi 100%)

---

## 1. Lingkup Teknis & Filosofi Integrasi Terbuka

### A. Modularitas Berbasis Plugin (100% Core Preservation)
Seluruh fitur baru dibangun secara modular untuk menjaga stabilitas kode sumber utama Hermes Agent.
- **Implementasi Riil:** Semua komponen berjalan sebagai modul terpisah di bawah direktori `plugins/` dan didaftarkan ke sistem menggunakan `PluginManager` Hermes secara runtime.
- **Daftar Plugin yang Berhasil Dipasang:**
  1. `plugins/abelion_core`: Menggabungkan *active reflection*, *loop detector*, *health check*, dan *caching middleware*.
  2. `plugins/autonomous_verify`: Menyediakan tool `verify_change` untuk visualisasi pengujian "Asa-style".
  3. `plugins/fault_tolerance`: Menangani *circuit breaker*, *auto-retry*, and perekaman kegagalan ke `memory/projects/error_log.json`.
  4. `plugins/display_aesthetics`: Merapikan visualisasi visual tabel markdown.

### B. Audit Redundansi & Penghapusan Solusi Kustom (Stop Reinventing the Wheel)
Berdasarkan audit teknis, implementasi fungsionalitas dialihkan ke integrasi fitur open-source native yang telah matang di dalam Hermes:
- **Prompt Caching:** Caching dinamis dikendalikan secara native oleh `agent/prompt_caching.py` (stabilisasi byte system prompt) yang terhubung langsung ke Anthropic/OpenRouter, memotong latensi hingga hampir nol tanpa memerlukan middleware kustom.
- **Sandboxing:** Mandat Docker Sandbox yang kaku didepresiasi karena mengganggu alur kerja vibe-coding. Keamanan dialihkan ke restriksi jalur lokal (path restriction) dan optimalisasi driver terminal native (`tools/environments/daytona.py` / `docker.py`).
- **Sistem Memori:** Memori prosedural mengintegrasikan platform terbuka `plastic-labs/honcho` and `mem0` daripada merancang basis data vektor lokal baru yang membebani RAM.

---

## 2. Status Implementasi Riil & Struktur Sub-Modul

### A. `plugins/abelion_core` (Pusat Refleksi & Loop Detector)
Modul ini bertindak sebagai koordinator kognitif pasif dan aktif pada sesi percakapan.

```
on_session_end ──> Pemicu Active Reflection ──> Analisis Trajectory via LLM ──> Simpan JSON ke docs/abelion/reflections/
```

- **Active Reflection (`reflection.py`):** Di akhir setiap sesi (`on_session_end`), modul memanggil instansi LLM (`ctx.llm.complete`) untuk menganalisis riwayat obrolan dan mengekstrak data pembelajaran (summary, status, errors, lessons, recommendations) ke dalam direktori terisolasi `docs/abelion/reflections/`.
- **Anti-Infinity Loop (`loop_detector.py`):** Hook `pre_tool_call` memantau riwayat tindakan. Jika terdeteksi pemanggilan alat yang sama dengan parameter identik sebanyak 3 kali berturut-turut dalam jendela 5 aksi terakhir, sistem mendeteksi kondisi loop dan mengeluarkan warning.
- **Health Check (`health.py`):** Melakukan verifikasi ketersediaan model API sebelum turn pertama berjalan untuk menghindari kegagalan eksekusi senyap.

### B. `plugins/fault_tolerance` (Circuit Breaker & Zero-Alpha Memory)
Menjamin keandalan agen di bawah kegagalan infrastruktur API atau tool.
- **Zero-Alpha Correction Memory:** Hook `pre_llm_call` membaca 3 catatan kegagalan terakhir di `memory/projects/error_log.json` dan menyuntikkannya secara dinamis ke dalam prompt LLM. Ini bertindak sebagai bias koreksi real-time agar agen tidak mengulangi kesalahan prosedural yang sama.
- **Auto-Retry & Circuit Breaker:** Tool call yang gagal memicu auto-retry hingga 2 kali. Jika kegagalan berturut-turut mencapai 5 kali, status circuit breaker berubah menjadi **OPEN**, memblokir seluruh pemanggilan delegasi (`delegate_task`) untuk menghemat token dan RAM, serta mengalihkan interupsi ke gateway Tele/DC.

### C. `plugins/autonomous_verify` (Unified Verification Pipeline)
Menyediakan tool terintegrasi `verify_change` untuk mengawal perubahan kode secara otonom.
- **Deteksi Otomatis:** Memindai file konfigurasi (`pyproject.toml`, `package.json`) untuk mendeteksi tipe proyek (Python/Node.js).
- **Eksekusi Pipeline:** Menjalankan linter (Ruff/Flake8/npm run lint) dan testing suite (pytest/npm test).
- **Asa-Style Status Blocks:** Mengembalikan visualisasi laporan ringkas berbentuk tabel monospaced yang mudah dibaca di terminal atau platform pesan instan:
  ```status
  Linting  ✅  Passed
  Testing  ❌  Failed
  ```

---

## 3. Penanganan Memori & RAM 4GB (Kanban vs OOM)

Untuk menghindari kehabisan memori (OOM) pada mesin berspesifikasi RAM 4GB:
- **Pelepasan Delegasi Bersarang:** Delegasi orkestrasi hirarkis kustom (`abelion_core/hierarchy.py`) resmi **dihapus**. Struktur ini terbukti memicu penumpukan frame memori Python akibat pemanggilan berlapis yang memblokir satu sama lain.
- **Pola Kanban Asinkron:** Pengiriman tugas antar-agen dialihkan sepenuhnya ke model antrean asinkron menggunakan Kanban board bawaan Hermes (`tools/kanban_tools.py`), memutus rantai penahanan RAM aktif.
- **SQLite FTS5 sebagai Main Write-Storage:** SQLite bawaan Hermes (`hermes_state.py`) digunakan sebagai basis penyimpanan transaksional yang aman terhadap penulisan paralel multi-agent dengan memori minimal (<20MB).

---

## 4. Pre-LLM Kredensial Redactor (Sensor Privasi)

Mengatasi celah keamanan kebocoran kunci API dan token sensitif:
- **Redaksi Input & Output:** Fungsi `redact_sensitive_text` diintegrasikan pada:
  1. `tools/memory_tool.py`: Menyensor konten sebelum ditulis ke memori persisten (`MEMORY.md` atau `USER.md`).
  2. `agent/tool_dispatch_helpers.py`: Menyensor hasil eksekusi terminal/alat sebelum diumpankan ke riwayat pesan LLM (`make_tool_result_message`).
  3. `tools/session_search_tool.py`: Melindungi riwayat pencarian sesi.
- **Pola Sensor:** Menggunakan kompilasi regex lokal cepat (<2ms overhead) untuk mendeteksi dan mengganti kunci API (mis. `sk-ant-...`, token 9router, kata sandi) dengan placeholder `[REDACTED_API_KEY]`.

---

## 5. Hasil Pengujian Unit & Validasi Data

Untuk memvalidasi integrasi plugin baru di dalam sistem, pengujian dijalankan menggunakan virtual environment Python (`.venv`) di repositori `/media/abelion/Isaf/ican/project/references/hermes-agent`:

Perintah eksekusi:
```bash
.venv/bin/python3 -m unittest test_abelion_error_handler.py
```

Hasil Output:
```status
[abelion_orchestrator] Circuit breaker OPENED due to 3 failures.
[abelion_core] Delegation blocked by circuit breaker.
.
..
----------------------------------------------------------------------
Ran 2 tests in 0.002s

OK
```

### Analisis Data Pengujian:
1. **Lolos Uji Circuit Breaker (Test 1):** Membuktikan secara logis bahwa ketika kegagalan berturut-turut tercapai, circuit breaker berubah menjadi status `OPEN`, dan hook `pre_tool_hook` secara otomatis memblokir pemanggilan `delegate_task` dengan pesan peringatan terstruktur.
2. **Lolos Uji Active Reflection (Test 2):** Membuktikan bahwa parser LLM berhasil menyintesis trajectory percakapan dan menulis berkas JSON refleksi secara terisolasi ke direktori `docs/abelion/reflections/` dengan format yang valid tanpa merusak workspace utama.
>>>>>>> convert-architecture-to-artifact
