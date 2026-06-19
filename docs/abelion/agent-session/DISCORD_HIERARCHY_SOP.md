# SOP: Discord Hierarchical Mapping (Abelion System)

## 1. Arsitektur Komunikasi
Struktur ini dirancang untuk mencegah *Context Leakage* pada sistem Multi-Agent Hierarchical.

| Hirarki Abelion | Entitas Discord | Aturan Main |
| :--- | :--- | :--- |
| **Me / Asa** | User / Admin | Memberikan instruksi High-Level di `#ceo-office`. |
| **CEO** | Multi-Agent Orchestrator | Menerima instruksi, memecah tugas, dan melakukan `abelion_delegate`. |
| **Division** | Category Manager | Mengelola kategori spesifik (e.g., Engineering, Research). |
| **Worker** | Channel Specialist | Eksekutor tugas spesifik di dalam channel di bawah kategorinya. |
| **Tools / Tasks** | Threads | Unit eksekusi terkecil. **WAJIB** digunakan untuk setiap tugas baru. |

## 2. Manajemen Thread (Zero-Alpha Isolation)
- **Nama Thread**: Harus mencerminkan Goal (e.g., `[DEV] Implement-OAuth`).
- **Lifecycle**: Buka thread saat tugas dimulai, **TUTUP/ARCHIVE** saat tugas selesai.
- **Memory Trigger**: Penutupan thread memicu rangkuman otomatis ke `MEMORY.md` melalui `abelion_core` plugin.

## 3. Monitoring & Status
- **Channel `#system-status`**: Digunakan khusus untuk output dari `abelion_test_model` dan `verify_model_health`.
- Jika API 9router/OC/GC limit, laporannya masuk ke sini, bukan di thread kerja.

## 4. Keamanan & Izin
- Matikan akses `Worker` ke channel `#ceo-office`.
- Pastikan `CEO` memiliki role `Administrator` atau izin `View All Channels`.
