%global _hardened_build 1
%global alphatag 4f463d7

Name:           knot-resolver
Version:        1.0.0
Release:        0.3.%{alphatag}%{?dist}
Summary:        Caching full DNS Resolver

License:        GPLv3
URL:            https://www.knot-resolver.cz/
# No tarballs have been published by the upstream yet.
# $ git clone https://gitlab.labs.nic.cz/knot/resolver.git knot-resolver
# $ cd knot-resolver
# $ git archive --format tar --prefix knot-resolver-1.0.0-alphatag/ alphatag | xz > knot-resolver-1.0.0-alphatag.tar.xz
Source0:        knot-resolver-%{version}-%{alphatag}.tar.xz
Source1:        kresd.service
Source2:        config
Source3:        root.keys

BuildRequires:  pkgconfig(libknot) >= 2.1
BuildRequires:  pkgconfig(libzscanner)
BuildRequires:  pkgconfig(libdnssec)
BuildRequires:  pkgconfig(libuv) >= 1.0
BuildRequires:  pkgconfig(luajit)

BuildRequires:  pkgconfig(libmemcached) >= 1.0
BuildRequires:  pkgconfig(hiredis)

BuildRequires:  pkgconfig(cmocka)
BuildRequires:  pkgconfig(socket_wrapper)

BuildRequires:  systemd
# FIXME: documentation fails to build on Fedora 23
#BuildRequires: doxygen
#BuildRequires: breathe
#BuildRequires: python-sphinx
#BuildRequires: python-sphinx_rtd_theme

Requires(pre): shadow-utils
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
The Knot DNS Resolver is a caching full resolver implementation written in C
and LuaJIT, including both a resolver library and a daemon. Modular
architecture of the library keeps the core tiny and efficient, and provides
a state-machine like API for extensions.

%package devel
Summary:        Development headers for Knot DNS Resolver
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
The package contains development headers for Knot DNS Resolver.

%prep
%setup -q -n %{name}-%{version}-%{alphatag}
rm -v scripts/bootstrap-depends.sh

%build
%global build_paths PREFIX=%{_prefix} BINDIR=%{_bindir} LIBDIR=%{_libdir} INCLUDEDIR=%{_includedir} ETCDIR=%{_sysconfdir}/kresd
%global build_flags V=1 CFLAGS="%{optflags}" LDFLAGS="%{__global_ldflags}" %{build_paths} HAS_go=no

make %{?_smp_mflags} %{build_flags}

%install
%make_install %{build_flags}

# move sample configuration files to documentation
install -m 0755 -d %{buildroot}%{_pkgdocdir}
mv %{buildroot}%{_sysconfdir}/kresd/config.* %{buildroot}%{_pkgdocdir}
chmod 0644 %{buildroot}%{_pkgdocdir}/config.*

# install service
mkdir -p %{buildroot}%{_unitdir}
install -m 0644 -p %SOURCE1 %{buildroot}%{_unitdir}/kresd.service

# install configuration file
install -m 0644 -p %SOURCE2 %{buildroot}%{_sysconfdir}/kresd/config

# remove ICANN key
rm %{buildroot}%{_sysconfdir}/kresd/icann-ca.pem

# create working directory
install -m 0755 -d %{buildroot}%{_sharedstatedir}/kresd
install -m 0644 -p %SOURCE3 %{buildroot}%{_sharedstatedir}/kresd/root.keys

%check
LD_PRELOAD=lib/libkres.so make check %{build_flags} LDFLAGS="%{__global_ldflags} -ldl"

%pre
getent group kresd >/dev/null || groupadd -r kresd
getent passwd kresd >/dev/null || useradd -r -g kresd -d %{_sysconfdir}/kresd -s /sbin/nologin -c "Knot DNS Resolver" kresd
exit 0

%post
%systemd_post kresd.service
/sbin/ldconfig

%preun
%systemd_preun kresd.service

%postun
%systemd_postun_with_restart kresd.service
/sbin/ldconfig

%files
%license COPYING
%doc %{_pkgdocdir}
%attr(755,root,kresd) %dir %{_sysconfdir}/kresd
%attr(644,root,kresd) %config(noreplace) %{_sysconfdir}/kresd/config
%{_unitdir}/kresd.service
%{_bindir}/kresd
%{_libdir}/libkres.so.*
%{_libdir}/kdns_modules
%attr(755,kresd,kresd) %dir %{_sharedstatedir}/kresd
%attr(644,kresd,kresd) %config(noreplace) %{_sharedstatedir}/kresd/root.keys
%{_mandir}/man8/kresd.*

%files devel
%{_includedir}/libkres
%{_libdir}/pkgconfig/libkres.pc
%{_libdir}/libkres.so

%changelog
* Thu May 05 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 1.0.0-0.3.4f463d7
- update to latest git version
- re-enable unit-test

* Sat Apr 09 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 1.0.0-0.2.79a8440
- update to latest git version
- fix package review issues

* Tue Feb 02 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 1.0.0-0.1.beta3
- initial package
