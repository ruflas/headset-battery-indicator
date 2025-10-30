Name:           python-headset-battery-indicator
Version:        1.3.0
Release:        1%{?dist}
Summary:        System tray application for controlling USB headsets (HeadsetControl GUI)

License:        GPL-3.0-or-later
URL:            https://github.com/ruflas/headset-battery-indicator
Source0:        https://github.com/ruflas/headset-battery-indicator/archive/refs/tags/v%{version}.tar.gz
Source1:        headset-battery-indicator.desktop
Source2:        headset-battery-indicator.png

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

Requires:       headsetcontrol
Requires:       python3-PySide6
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

# Fix shebang line in the executable
%py3_shebang_fix %{buildroot}%{_bindir}/headset-battery-indicator

# Install desktop file and icon
install -Dm0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/headset-battery-indicator.desktop
install -Dm0644 %{SOURCE2} %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/headset-battery-indicator.png

# Remove unnecessary compiled files
find %{buildroot} -name '*.pyc' -delete

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
%{_datadir}/applications/headset-battery-indicator.desktop
%{_datadir}/icons/hicolor/512x512/apps/headset-battery-indicator.png

%changelog
* Thu Oct 30 2025 Ruflas <ruflas@ruflas.dev> - 1.3.0-1
- Initial Fedora RPM packaging for Headset Battery Indicator
- Added post-install hooks for desktop integration
- Verified compatibility with Copr
