# Model Kompatibel untuk Hermes Agent (Berbayar dan Gratis)

Hermes Agent tidak menyediakan model bawaan; agen ini menggunakan berbagai Large Language Model (LLM) melalui API pihak ketiga. Karena itu, pemilihan model berpengaruh besar terhadap performa dan biaya. Laporan ini merangkum penyedia dan model yang kompatibel dengan Hermes, dibagi dalam kategori gratis (tanpa atau dengan kartu kredit) dan berbayar.

## Sumber Penyedia LLM

Dokumentasi Hermes menyebutkan bahwa agent dapat terhubung ke banyak provider seperti Nous Portal, OpenAI, Anthropic, OpenRouter, NovitaAI, z.ai/GLM, Kimi, MiniMax, NVIDIA NIM, GMI Cloud, Ollama (vLLM lokal), Google Gemini, AWS Bedrock, dan lainnya【207489193849511†L48-L117】. Penyedia tertentu memerlukan kredensial API; yang lain menggunakan OAuth melalui `hermes model`. Setiap provider menawarkan model yang berbeda serta tier gratis dan berbayar.

### Provider Dengan Akses Gratis Tanpa Kartu Kredit

Berikut penyedia yang menawarkan tier gratis yang sesuai dengan Hermes tanpa perlu kartu kredit. Mereka ideal untuk percobaan atau beban kerja ringan.

| Penyedia | Model dan Kuota Gratis | Informasi Penting |
|---|---|---|
| **Ollama (Lokal)** | Menjalankan model secara lokal di mesin pengguna. Artikel OpenClaw menyoroti bahwa Qwen 3.5 27B (quantized 27B) adalah pilihan terbaik untuk Hermes karena memiliki context 128K, VRAM minimal 16 GB, serta kemampuan tool‑calling yang andal【667953570341297†L81-L90】. Qwen 3 8B (8 GB VRAM) dan Gemma 4 12B juga tersedia sebagai opsi ringan【667953570341297†L81-L87】. Karena model diunduh lokal, tidak ada biaya per API, tidak perlu kredensial, tetapi memerlukan hardware memadai. |
| **Groq** | Penyedia hardware LPU memberikan free tier ~14 400 request/hari dan 30 request per menit tanpa kartu kredit, cukup untuk 25–50 tugas Hermes per hari【667953570341297†L103-L129】. Model gratis mencakup Llama 4 Scout, Llama 3.3 70B, dan Gemma 2 9B【667953570341297†L109-L115】. |
| **OpenRouter (Free Models)** | OpenRouter menawarkan 29 model gratis seperti Gemma 4 26B, Llama 4 Maverick, dan Qwen3‑235B; rate limit sekitar 200 request/hari tanpa kartu kredit【667953570341297†L109-L115】. |
| **Google AI Studio** | Menyediakan akses ke Gemini 2.5 Flash dan Gemini 2.5 Flash Lite dengan limit 15 RPM dan 1 500 request/hari, tanpa kartu kredit. Ini cukup untuk 20–40 tugas Hermes sehari【667953570341297†L109-L120】. |
| **xAI Grok OAuth** | Hermes mendukung login OAuth ke Grok (xAI) melalui `hermes model` tanpa memerlukan API key【207489193849511†L75-L97】. Saat laporan ini dibuat, Grok menawarkan penggunaan gratis terbatas. |

### Provider Gratis Dengan Kartu Kredit (Tier Gratis Memerlukan Verifikasi)

Beberapa penyedia menawarkan tier gratis tetapi meminta verifikasi kartu kredit atau metode pembayaran saat pendaftaran:

| Penyedia | Model Gratis / Tier Gratis | Catatan |
|---|---|---|
| **Anthropic** | Melalui OAuth, Hermes dapat mengakses Claude Max dengan kredit gratis bulanan【207489193849511†L59-L60】. Anthropic mungkin meminta kartu kredit untuk verifikasi identitas meski penggunaan awal gratis. |
| **Azure AI Foundry / AWS Bedrock** | Cloud provider ini menawarkan tier gratis terbatas bagi pengguna baru. Setup memerlukan akun cloud dengan metode pembayaran, meski penggunaan awal gratis【207489193849511†L100-L103】. |
| **Google Gemini OAuth** | Login melalui Google Gemini CLI memungkinkan akses ke model Gemini tanpa API key; namun Google sering meminta kartu kredit untuk mengaktifkan layanan cloud dalam jangka panjang【207489193849511†L94-L98】. |
| **Nous Portal Free Tier** | Nous Portal memberikan kredit bulanan gratis untuk pengguna baru. Akses ke >300 model, termasuk Claude, GPT‑5.5, Kimi, DeepSeek, Qwen, GLM【214101224775704†L108-L112】. Pendaftaran memerlukan kartu kredit untuk verifikasi, tetapi kredit awal mencakup penggunaan dasar. |

