# Development Standards: jules Branch (QA & Integration)

Dokumen ini mendefinisikan standar keselamatan, kualitas kode, dan manajemen memori yang wajib dipatuhi oleh seluruh armada AI dan pengembang manusia yang berkontribusi di cabang integrasi `jules` (QA/Staging).

---

## 1. Proteksi Memori (RAM Guard & GC)

Untuk mencegah kegagalan Out of Memory (OOM) pada mesin berspesifikasi RAM terbatas (4GB/5GB), setiap modul baru wajib mengadopsi mekanisme pertahanan berikut:
* **Threshold Batas Aman**: Batasi penggunaan RAM sistem maksimal **80%**.
* **Garbage Collection (GC)**: Pemicuan pembersihan sampah memori (`gc.collect()`) secara eksplisit wajib dijalankan di awal turn atau sebelum pemanggilan tool jika pemakaian memori RSS proses Hermes melebihi **500MB**.
* **Blokir Tool Berat**: Panggilan tool yang memicu subproses eksternal berat (seperti browser headless, `run_command`, atau `execute_code`) wajib diblokir jika penggunaan RAM sistem sudah melampaui 80%.

---

## 2. Struktur Memori Pengalaman (Experiential RAG)

Setiap profil Hermes wajib dibekali dengan database pengalaman SQLite FTS5 lokal terisolasi:
* **Nama Database**: `experience_fts.db` disimpan di dalam direktori profil `get_hermes_home() / memories/`.
* **Inisialisasi Otomatis**: Database dan tabel FTS5 wajib diinisialisasi secara otomatis ketika plugin dimuat (pada fungsi `register(ctx)`), bukan menunggu turn chat selesai.
* **Skema Virtual Table**:
  ```sql
  CREATE VIRTUAL TABLE experiences USING fts5(
      session_id UNINDEXED,
      timestamp UNINDEXED,
      summary,
      status,
      errors,
      lessons,
      recommendations,
      raw_content
  );
  ```
* **RAG Iteration Limit**: Batasi panggilan tool pencarian dokumen `knowledge_search` maksimal **3 kali per sesi** guna menghindari infinite loop pencarian dokumen.

---

## 3. PII Redaction & Proteksi Kredensial

* **Filter Kredensial**: Semua token API, password, dan kunci privat (seperti kunci 9Router) wajib disensor (masking/REDACTED) sebelum disimpan ke dalam database bersama, Kanban task comments, atau log publik.
* **Isolasi Obsidian Exporter**: Berkas catatan refleksi markdown yang diekspor ke Obsidian Vault wajib disimpan ke dalam subfolder terpisah berdasarkan nama profil aktif (misal: `HermesVault/<profile_name>/`) untuk mencegah bentrokan file antar profil.

---

## 4. Alur Kerja Git & Kebersihan Repositori

* **Sterilisasi File Sampah**: Dilarang melakukan komit terhadap berkas log temporer (`.log`), database sementara, berkas kredensial (`.env`, `auth.json`), dan folder pengujian temporer (`scratch/`). Semua berkas tersebut wajib masuk dalam `.gitignore`.
* **Kebijakan Resolusi Konflik**: Saat menyinkronkan pembaruan dari upstream, pengembang wajib mengutamakan kode upstream (`upstream/main`) menggunakan strategi `-X theirs` guna mempertahankan sifat modular basis kode inti.
