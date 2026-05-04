Name:           python-headset-battery-indicator
Version:        2.2.0
Release:        1%{?dist}
Summary:        System tray application for monitoring USB headsets (HeadsetControl GUI)

License:        GPL-3.0-or-later
URL:            https://github.com/ruflas/headset-battery-indicator
Source0:        https://github.com/ruflas/headset-battery-indicator/archive/refs/tags/v%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-build
BuildRequires:  python3-installer
BuildRequires:  python3-wheel

Requires:       headsetcontrol
Requires:       python3-pyside6
Requires:       xdg-utils
Requires(post): desktop-file-utils
Requires(postun): desktop-file-utils
Requires(post): hicolor-icon-theme
Requires(postun): hicolor-icon-theme

%description
Headset Battery Indicator is a Python/Qt system tray application for monitoring and
controlling USB headsets using the HeadsetControl backend. It allows battery monitoring,
ChatMix adjustment, Sidetone control, and Auto-Off timing directly from the tray icon.

%prep
%autosetup -n headset-battery-indicator-%{version}

%build
%py3_build

%install
%py3_install

%py3_shebang_fix %{buildroot}%{_bindir}/headset-battery-indicator

install -Dm0644 headset-battery-indicator.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/headset-battery-indicator.png

%post
update-desktop-database &> /dev/null || :
touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :

%postun
update-desktop-database &> /dev/null || :
gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :

%files
%license LICENSE
%doc README.md
%{python3_sitelib}/headset_battery_indicator/
%{python3_sitelib}/headset_battery_indicator-%{version}.dist-info/
%{_bindir}/headset-battery-indicator
%{_datadir}/icons/hicolor/512x512/apps/headset-battery-indicator.png

%changelog
* Sun May 04 2026 Ruflas <ruflas@ruflas.dev> - 2.2.0-1
- Bump to v2.2.0: Preferences Overhaul & Architecture Refactor
- Fix BuildRequires: add python3-build, python3-installer, python3-wheel
- Fix Requires: python3-pyside6 (lowercase, correct Fedora package name)
- Remove .desktop file install (not present in source)

* Thu Oct 30 2025 Ruflas <ruflas@ruflas.dev> - 1.3.0-1
- Initial Fedora RPM packaging for Headset Battery Indicator
