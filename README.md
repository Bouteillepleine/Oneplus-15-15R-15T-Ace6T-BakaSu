# 🚀 OnePlus BakaSU Kernel Builder

GitHub Actions workflow for building flashable **BakaSU GKI kernels** for supported OnePlus devices.

It syncs Android GKI sources, adds **BakaSU**, optionally applies **SUSFS**, and packages the result as an **AnyKernel3 ZIP**.

> **BakaSU** is the project previously published as **ReSukiSU** (`ReSukiSU/ReSukiSU` → `Baka-SU/BakaSU`).
> Same tree, new name — output ZIPs are now named `AK3_BakaSU_…`.

---

## 📱 Supported Devices

| Device | ID | Codename | SoC | Default GKI release | Kernel |
|---|---|---|---|---|---|
| OnePlus 15 | `oneplus15` | `Infinity` | `sm8850` | `android16-6.12-2025-06` | 6.12.23 |
| OnePlus 15T | `oneplus15t` | `Infinity` | `sm8850` | `android16-6.12-2025-06` | 6.12.23 |
| OnePlus 15R | `oneplus15r` | `macan` | `sm8845` | `android16-6.12-2025-09` | 6.12.38 |
| OnePlus Ace 6T | `ace6t` | `macan` | `sm8845` | `android16-6.12-2025-09` | 6.12.38 |
| OnePlus Pad 3 Pro | `pad3pro` | `canoe` | `sm8850` | `android16-6.12-2025-12` | 6.12.58 |
| OnePlus Pad 4 | `pad4` | `canoe` | `sm8850` | `android16-6.12-2025-12` | 6.12.58 |

> This builder produces a **generic GKI** `kernel_aarch64` Image. The resulting
> Image depends only on the **GKI release branch** and the **kernel suffix** —
> the device selects nothing else, so every device on the same release gets a
> byte-identical Image and only the ZIP name differs.
>
> Use `GKI_RELEASE` to build any device against a different release; the table
> above is only the default. The September 2026 OTA moved OnePlus 15 and 15R to
> **6.12.58 / android16-6** (a KMI generation bump), so pick
> `android16-6.12-2025-12` if your firmware is on that OTA.

### Selectable GKI releases

`GKI_RELEASE` accepts every buildable AOSP `android16-6.12` release:

| GKI release | Kernel | KMI | Notes |
|---|---|---|---|
| `android16-6.12-2025-06` | 6.12.23 | 5 | OnePlus 15 / 15T launch firmware (retired upstream, auto-redirected to `deprecated/`) |
| `android16-6.12-2025-09` | 6.12.38 | 5 | OnePlus 15R / Ace 6T launch firmware |
| `android16-6.12-2025-12` | 6.12.58 | 6 | Sept-2026 OTA, Pad 3 Pro / Pad 4 |
| `android16-6.12-2026-03` | 6.12.69 | 6 | OnePlus 15 / 15T / 15R / Ace 6T / Pad 3 Pro / Pad 4 (no OnePlus OTA on this release yet) |
| `android16-6.12-2026-06` | 6.12.81 | 6 | OnePlus 15 / 15T / 15R / Ace 6T / Pad 3 Pro / Pad 4 (no OnePlus OTA on this release yet) |
| `android16-6.12-2026-09` | 6.12.92 | 6 | OnePlus 15 / 15T / 15R / Ace 6T / Pad 3 Pro / Pad 4 (no OnePlus OTA on this release yet) |

> Anything past `2025-12` is a plain AOSP branch — KMI-6, so it boots on
> post-OTA firmware, but no OnePlus build has ever shipped it.
>
> Not offered: `2025-07` / `2025-08` (the manifest branch exists but Google
> deleted the matching `kernel/common` ref, so `repo sync` cannot resolve it),
> `2025-05-exp` (KMI 4), `-kminext` (KMI 7), the moving `-sp` / `-lts` tips and
> the `-desktop` variants.

### What `DEVICE=all` builds

One kernel per GKI release, not one per device:

| GKI release | Kernel | KMI | Flashable on |
|---|---|---|---|
| `android16-6.12-2025-06` | 6.12.23 | 5 | OnePlus 15 / 15T |
| `android16-6.12-2025-09` | 6.12.38 | 5 | OnePlus 15R / Ace 6T |
| `android16-6.12-2025-12` | **6.12.58** | 6 | all six devices |
| `android16-6.12-2026-03` | 6.12.69 | 6 | all six devices |
| `android16-6.12-2026-06` | 6.12.81 | 6 | all six devices |
| `android16-6.12-2026-09` | 6.12.92 | 6 | all six devices |

> ⚠️ A KMI-6 kernel (6.12.58 and newer) will not load the KMI-5 `vendor_dlkm`
> modules shipped by firmware on 6.12.23 or 6.12.38, and vice versa — match the
> kernel to the firmware you are actually running.

Pinning `GKI_RELEASE` with `DEVICE=all` builds **that one release only**, not six
copies of it. Pinning it with a single device builds that release for that device
and labels the ZIP accordingly.

---

## ✨ Features

