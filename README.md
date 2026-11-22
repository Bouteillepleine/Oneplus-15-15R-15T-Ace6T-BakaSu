# 🚀 OnePlus BakaSU Kernel Builder

GitHub Actions workflow that builds flashable **BakaSU GKI kernels** for OnePlus devices:
syncs AOSP GKI, adds BakaSU, optionally applies SUSFS, packages an **AnyKernel3 ZIP**.

> **BakaSU** is the project previously published as **ReSukiSU** (`Baka-SU/BakaSU`).
> Output ZIPs are named `AK3_BakaSU_…`.

---

## 📱 Devices and GKI releases

`DEVICE` accepts `oneplus15`, `oneplus15t`, `oneplus15r`, `ace6t`, `pad3pro`, `pad4`, or `all`.

The build produces a generic GKI `kernel_aarch64` Image, so the Image depends only on the
**GKI release** and the **suffix**. Every device on the same release gets a byte-identical
Image; only the ZIP name differs.

| `GKI_RELEASE` | Kernel | KMI | Default for | Flashable on |
|---|---|---|---|---|
| `android16-6.12-2025-06` | 6.12.23 | 5 | 15, 15T | 15, 15T |
| `android16-6.12-2025-09` | 6.12.38 | 5 | 15R, Ace 6T | 15R, Ace 6T |
| `android16-6.12-2025-12` | 6.12.58 | 6 | Pad 3 Pro, Pad 4 | all six (Sept-2026 OTA) |
| `android16-6.12-2026-03` | 6.12.69 | 6 | | all six, no OnePlus OTA yet |
| `android16-6.12-2026-06` | 6.12.81 | 6 | | all six, no OnePlus OTA yet |
| `android16-6.12-2026-09` | 6.12.92 | 6 | | all six, no OnePlus OTA yet |

> ⚠️ **Match the KMI generation to your firmware.** A KMI-6 kernel (6.12.58 and newer) will
> not load the KMI-5 `vendor_dlkm` modules shipped on 6.12.23 or 6.12.38, and vice versa.

`DEVICE=all` builds one kernel per release, not one per device. `GKI_TAG` pins
`kernel/common` to an exact AOSP tag (`r54`, or a full `android16-6.12-2026-03_r54`) and
fails if it does not resolve. `2025-07` and `2025-08` are not offered: Google deleted the
matching `kernel/common` refs.

---

## ✨ Features

BakaSU · **AutoFDO** profile-guided codegen, inherited from the AOSP GKI build · optional
SUSFS · optional Baseband Guard (**broken on 6.12, leave off**) · optional Netfilter and
IPSet · optional BBR + ECN · optional BBRv3 backport (KMI-safe) · `fq`, `fq_codel`, `cake` ·
optional ADIOS block MQ scheduler · optional Sultan power/memory tweaks · optional Unicode
bypass · optional No_5uS · AnyKernel3 ZIP, GitHub Release or artifact, build logs and hashes.

---

<details>
<summary><b>🛡️ Security backports</b> — 17 critical upstream CVE fixes (click to expand)</summary>

<!-- from Bouteillepleine/kernel_patches common/cve/6.12 + the rtmutex fix; regenerate when the series changes -->

Bugs exploited in the wild, app-reachable use-after-frees (binder, futex, af_unix, epoll, timers,
pipe, memfd), remote TCP and IP-fragment bugs, and an exFAT bug reachable from a plugged-in drive.
Each GKI release applies only the fixes its branch still lacks; the build summary lists the result
per CVE.

