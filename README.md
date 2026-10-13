# Naya Smart Calculator

Aplikasi kalkulator desktop untuk Windows, dibuat dengan Python dan CustomTkinter.

## Menjalankan dari sumber

Gunakan Python 3.8 atau lebih baru:

```powershell
py -m pip install -r requirements.txt
py main.py
```

Ketik ekspresi lewat keyboard atau gunakan tombol. `Enter` menghitung, `Esc`
menghapus ekspresi, dan tombol `( )` memilih kurung berikutnya secara otomatis.
Persentase mendukung ekspresi seperti `15% dari 200`. Tema dapat mengikuti
pengaturan sistem atau dipilih manual. Riwayat tersimpan di `naya_history.json`
di folder aplikasi.

## Membuat executable Windows

```powershell
py -m pip install pyinstaller
py -m PyInstaller --noconsole --onefile --collect-all customtkinter --name "Naya Smart Calculator" main.py
```

Executable dibuat di folder `dist`. File `naya_history.json` akan disimpan di
folder executable saat aplikasi dijalankan sebagai berkas `.exe`.

## Menjalankan tes

```powershell
py -m unittest discover -s tests
```
