# Pengenalan & Pengalaman Implementasi Hermes Agent

Dokumen ini membagikan pengalaman, arsitektur, usecase, serta pengelolaan memori praktis berdasarkan pengerjaan integrasi dan kustomisasi pada repositori **Hermes Agent**.

---

## 1. Apa itu Hermes Agent?

Hermes Agent bukan sekadar chatbot biasa. Hermes adalah personal AI agent tangguh yang menjalankan satu *core engine* yang sama di berbagai antarmuka:
- **Command Line Interface (CLI)**: Untuk eksekusi cepat langsung dari terminal.
- **Terminal User Interface (TUI)**: Antarmuka berbasis teks interaktif yang kaya menggunakan Ink (React).
- **Messaging Gateway**: Terhubung ke lebih dari 20 platform seperti Telegram, Discord, Slack, WhatsApp, Signal, dan Matrix.
- **Electron Desktop App**: Antarmuka desktop terpadu.

### Filosofi Core Desain
Hermes didesain dengan prinsip **Narrow Waist, Wide Edge**:
1. **Prompt Caching Stabil**: Setiap turn dalam percakapan panjang menggunakan prefix ter-cache untuk menekan biaya API dan meningkatkan latensi. Modifikasi system prompt di tengah jalan sangat dihindari.
2. **Ekstensi di Sisi Edge**: Kemampuan baru ditambahkan via plugin, skills, atau CLI command, bukan dengan memperbesar *core model tools* yang dikirimkan pada setiap API call.

---

## 2. Usecases Utama yang Diimplementasikan

Dalam proyek kustomisasi ini, kami membangun beberapa sub-sistem pendukung (dikelompokkan dalam `abelion_core` plugin) yang memperluas fungsionalitas dasar:

- **Circuit Breaker**: Mencegah kegagalan beruntun pada API call jika model mengalami limitasi kuota (rate limit) atau error berulang.
- **Link Tracker**: Melacak tautan yang dikunjungi oleh browser agent untuk ekstraksi konteks dan sinkronisasi referensi.
- **RAM Monitor**: Mengawasi penggunaan memori secara real-time untuk mencegah Out Of Memory (OOM) saat agent melakukan pemrosesan data besar atau browsing.
- **Obsidian Exporter**: Membantu mengekspor riwayat riset dan sesi ke format Markdown yang kompatibel dengan Obsidian vault.
- **Loop Detector**: Mencegah agent terjebak dalam siklus pemanggilan tool yang redundan secara rekursif.

---

## 3. Strategi Pengelolaan Memori yang Enak

Salah satu aspek krusial dalam interaksi agent jangka panjang adalah memori yang praktis dan efisien (*memory yang enak*). Berikut adalah pendekatan yang kami gunakan:

### A. Pembagian Memori Berdasarkan Dimensi Waktu & Konteks
1. **Short-Term Memory (Context Caching)**: Memanfaatkan prompt caching tingkat provider untuk menyimpan riwayat chat aktif.
2. **Semantic Memory (FTS5 + Vector)**: Menyimpan pengalaman terformat secara otomatis ke SQLite lokal (`hermes_state.py`). Kita memanfaatkan pencarian Full-Text Search (FTS5) agar pencarian kembali cepat dan hemat biaya dibandingkan full vector search di setiap langkah.
3. **Structured Experience (RSI - Reflective Self-Instruction)**: Saat agent mendeteksi kegagalan atau kesuksesan penting, agent menulis berkas refleksi berformat JSON secara otomatis di direktori `docs/abelion/reflections/`. Refleksi ini dibaca kembali saat agent membutuhkan konteks pemecahan masalah serupa.

### B. Tips Praktis Pengelolaan Memori
- **Batasi Ukuran Sesi**: Gunakan kebijakan reset otomatis (`session_reset`) berbasis durasi idle (contoh: 1440 menit) untuk menjaga agar context window tidak membengkak secara tidak perlu.
- **Pruning Berkala**: Lakukan pembersihan riwayat sesi lama secara otomatis (`session_store_max_age_days: 90`) untuk menjaga performa pembacaan database status.
- **Gunakan Caching Variable**: Jangan melakukan resolusi ulang untuk variabel lingkungan statis di dalam loop iterasi chat.

---

## 4. Pembelajaran dari Proses Penggabungan (Merge & Upstream Sync)

Saat bekerja dengan repositori fork yang aktif berkembang secara paralel dengan upstream:
1. **Gunakan Cabang QA/Staging (`jules`)**: Gabungkan semua cabang fitur ke cabang integrasi ini terlebih dahulu sebelum menyentuh cabang utama (`main`). Hal ini meminimalkan risiko kerusakan di cabang produksi.
2. **Prioritaskan Upstream pada Konflik File Inti**: Ketika terjadi konflik kode pada struktur inti seperti parser konfigurasi (`gateway/config.py`), utamakan arsitektur upstream (`-X ours` dari sisi main) untuk menjaga modularitas, sembari menyisipkan kustomisasi lokal secara selektif.
3. **Casing Berkas Sensitif pada Lintas OS**: Hindari duplikasi berkas dengan perbedaan casing nama file (seperti `FILE.md` dan `file.md`) karena akan menimbulkan konflik tak terlacak di sistem file non-case-sensitive seperti macOS atau Windows. Selalu gunakan lowercase dengan pemisah underscore.
