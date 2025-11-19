---

layout: home

hero:
  name: "C / C++ toolchains"
  text: "For static builds."
  tagline: "Direct downloads ~50 MB each<br/>Extract into /opt/dyne, works in any distro."
  image:
    src: musl-logo-infinity-optimized.svg
    alt: Hands-on, Dyne.org style
  actions:
    - theme: sponsor
      text: "📥 FREE DOWNLOADS"
      link: 'https://files.dyne.org/musl'

features:
  - title: 👟 Zero dependencies
    details: Produce static ELF binaries that run on any GNU/Linux distribution and are free to be redistributed.

  - title: 🚀 GCC 15.1 / Binutils 2.44
    details: Built with recent GNU tools and musl-libc releases, libreSSL, ZLib-ng, libCURL, etc.

  - title: 🤏 Optimized for size
    details: Stripped and compiled with -Os to fit anywhere and produce the smallest binaries possible.

  - title: 🦾 Latest C++ support
    details: Includes libstdc++ and libatomic to support modern C++17 and C++20 code.


---

<div class="spacer"></div>

<!--@include:readme.md-->

<!--
<p>&nbsp;</p>
#### One liner root install
```bash
curl -sL dyne.org/musl/install.sh | bash -
```
#### Wizard setup (interactive)
```bash
curl -sL dyne.org/musl/wizard.sh && bash wizard.sh
```
-->
