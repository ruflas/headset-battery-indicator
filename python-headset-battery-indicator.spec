# --------------------------------------------------------------------------------------
# Section 1: Metadata (Global Information)
# --------------------------------------------------------------------------------------
Name:           python-headset-battery-indicator
Version:        1.3.0
Release:        1%{?dist}
Summary:        System tray application for controlling USB headsets (HeadsetControl GUI).

# Source URL points to the GitHub Release tarball
Source0:        https://github.com/ruflas/headset-battery-indicator/archive/refs/tags/v%{version}.tar.gz

License:        GPLv3+
URL:            https://github.com/ruflas/headset-battery-indicator
BuildArch:      noarch

# Build Dependencies (minimal for Python projects)
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

# Runtime Requirements
Requires:       headsetcontrol                  # The C/C++ backend binary
Requires:       python3-PySide6                 # The Qt GUI library
Requires:       xdg-utils                       # For opening the file explorer (xdg-open)

%description
Headset Battery Indicator is a Python/Qt application providing a clean system
tray interface for managing USB headset features, including battery level,
[cite_start]ChatMix, Sidetone, and Auto-Off time[cite: 3]. It acts as a graphical frontend 
[cite_start]for the already installed 'headsetcontrol' binary[cite: 4].


# --------------------------------------------------------------------------------------
# Section 2: Preparation, Build, and Installation Instructions
# --------------------------------------------------------------------------------------

%prep
# Prepares the source code (unpacks the tarball)
%autosetup -n %{name}-%{version}

%build
# Prepares the Python environment (no native C/C++ compilation)
%py3_build

%install
# Installs Python application files to the build root
%py3_install

# Fix the shebang (#!) line for executables installed into %{_bindir}
%py3_shebang_fix %{buildroot}%{_bindir}/headset-battery-indicator

# Install the .desktop file for the application launcher
install -Dm 0644 %{_sourcedir}/headset-battery-indicator.desktop %{buildroot}%{_datadir}/applications/headset-battery-indicator.desktop

# Install the icon (assuming 512x512 resolution)
install -Dm 0644 %{_sourcedir}/headset-battery-indicator.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/headset-battery-indicator.png


# --------------------------------------------------------------------------------------
# Section 3: Files and Changelog
# --------------------------------------------------------------------------------------

%files
# Ensure permissions are set correctly for the entire site-packages directory
%license LICENSE
%doc README.md

# 1. Python Application Files
%{python3_sitelib}/headset_battery_indicator/
%{python3_sitelib}/%{name}-%{version}.dist-info/

# 2. The Launcher Script (created via setuptools)
%{_bindir}/headset-battery-indicator

# 3. Resources (Desktop Entry and Icon)
%{_datadir}/applications/headset-battery-indicator.desktop
%{_datadir}/icons/hicolor/512x512/apps/headset-battery-indicator.png

%changelog
* Tue Oct 28 2025 Ruflas <ruflas@ruflas.dev> - 1.3.0-1
- [cite_start]Implement robust binary search logic for headsetcontrol[cite: 7].
- Add system logging and enhanced debug tools.
- [cite_start]Fix Python version conflicts for AppImage compilation[cite: 8].
- Initial Fedora RPM packaging.