- BakaSU integration
- Optional SUSFS
- Optional Baseband Guard / ✨LSM Do not enable as it does not work with 6.12 kernels !✨
- Optional Netfilter + IPSet
- Optional BBR + ECN
- Optional BBRv3 backport (KMI-safe on android16-6.12)
- Net schedulers built in: `fq`, `fq_codel`, `cake`
- Optional ADIOS block MQ I/O scheduler
- Optional Sultan-derived power/memory tweaks (off by default)
- Optional Unicode bypass patch
- Flashable AnyKernel3 ZIP
- GitHub Release or artifact output
- Build logs, hashes, and summary

---

## 🚀 Quick Start

1. Fork this repo
2. Open **Actions**
3. Run the workflow
4. Select your device and options
5. Download the generated ZIP

---

### SUSFS across GKI releases

susfs4ksu rebases its kernel-side patch onto one GKI sublevel at a time, so
upstream only ever matches a single release — `bd27568` moved it to 6.12.92 and
it stopped applying to 6.12.23 through 6.12.81. The builder reconciles it:
rejected hunks are dropped from the patch and their code re-inserted on anchors
that exist on every release, matched by the content a hunk adds rather than by
`@@` line numbers, which every rebase renumbers. A reject with no known
re-insertion is still a hard failure, so a kernel never ships quietly missing a
SUSFS feature. See [`.github/scripts/susfs_patch_surgery.py`](.github/scripts/susfs_patch_surgery.py).

The same sync added `fs/exec.c` calls into KernelSU's preinit helpers, which
BakaSU does not have; the builder defines `KSU_NO_PREINIT` to compile them out
and stops doing so automatically once those symbols appear in the KSU tree.

> ⚠️ BakaSU `main` currently refuses SUSFS builds outright — its
> `kernel/tools/susfs_compat.mk` ends in `$(error Please wait susfs update.)`.
> Until that lands on `main`, dispatch with `KSU_META=sync-susfs/⚡Ultra⚡/`.

---

## ⚙️ Key Options

| Option | Description |
|---|---|
| `DEVICE` | Device to build, or `all` |
| `GKI_RELEASE` | `auto` = the device default above, or pin any release from [Selectable GKI releases](#selectable-gki-releases) |
| `KSU_META` | BakaSU source: `branch/tag/commit` |
| `SUSFS_META` | Empty = latest, `-1` = disabled, hash = pinned |
| `SUFFIX` | Kernel local version tail. **Empty = the stock suffix for the selected GKI release**, `-1` = disabled, or set your own |
| `SUBLEVEL` | Override the kernel SUBLEVEL |
| `LSM` | Enable Baseband Guard |
| `NETFILTER` | Enable Netfilter/IPSet |
| `BBR_ECN` | Enable BBR + ECN |
| `BBR3` | Backport BBRv3 (patches `net/tcp`, adds `CONFIG_TCP_CONG_BBR3`) |
| `ADIOS` | Add the ADIOS block MQ I/O scheduler and make it the default |
| `SULTAN_TWEAKS` | Apply Sultan-derived power/memory patches from WildKernels (dry-run checked, off by default) |
| `CREATE_RELEASE` | Publish ZIP to GitHub Releases |

### Kernel suffix

Left empty, `SUFFIX` resolves to the stock OnePlus tail for the selected release,
so `uname -r` matches what the device shipped with:

| GKI release | Resulting `uname -r` |
|---|---|
| `android16-6.12-2025-06` | `6.12.23-android16-5-gb2a876903b49-ab14541642-4k` |
| `android16-6.12-2025-09` | `6.12.38-android16-5-g844001fb8721-ab14552068-4k` |
| `android16-6.12-2025-12` | `6.12.58-android16-6-g925a103d123c-ab15898589-4k` |

Those three strings are OnePlus OEM build tails, so they only exist for releases
an OTA has shipped. For any other release the suffix is synthesized instead:
`<KMI generation>-g<kernel/common commit>-ab<id derived from that commit>-4k`,
e.g. `6.12.92-android16-6-g<sha12>-ab<id>-4k`. It carries the correct KMI
generation and the real upstream commit, and is stable across rebuilds of the
same branch head, but it is not a string any device ever shipped.

---

## 📦 Output

Naming: `AK3_BakaSU_<ksuver>_<SUSFS-ver|noSUSFS>_<device>_<kernel>[_LSM].zip`

Example ZIP:
`AK3_BakaSU_43000_SUSFS-v2.3.0_OnePlus15-15T_6.12.23.zip`

With LSM:
`AK3_BakaSU_43000_SUSFS-v2.3.0_OnePlus15-15T_6.12.23_LSM.zip`

SUSFS disabled:
`AK3_BakaSU_43000_noSUSFS_OnePlus15-15T_6.12.23.zip`

> Building `DEVICE=all` compiles each **unique** kernel once — one per GKI
> release rather than one per device — so you get three ZIPs:
>
> - `…_OnePlus15-15T_6.12.23.zip`
> - `…_OnePlus15R-Ace6T_6.12.38.zip`
> - `…_OnePlus15-15T-15R-Ace6T-Pad3Pro-Pad4_6.12.58.zip`
>
> The kernel version is part of the name, so the 6.12.23 and 6.12.58 builds for
> the same device never overwrite each other.

---

## ⚠️ Notice

Use at your own risk. Keep a backup boot image and make sure fastboot/recovery access is available.

---

## 🙏 Credits

Thanks to the maintainers of Android GKI, BakaSU, SUSFS, AnyKernel3, Baseband Guard, and related community patches.