### Provider Berbayar (Membutuhkan Kartu Kredit / Subscription)

| Provider | Model / Fitur | Rekomendasi |
|---|---|---|
| **Nous Portal (Plus, Super, Ultra)** | Menyediakan ratusan model frontier dengan berbagai harga. Semua tier berbayar menyediakan kredit bulanan untuk Hermes Agent serta akses ke tool gateway【214101224775704†L108-L112】. Cocok untuk penggunaan intensif karena menggabungkan banyak model premium. |
| **OpenAI API (ChatGPT/GPT‑5.x)** | Model GPT 4.5, GPT‑5.5 (asumsi rilis 2026) memiliki reasoning dan tool‑calling terdepan. Pengguna harus menambahkan `OPENAI_API_KEY` di konfigurasi【207489193849511†L98-L99】. Terbaik untuk proyek produksi ketika kualitas jawaban menjadi prioritas. |
| **Anthropic (Claude 3 & Max)** | Model Claude 3 atau Max terkenal karena batas konteks besar (200K) dan reasoning yang kuat. Digunakan melalui OAuth atau API key【207489193849511†L59-L60】. |
| **MiniMax** | Menyediakan model via API key (`MINIMAX_API_KEY`) dengan kualitas tinggi dalam bahasa Mandarin dan kemampuan tool‑calling【207489193849511†L72-L73】. |
| **Kimi/Moonshot** | Menawarkan model bahasa Mandarin/Inggris dengan konteks panjang. Tersedia via API key atau OAuth【207489193849511†L65-L67】. |
| **NovitaAI** | Menyediakan 200+ model melalui `NOVITA_API_KEY` dengan akses ke API komputasi GPU【207489193849511†L62-L63】. |
| **Arcee AI, GMI Cloud, xAI (paid tiers), Kilo Code, DeepSeek, Hugging Face** | Semua menyediakan model melalui API key; harga bervariasi sesuai penggunaan【207489193849511†L68-L100】. |

## Pertimbangan Pemilihan Model

1. **Kemampuan Tool‑Calling:** Hermes membutuhkan model yang mendukung *tool calling* (fungsi JSON) dan konteks minimal 64K token agar dapat menggunakan skill dan memori dengan efisien. Artikel OpenClaw menyoroti bahwa Qwen 3.5 27B (quantized Q4) memberikan tool‑calling andal dengan VRAM minimal 16 GB【667953570341297†L81-L90】.

2. **Biaya vs. Kinerja:** Local models (Ollama) menghilangkan biaya API tetapi memerlukan hardware GPU. Penyedia cloud gratis cocok untuk eksperimen dengan batas tugas harian. Penyedia berbayar menawarkan performa lebih baik dan jatah token tinggi untuk produksi.

3. **Bahasa dan Domain:** Model seperti MiniMax dan Kimi unggul di bahasa Mandarin, sementara GPT‑series, Claude, DeepSeek, dan Qwen cocok untuk bahasa Inggris dan multi‑bahasa. Pilih berdasarkan bahasa pengguna.

4. **Ketersediaan dan Rate Limit:** Free tier memiliki rate limit ketat. Gunakan routing adaptif dalam Hermes untuk mendistribusikan beban antar provider (Groq untuk tugas cepat, OpenRouter untuk diversifikasi, Nous Portal saat memerlukan model premium).

### Ringkasan

Hermes Agent mendukung banyak provider, dari local inference sampai cloud premium. Untuk penggunaan gratis tanpa kartu, opsi terbaik adalah menjalankan model lokal via Ollama (Qwen 3.5 27B) jika hardware memungkinkan atau memanfaatkan free tier dari Groq, OpenRouter, dan Google AI Studio【667953570341297†L109-L120】. Jika kualitas tertinggi dibutuhkan, model berbayar seperti GPT‑5.x (OpenAI) atau Claude 3 (Anthropic) dapat diintegrasikan melalui API key atau subscription. Pemilihan model harus mempertimbangkan trade‑off antara biaya, performa, bahasa, dan rate limit.