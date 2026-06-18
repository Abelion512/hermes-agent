# Menjalankan Hermes Agent dengan Browser Nyata dan Akun Autentik

Hermes Agent mendukung kontrol browser penuh melalui beberapa provider (Browserbase, Browser Use, Firecrawl, Camofox, dan local Chromium)【865977386280222†L61-L72】. Biasanya, agen meluncurkan sesi baru dengan cookie bersih. Namun, beberapa tugas memerlukan login ke akun pribadi (misal Gmail, GitHub, atau layanan berbayar). Laporan ini menjelaskan cara menggunakan profil browser nyata atau mengimpor status autentikasi agar agen dapat bekerja dengan sesi Anda, bukan sandbox uji.

## Pendekatan: Profil Chrome dan Persistent Session

### Menggunakan agent‑browser dengan profil Chrome

Proyek `agent-browser` menyediakan CLI untuk meluncurkan dan mengontrol browser. Fitur *sessions* memungkinkan reuse cookies dan storage state. Dokumentasi menjelaskan bahwa Anda dapat menyalin profil Chrome yang ada dengan opsi `--profile`【372162304856941†L85-L102】:

```bash
# Menjalankan agen dengan profil Chrome default (macOS/Windows/Linux)
agent-browser --profile Default open https://gmail.com

# Gunakan nama profil spesifik
agent-browser --profile "Work" open https://app.example.com

# Alternatif via environment variable
AGENT_BROWSER_PROFILE=Default agent-browser open https://gmail.com
```

Dalam mode ini, agent-browser menyalin direktori profil Anda ke direktori sementara dan meluncurkan Chrome dengan cookies, localStorage, dan state ekstensi dari akun Anda【372162304856941†L85-L106】. Profil asli tetap read‑only; setelah sesi ditutup, salinan sementara dihapus. Fitur ini bekerja pada Chrome, Chrome Canary, Chromium, dan Brave.

### Profil Persisten

Jika Anda ingin menyimpan state autentikasi antarsesi, berikan path direktori khusus:

```bash
# Gunakan direktori persisten
agent-browser --profile ~/.myapp-profile open myapp.com

# Login sekali, lalu reuse sesi
agent-browser --profile ~/.myapp-profile open myapp.com/dashboard
```

Direktori tersebut menyimpan cookies, localStorage, IndexedDB, service workers, dan cache【372162304856941†L111-L132】. Sesi ini bertahan saat browser ditutup dan dibuka kembali.

### Impor State Autentikasi

Untuk mengimpor state dari Chrome yang sedang berjalan (tanpa menyalin profil penuh), lakukan langkah berikut【372162304856941†L139-L170】:

1. Jalankan Chrome dengan remote debugging (`--remote-debugging-port=9222`), lalu login ke situs target.
2. Simpan state dengan `agent-browser --auto-connect state save ./my-auth.json`.
3. Muat state ke sesi baru: `agent-browser --state ./my-auth.json open https://app.example.com/dashboard`.
4. Gunakan `--session-name` agar state tersimpan otomatis antarsesi.

State file berisi token cookies dalam teks biasa; pastikan file ini tidak disimpan di repositori publik dan dienkripsi jika diperlukan【372162304856941†L135-L173】.

### Menggunakan library `browser-use` dalam kode Python

Jika Anda membangun agen melalui Python, library `browser-use` memudahkan pengelolaan sesi. Artikel panduan menjelaskan bahwa objek `Browser` memiliki parameter `user_data_dir` dan `profile_directory` untuk menggunakan profil Chrome nyata【754623781024331†L119-L134】. Contoh:

```python
import asyncio
from browser_use import Agent, Browser, ChatOpenAI

async def main():
    browser = Browser(
        executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        user_data_dir="~/Library/Application Support/Google/Chrome",
        profile_directory="Default",
        keep_alive=True
    )
    agent = Agent(
        task="Buka Gmail dan periksa jumlah email tak terbaca",
        browser=browser,
        llm=ChatOpenAI(model="gpt-4.1-mini"),
    )
    await agent.run()
asyncio.run(main())
```

Parameter `keep_alive=True` memastikan sesi tetap terbuka sehingga tugas selanjutnya dapat menggunakan tab dan cookies yang sama【754623781024331†L92-L113】. Opsi `storage_state` juga tersedia jika Anda hanya ingin memuat cookies tertentu dari file JSON【754623781024331†L149-L173】.

### Integrasi dengan Hermes

Dalam konfigurasi Hermes, Anda dapat memilih provider browser `agent-browser` melalui `hermes setup tools → Browser Automation`. Hermes kemudian akan menghubungkan tools‐nya dengan sesi `agent-browser` yang Anda jalankan secara terpisah atau melalui `hermes browser connect`. Dengan menggunakan opsi `--profile` atau direktori persisten, sesi Hermes akan mewarisi state autentikasi dari profil tersebut. Alternatif lainnya, Hermes dapat terhubung ke browser lokal Anda melalui CDP (Chrome DevTools Protocol) menggunakan `hermes browser connect`【865977386280222†L69-L91】. Pastikan untuk menutup Chrome sebelum menyalin profil agar tidak terjadi konflik file.

## Pertimbangan Keamanan

- **Privasi data:** Menyalin profil Chrome berarti cookies, token, dan data sensitif lainnya ikut disalin. Gunakan pada mesin lokal yang aman dan hindari memindahkan file profil ke server yang tidak terpercaya.
- **Remote debugging:** Jalankan Chrome dengan `--remote-debugging-port` hanya pada komputer yang Anda kontrol, karena port ini memberikan akses penuh ke browser【372162304856941†L139-L151】.
- **Enkripsi state:** Simpan file state (`my-auth.json`) di luar repositori dan enkripsi jika berisi token akses【372162304856941†L172-L173】.
- **Patuh Terms of Service:** Pastikan penggunaan automation mematuhi kebijakan situs; beberapa layanan melarang scraping atau penggunaan bot.

## Kesimpulan

Menggunakan browser nyata dalam Hermes Agent memungkinkan otomatisasi tugas yang memerlukan login, tanpa harus memasukkan kredensial ke model. Opsi `--profile` dan `--session-name` dari `agent-browser`, atau `user_data_dir`/`profile_directory` dari `browser-use`, menyalin atau memanfaatkan profil Chrome Anda untuk memulihkan cookies dan localStorage【372162304856941†L85-L132】. Gunakan persistent session untuk beban kerja jangka panjang dan selalu jaga keamanan serta privasi data ketika memanfaatkan fitur ini.