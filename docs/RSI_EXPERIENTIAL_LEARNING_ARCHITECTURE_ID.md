# Desain Arsitektur: Sistem RSI & Pembelajaran Berbasis Pengalaman (Experiential Learning)

## 1. Filosofi: Zero-Alpha & Experiential Learning
Tujuan utama arsitektur ini adalah memindahkan kebergantungan agen dari sekadar bobot pre-training LLM (Prompt Engineering) menuju **Basis Pengetahuan Berbasis Pengalaman** (Experience Engineering).
Terinspirasi dari paradigma AlphaGo Zero / Zero-Alpha, agen belajar dengan mempraktikkan. Keberhasilan dan kegagalan dalam eksekusi tugas di-parsing dan diubah menjadi data pelatihan lokal yang persisten (Memori). Agen lebih mengandalkan akumulasi pengalamannya dalam suatu proyek atau persona dibandingkan bias bawaan pre-training-nya.

## 2. Isolasi Memori Berbasis Persona
Untuk mencegah keruntuhan konteks (context collapse) dan halusinasi antar domain yang berbeda, memori disegregasi secara ketat.
- **Batasan Global:** Aturan sistem yang statis.
- **Memori Persona (`~/.config/hermes/profiles/`):** Profil memori yang dipisah untuk peran berbeda (contoh: `coding_agent.md`, `seo_agent.md`, `business_agent.md`).
- **Memori Proyek (`AGENTS.md` / `.plans/`):** Konteks yang secara ketat terikat pada direktori kerja saat ini.
- **Mekanisme:** Saat persona tertentu dipanggil, hanya memorinya masing-masing yang dimuat ke dalam *context window*, menjaga *Semantic Memory* tetap tajam, presisi, dan efisien secara token.

## 3. Toleransi Kesalahan Multi-Agen & Hierarki
Sistem ini menggunakan struktur hierarki "Managed Agents": **Agen CEO -> Agen Divisi -> Agen Pekerja (Worker)**.
- **Alur Eksekusi:** CEO mendelegasikan tugas ke sub-agen khusus.
- **Toleransi Kesalahan (Fault Tolerance) & Penanganan Error:**
  - **Timeout/Crash:** Jika sub-agen mengalami crash, timeout, atau mengembalikan data sampah, CEO tidak akan ikut crash. CEO akan menangkap exception (error) tersebut.
  - **Fallback:** CEO dapat mencoba ulang tugas dengan model cadangan, memanggil sub-agen lain, atau melakukan degradasi secara mulus (graceful degradation).
  - **Sistem Umpan Balik (Feedback Loop):** Kegagalan dicatat ke dalam memori pelatihan sub-agent sehingga kesalahan yang sama tidak terulang.
  - **Pemutus Arus (Circuit Breaker):** Maksimal 3 kali percobaan ulang untuk tugas yang gagal sebelum sistem di-pause dan eskalasi ke pengguna (manusia).

## 4. Manajemen Sumber Daya Interaktif (Gaya Codex-CLI)
Kehabisan token, limit API (Rate Limits), atau error API tidak akan lagi mengakibatkan hard crash.
- **Interupsi Interaktif:** Saat limit tercapai di tengah tugas yang memakan waktu lama (contoh: perintah `/goal`), perulangan (loop) akan di-pause secara aman.
- **Opsi CLI yang Ditampilkan ke Pengguna:**
  1. **Tunggu (Wait):** Menahan state hingga limit di-reset.
  2. **Ganti Model (Switch Model):** Mengganti provider secara langsung (hot-swap, misal dari `Antigravity` ke `Opencode`) dan melanjutkan tanpa hambatan.
  3. **Batal/Reset:** Membuang konteks saat ini dan memulai dari awal.

## 5. Efisiensi Sumber Daya (RAM & Caching)
Dioptimalkan untuk lingkungan Linux dengan RAM 4GB dan API proxy kelas gratis (seperti 9router).
- **Pengumpulan Sampah (Garbage Collection):** Eksekusi `gc.collect()` secara eksplisit setelah tugas selesai untuk membersihkan memori RAM yang tidak memiliki referensi.
- **Caching Universal:**
  - Dukungan untuk **Anthropic Cache-Control** (`{"cache_control": {"type": "ephemeral"}}`).
  - Dukungan untuk **OpenAI Prefix Caching**: Inti *System Prompt* dan histori awal dibekukan (statis). Variabel dinamis (seperti timestamp) dipindahkan ke bagian akhir prompt untuk memastikan tingkat *cache hit* maksimal lintas provider proxy.
- **Kompresi Pintar (Smart Compression):** Menggantikan pemotongan pesan (naive truncation). Konteks diringkas secara aman tanpa membuang fakta krusial (seperti URL atau trace error) yang ditandai dengan tag `<memory-context>`.
