# Third-party notices

## Hamlib 4.7.2 (Windows x64 binaries)

The directory `vendor/hamlib-w64-4.7.2/` contains official Hamlib command-line utilities
(`rigctl`, `rigctld`, and related files) from:

- Project: https://github.com/Hamlib/Hamlib
- Release: 4.7.2 (`hamlib-w64-4.7.2.zip`)
- License: GNU LGPL (library) and GNU GPL (some components). See files under
  `vendor/hamlib-w64-4.7.2/hamlib-w64-4.7.2/` (`COPYING.txt`, `COPYING.LIB.txt`, `LICENSE.txt`).

Hamlib is redistributed here so a fresh `git clone` works on Windows without a separate
Hamlib install. Source code is available from the Hamlib project above.

To refresh the bundled Windows build (maintainers):

```powershell
.\scripts\update-vendor-hamlib.ps1
```
