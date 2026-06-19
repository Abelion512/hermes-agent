# Perbandingan Repositori Hermes Agent Kustom dan Upstream

> **Catatan penting:** Laporan ini berasumsi bahwa Anda memiliki repositori Hermes Agent versi kustom di GitHub yang dibangun di atas upstream `nousresearch/hermes-agent`. Tanpa akses ke repositori pribadi Anda, perbandingan ini disusun sebagai template yang dapat Anda isi berdasarkan perubahan aktual. Gunakan panduan ini untuk memeriksa perbedaan dan mendokumentasikannya dengan jelas.

## Fitur Utama Upstream

Repositori resmi *hermes‑agent* dari Nous Research menyediakan kerangka kerja agen AI self‑hosted dengan fitur berikut:

- **Learning loop bawaan:** Hermes menulis skill dari pengalaman, meninjau dan meningkatkan skill saat digunakan, serta membangun model pengguna melalui sistem memori FTS5【379018934104739†L533-L569】.
- **Support banyak model:** Pengguna dapat beralih antara model dari Nous Portal, OpenRouter, NovitaAI, NVIDIA NIM, Kimi/Moonshot, MiniMax, Hugging Face, dan OpenAI hanya dengan menjalankan `hermes model`【379018934104739†L541-L547】.
- **Terminal UI & CLI lengkap:** Terminal antarmuka mendukung pengeditan multiline, autocomplete perintah, histori percakapan, dan streaming output tool【379018934104739†L549-L551】.
- **Gateway multi-platform:** Agen terhubung ke Telegram, Discord, Slack, WhatsApp, Signal, dan CLI melalui satu proses gateway untuk sesi yang terus berjalan【379018934104739†L552-L556】.
- **Scheduler dan sub‑agen paralel:** Hermes menyediakan scheduler natural‑language dan dukungan delegasi sub‑agen untuk menjalankan alur kerja parallel【379018934104739†L560-L564】.
- **Eksekusi fleksibel:** Dapat berjalan di local, Docker, SSH, Singularity, Modal atau Daytona—bahkan di VPS berbiaya rendah【379018934104739†L566-L569】.

## Langkah Perbandingan

1. **Kloning upstream sebagai baseline:**

   ```bash
   # Clone upstream untuk referensi
   git clone https://github.com/nousresearch/hermes-agent.git upstream
   
   # Clone repositori pribadi Anda
   git clone https://github.com/<username>/<your-hermes-repo>.git my-hermes
   
   cd my-hermes
   
   # Tambahkan upstream remote
   git remote add upstream ../upstream
   ```

2. **Bandingkan konfigurasi dan file kunci:**

   - **`config.yaml` / `cli-config.yaml`**: periksa apakah Anda menambahkan default model atau provider baru, misalnya integrasi khusus ke API internal.
   - **`scripts/install.sh`**: lihat apakah ada perubahan dalam proses instalasi (penambahan dependensi, perubahan alamat repo). Upstream menggunakan satu baris `curl` untuk instalasi【340288179040835†L224-L249】; modifikasi apa pun perlu didokumentasikan.
   - **`hermes_state.py` atau modul memori lain:** periksa apakah Anda menambah format memori baru (misal vector store) atau parameter kompresi tambahan.
   - **File skill baru:** upstream memiliki 40+ skill built‑in dan menulis skill otomatis di direktori `.skills`. Jika repositori kustom memasukkan skill tambahan (contoh: penerjemah Bahasa Indonesia atau integrasi MLOps), catat nama, fungsi, dan bagaimana ia berbeda dari skill upstream.

3. **Pemeriksaan Dependensi dan Model Tools:**

   - Bandingkan `pyproject.toml` atau `requirements.txt` untuk melihat apakah ada library baru (misal `browser-use`, `camofox`, `crew-ai`) atau versi berbeda dari library upstream.
   - Jika Anda menambahkan model provider baru (misal Qwen 4.0 Beta) melalui modul `provider_config.py`, jelaskan API key yang diperlukan dan alasan pemilihan.

4. **Perubahan pada Tool Gateway:**

   - Upstream menggunakan Tool Gateway untuk integrasi browser, voice, diagram, MLOps, dsb【865977386280222†L61-L91】. Jika repositori kustom mengganti provider default (misal, menggunakan `browser-use` cloud mode alih‑alih `browserbase`), jelaskan parameter `.env` tambahan.

5. **Perbaikan Bug dan Peningkatan Kinerja:**

   - Jika repositori Anda berisi perbaikan bug tertentu (contoh: mempercepat caching, memperbaiki error saat `hermes model`), tambahkan ringkasan commit dan tautkan ke issue upstream jika relevan.
   - Dokumentasikan optimisasi kinerja seperti pengurangan pemanggilan API, pengaturan ulang concurrency sub‑agen, atau penambahan caching file.

6. **Penyesuaian Antarmuka Pengguna:**

   - Upstream CLI menggunakan interface bahasa Inggris default. Jika Anda menambahkan dukungan bahasa lain atau menyesuaikan prompt CLI, jelaskan perubahan pada `cli.py` dan file internasionalisasi.
   - Jelaskan perubahan estetika (warna, ikon) dan bagaimana hal tersebut memengaruhi pengalaman pengguna.

## Contoh Tabel Perbandingan

Berikut contoh tabel untuk meringkas perbedaan utama. Anda dapat mengisinya setelah melakukan analisis diff.

| Aspek | Upstream Hermes Agent | Repositori Anda | Perbedaan |
|---|---|---|---|
| **Support Model** | Mendukung Nous Portal, OpenRouter, NovitaAI, dll. lewat `hermes model`【379018934104739†L541-L547】 | <model khusus> | Contoh: menambahkan integrasi `MyCustomLLM` dengan API internal |
| **Skill Built‑in** | 40+ skill built‑in + auto‑skill【340288179040835†L46-L49】 | <jumlah skill> | Contoh: menambah skill `Translate_BI` untuk Bahasa Indonesia |
| **Browser Provider** | Browserbase, Browser Use, Firecrawl, Camofox, local Chrome/CDP【865977386280222†L61-L91】 | <provider> | Contoh: mengganti default ke `browser-use` dengan fingerprint stealth |
| **Instalasi** | One‑liner install via curl【340288179040835†L224-L249】 | <install script baru> | Contoh: menambahkan script Ansible untuk deployment server |
| **Konfigurasi** | `hermes setup` wizard【340288179040835†L217-L249】 | <perubahan> | Contoh: menyediakan konfigurasi non‑interactive dengan file YAML |
| **Perubahan lainnya** | - | - | - |

### Kesimpulan

Melakukan perbandingan sistematis antara repositori kustom dan upstream penting untuk menjaga keberlanjutan dan kompatibilitas dengan ekosistem Hermes. Gunakan `git diff` untuk mengidentifikasi perubahan, dokumentasikan penyesuaian konfigurasi, skill, provider model, dan perbaikan bug. Dengan menyusun ringkasan ini, Anda akan lebih mudah memelihara proyek serta berkontribusi kembali ke repositori upstream jika diperlukan.