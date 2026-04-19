Name:           seekr
Version:        1.2
Release:        1%{?dist}
Summary:        AI-powered file search tool

License:        MIT
URL:            https://github.com/yourusername/seekr
Source0:        %{name}-%{version}.tar.gz

# Disable debug package (safe)
%global debug_package %{nil}

BuildRequires:  python3

Requires:       python3
Requires:       python3-gobject
Requires:       gtk4
Requires:       python3-keyring
Requires:       python3-watchdog

%description
Seekr is an AI-powered file search GTK application.

%prep
%autosetup

%build
# nothing to build

%install
# -------------------------------
# Install app to /opt
# -------------------------------
mkdir -p %{buildroot}/opt/seekr
cp -r app %{buildroot}/opt/seekr/
cp -r assets %{buildroot}/opt/seekr/
cp LICENSE %{buildroot}/opt/seekr/
cp README.md %{buildroot}/opt/seekr/

# -------------------------------
# CLI launcher (IMPORTANT)
# -------------------------------
mkdir -p %{buildroot}/usr/bin

cat > %{buildroot}/usr/bin/seekr <<EOF
#!/bin/bash
cd /opt/seekr
export PYTHONPATH=/opt/seekr
exec python3 app/app_entry/main_gtk.py
EOF

chmod +x %{buildroot}/usr/bin/seekr

# -------------------------------
# Desktop entry
# -------------------------------
mkdir -p %{buildroot}/usr/share/applications

cat > %{buildroot}/usr/share/applications/seekr.desktop <<EOF
[Desktop Entry]
Name=Seekr
Comment=AI-Powered File Search
Exec=/usr/bin/seekr
Icon=/opt/seekr/assets/logo.png
Type=Application
Categories=Utility;System;
Terminal=false
StartupNotify=true
EOF

%files
/opt/seekr
/usr/bin/seekr
/usr/share/applications/seekr.desktop

%post
update-desktop-database /usr/share/applications &>/dev/null || :

%changelog
* Wed Apr 15 2026 Anuj
- Final working version with CLI launcher