| CVE | Fix |
|---|---|
| [CVE-2026-31554](https://nvd.nist.gov/vuln/detail/CVE-2026-31554) | futex: Require sys_futex_requeue() to have identical flags |
| [CVE-2026-43074](https://nvd.nist.gov/vuln/detail/CVE-2026-43074) | eventpoll: defer struct eventpoll free to RCU grace period |
| [CVE-2026-43499](https://nvd.nist.gov/vuln/detail/CVE-2026-43499) | rtmutex: Use waiter::task instead of current in remove_waiter() |
| [CVE-2026-53361](https://nvd.nist.gov/vuln/detail/CVE-2026-53361) | af_unix: Set gc_in_progress to true in unix_gc(). |
| [CVE-2026-63808](https://nvd.nist.gov/vuln/detail/CVE-2026-63808) | exfat: fix potential use-after-free in exfat_find_dir_entry() |
| [CVE-2026-63952](https://nvd.nist.gov/vuln/detail/CVE-2026-63952) | memfd: deny writeable mappings when implying SEAL_WRITE |
| [CVE-2026-64109](https://nvd.nist.gov/vuln/detail/CVE-2026-64109) | af_unix: Fix UAF read of tail->len in unix_stream_data_wait() |
| [CVE-2026-64468](https://nvd.nist.gov/vuln/detail/CVE-2026-64468) | binder: fix UAF in binder_free_transaction() |
| [CVE-2026-64469](https://nvd.nist.gov/vuln/detail/CVE-2026-64469) | binder: fix UAF in binder_thread_release() |
| [CVE-2026-64560](https://nvd.nist.gov/vuln/detail/CVE-2026-64560) | posix-cpu-timers: Prevent UAF caused by non-leader exec() race |
| [CVE-2026-74662](https://nvd.nist.gov/vuln/detail/CVE-2026-74662) | inet: frags: publish queues before arming timer |
| [CVE-2026-80521](https://nvd.nist.gov/vuln/detail/CVE-2026-80521) | af_unix: Unlink scc_entry in unix_del_edge(). |
| [CVE-2026-90003](https://nvd.nist.gov/vuln/detail/CVE-2026-90003) | futex: Prevent rcuwait use-after-free during requeue PI |
| [CVE-2026-98260](https://nvd.nist.gov/vuln/detail/CVE-2026-98260) | exec: Cleanup POSIX timers right after de_thread() |
| [CVE-2026-98374](https://nvd.nist.gov/vuln/detail/CVE-2026-98374) | tcp: fix use-after-free of retransmit_skb_hint in tcp_send_synack() |
| [CVE-2026-98432](https://nvd.nist.gov/vuln/detail/CVE-2026-98432) | ipv4: free inet_opt and ireq_opt after an RCU grace period |
| [CVE-2026-99203](https://nvd.nist.gov/vuln/detail/CVE-2026-99203) | pipe: preserve existing fasync readers on writer setup failure |

</details>

## 🚀 Usage

Fork the repo, open **Actions**, run the workflow, pick a device and options, download the ZIP.

| Option | Description |
|---|---|
| `DEVICE` | Device to build, or `all` |
| `GKI_RELEASE` | `auto` = the device default above, or pin any release from the table |
| `GKI_TAG` | Empty = branch head, `rNN` = that tag of the selected release, or a full tag |
| `KSU_META` | BakaSU source: `branch/CustomTag/CommitHash` |
| `SUSFS_META` | Empty = latest, `-1` = disabled, hash = pinned |
| `SUSFS_DEV` | Build against the SUSFS dev branch |
| `SUFFIX` | Kernel local version tail. Empty = stock suffix, `-1` = disabled, or your own |
| `SUBLEVEL` | Override the kernel SUBLEVEL |
| `BUILD_TIME` | Kernel build timestamp. `F` = current UTC time, or a custom string |
| `LSM` | Enable Baseband Guard |
| `NETFILTER` | Enable Netfilter/IPSet |
| `BBR_ECN` | Enable BBR + ECN |
| `BBR3` | Backport BBRv3 (patches `net/tcp`, adds `CONFIG_TCP_CONG_BBR3`) |
| `ADIOS` | Add the ADIOS block MQ I/O scheduler and make it the default |
| `SULTAN_TWEAKS` | Sultan-derived power/memory patches from WildKernels |
| `UNICODE_BYPASS` | Apply the Unicode invisible-codepoint bypass patch |
| `XUS_FIX` | Apply the No_5uS patch |
| `KSU_SETUP_BRANCH` | BakaSU `setup.sh` branch |
| `CREATE_RELEASE` | Publish ZIP to GitHub Releases |
| `SPACE_NOCLEAN` | Skip the disk-space cleanup |

---

## 🔖 Suffix and output

Left empty, `SUFFIX` resolves to the stock OnePlus tail so `uname -r` matches shipped
firmware, which exists only for the three releases an OTA has shipped (6.12.23, 6.12.38,
6.12.58). Any other release gets a synthesized tail,
`<KMI>-g<kernel/common commit>-ab<id>-4k`: correct KMI generation, real upstream commit,
stable across rebuilds, but not a string any device ever shipped.

ZIP name: `AK3_BakaSU_<ksuver>_<SUSFS-ver|noSUSFS>_<devices>_<kernel>[_LSM].zip`, for example
`AK3_BakaSU_43000_SUSFS-v2.3.0_OnePlus15-15T_6.12.23.zip`. The kernel version is part of the
name, so builds for different releases never overwrite each other.

---

## 🔒 SUSFS

susfs4ksu rebases its kernel-side patch onto one GKI sublevel at a time, so upstream only
ever matches a single release. The builder reconciles it: rejected hunks are dropped and
their code re-inserted on anchors that exist on every release, matched by content rather
than `@@` line numbers. A reject with no known re-insertion is a hard failure, so a kernel
never ships quietly missing a SUSFS feature. See
[`susfs_patch_surgery.py`](.github/scripts/susfs_patch_surgery.py).

It also defines `KSU_NO_PREINIT` to compile out the KernelSU preinit calls BakaSU lacks, and
fails fast with a readable message if the chosen `KSU_META` branch still carries
`susfs_compat.mk`'s `$(error Please wait susfs update.)`.

---

## ⚠️ Notice

Use at your own risk. Keep a backup boot image and working fastboot/recovery access.

## 🙏 Credits

Android GKI, BakaSU, SUSFS, AnyKernel3, Baseband Guard, and related community patches.
