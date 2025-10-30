# --------------------------------------------------------------------------------------
# Section 1: Metadata (Global Information)
# --------------------------------------------------------------------------------------
Name:           python-headset-battery-indicator
Version:        1.3.0
Release:        1%{?dist}
Summary:        System tray application for controlling USB headsets (HeadsetControl GUI)

License:        GPLv3+
URL:            https://github.com/ruflas/headset-battery-indicator
Source0:        https://github.com/ruflas/headset-battery-indicator/archive/refs/tags/v%{version}.tar.gz
Source1:        headset-battery-indicator.desktop
Source2:        headset-battery-indicator.png

BuildArch:      noarch

# Build Dependencies (Python project)
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

# Runtime Requirements
Requires:       headsetcontrol                  # The C/C++ backend binary
Requires:       python3-PySide6                 # The Qt GUI library
Requires:       xdg-utils                       # For opening the file explorer (xdg-open)
Requires(post): desktop-file-utils
Requires(postun): desktop-file-utils
Requires(post): hicolor-icon-theme
Requires(postun): hicolor-icon-theme

%description
Headset Battery Indicator is a Python/Qt application providing a clean system
tray interface for managing USB headset features, including battery level,
ChatMix, Sidetone, and Auto-Off time. It acts as a graphical frontend 
for the already installed 'headsetcontrol' binary.

# --------------------------------------------------------------------------------------
# Section 2: Preparation, Build, and Installation Instructions
# --------------------------------------------------------------------------------------

%prep
%autosetup -n headset-battery-indicator-%{version}

%build
%py3_build

%install
%py3_install

# Fix the shebang for executables installed into %{_bindir}
%py3_shebang_fix %{buildroot}%{_bindir}/headset-battery-indicator

# Install the .desktop file for the application launcher
install -Dm 0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/headset-battery-indicator.desktop

# Install the icon (assuming 512x512 resolution)
install -Dm 0644 %{SOURCE2} %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/headset-battery-indicator.png

# --------------------------------------------------------------------------------------
# Section 3: Post-installation Scripts
# --------------------------------------------------------------------------------------

%post
update-desktop-database &> /dev/null || :
touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :

%postun
update-desktop-database &> /dev/null || :
gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :

# --------------------------------------------------------------------------------------
# Section 4: Files and Changelog
# --------------------------------------------------------------------------------------

%files
%license LICENSE
%doc README.md

# 1. Python Application Files
%{python3_sitelib}/headset_battery_indicator/
%{python3_sitelib}/%{name}-%{version}.dist-info/

# 2. The Launcher Script
%{_bindir}/headset-battery-indicator

# 3. Resources (Desktop Entry and Icon)
%{_datadir}/applications/headset-battery-indicator.desktop
%{_datadir}/icons/hicolor/512x512/apps/headset-battery-indicator.png

%changelog
* Tue Oct 28 2025 Ruflas <ruflas@ruflas.dev> - 1.3.0-1
- Implement robust binary search logic for headsetcontrol
- Add system logging and enhanced debug tools
- Fix Python version conflicts for AppImage compilation
- Initial Fedora RPM packaging
