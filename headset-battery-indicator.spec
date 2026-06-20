Name:           headset-battery-indicator
Version:        2.3.1
Release:        1%{?dist}
Summary:        System tray application for monitoring USB headsets via HeadsetControl

License:        GPL-3.0-or-later
URL:            https://github.com/ruflas/headset-battery-indicator
Source0:        https://github.com/ruflas/headset-battery-indicator/archive/refs/tags/v%{version}.tar.gz

BuildArch:      noarch

Obsoletes:      python-headset-battery-indicator < 2.3.0
Provides:       python-headset-battery-indicator = %{version}

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  desktop-file-utils

Requires:       headsetcontrol
Requires:       python3-pyside6
Requires:       xdg-utils
Requires(post): desktop-file-utils
Requires(postun): desktop-file-utils
Requires(post): hicolor-icon-theme
Requires(postun): hicolor-icon-theme

%description
Headset Battery Indicator is a Python/Qt system tray application for monitoring
and controlling USB headsets using the HeadsetControl backend. It allows battery
monitoring, ChatMix adjustment, Sidetone control, and Auto-Off timing directly
from the tray icon.

%generate_buildrequires
%pyproject_buildrequires

%prep
%autosetup -n headset-battery-indicator-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files headset_battery_indicator

install -Dm0644 headset-battery-indicator.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/headset-battery-indicator.png

desktop-file-install \
    --dir=%{buildroot}%{_datadir}/applications \
    headset-battery-indicator.desktop

%post
update-desktop-database &> /dev/null || :
touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :

%postun
update-desktop-database &> /dev/null || :
gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :

%files -f %{pyproject_files}
%license LICENSE
%doc README.md
%{_bindir}/headset-battery-indicator
%{_datadir}/icons/hicolor/512x512/apps/headset-battery-indicator.png
%{_datadir}/applications/headset-battery-indicator.desktop

%changelog
* Sat Jun 20 2026 Ruflas <ruflas@ruflas.dev> - 2.3.1-1
- Fix delayed battery icon update on startup caused by startup commands blocking the GUI thread

* Mon Jun 15 2026 Ruflas <ruflas@ruflas.dev> - 2.3.0-1
- Fix Spanish language name capitalization in the language picker
- Store settings and logs next to the executable for portable mode

* Thu May 28 2026 Ruflas <ruflas@ruflas.dev> - 2.2.2-1
- Add version menu item in tray that opens the GitHub releases page on click
- Fix Windows EXE taskbar/window icon (now uses headset-battery-indicator.png via Pillow ICO conversion in CI)

* Wed May 21 2026 Ruflas <ruflas@ruflas.dev> - 2.2.1-1
- Add internationalization (i18n) with Spanish translation
- Add language selector in Preferences dialog
- Add disconnected icon style preference (empty/error/hide)
- Fix QTranslator locale fallback (es_ES -> es)
- Rename package back to headset-battery-indicator, add Obsoletes

* Sun May 04 2026 Ruflas <ruflas@ruflas.dev> - 2.2.0-1
- Bump to v2.2.0: Preferences Overhaul & Architecture Refactor
- Migrate to modern pyproject RPM macros (pyproject_wheel, pyproject_install)
- Add %generate_buildrequires with %pyproject_buildrequires
- Fix Requires: python3-pyside6 (correct Fedora package name)
- Add desktop-file-install for proper .desktop validation
- Add .desktop file to source repo

* Thu Oct 30 2025 Ruflas <ruflas@ruflas.dev> - 1.3.0-1
- Initial Fedora RPM packaging for Headset Battery Indicator
