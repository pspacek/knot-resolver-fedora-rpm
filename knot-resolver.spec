%global _hardened_build 1

Name:           knot-resolver
Version:        1.1.1
Release:        3%{?dist}
Summary:        Caching full DNS Resolver

License:        GPLv3
URL:            https://www.knot-resolver.cz/
Source0:	https://secure.nic.cz/files/%{name}/%{name}-%{version}.tar.xz

# LuaJIT only on these arches
ExclusiveArch: %{arm} aarch64 %{ix86} x86_64

Source1:        config
Source2:        root.keys

Source100:	kresd.service
Source101:	kresd.socket
Source102:	kresd-control.socket
Source103:	kresd-tls.socket
Source104:	kresd.tmpfiles

BuildRequires:  pkgconfig(libknot) >= 2.3
BuildRequires:  pkgconfig(libzscanner)
BuildRequires:  pkgconfig(libdnssec)
BuildRequires:  pkgconfig(libuv)
BuildRequires:  pkgconfig(luajit) >= 2.0

BuildRequires:  pkgconfig(libmemcached) >= 1.0
BuildRequires:  pkgconfig(hiredis)
BuildRequires:  pkgconfig(libsystemd)

BuildRequires:  pkgconfig(cmocka)
BuildRequires:  pkgconfig(socket_wrapper)

BuildRequires:  systemd
# FIXME: documentation fails to build on Fedora 23
#BuildRequires: doxygen
#BuildRequires: breathe
#BuildRequires: python-sphinx
#BuildRequires: python-sphinx_rtd_theme

Requires:       lua-socket
Requires:       lua-sec

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
%autosetup
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
rm -vr %{buildroot}%{_sysconfdir}/kresd

# install configuration files
mkdir -p %{buildroot}%{_sysconfdir}
install -m 0755 -d %{buildroot}%{_sysconfdir}/kresd
install -m 0644 -p %SOURCE1 %{buildroot}%{_sysconfdir}/kresd/config
install -m 0644 -p %SOURCE2 %{buildroot}%{_sysconfdir}/kresd/root.keys

# install systemd units
mkdir -p %{buildroot}%{_unitdir}
install -m 0644 -p %SOURCE100 %{buildroot}%{_unitdir}/kresd.service
install -m 0644 -p %SOURCE101 %{buildroot}%{_unitdir}/kresd.socket
install -m 0644 -p %SOURCE102 %{buildroot}%{_unitdir}/kresd-control.socket
install -m 0644 -p %SOURCE103 %{buildroot}%{_unitdir}/kresd-tls.socket

# install tmpfiles.d
mkdir -p %{buildroot}%{_tmpfilesdir}
install -m 0644 -p %SOURCE104 %{buildroot}%{_tmpfilesdir}/kresd.conf
mkdir -p %{buildroot}%{_rundir}
install -m 0750 -d %{buildroot}%{_rundir}/kresd

# remove module with unsatisfied dependencies
rm -r %{buildroot}%{_libdir}/kdns_modules/{http,http.lua}

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
%attr(644,root,kresd) %config(noreplace) %{_sysconfdir}/kresd/root.keys
%attr(750,kresd,kresd) %dir %{_rundir}/kresd
%{_unitdir}/kresd.service
%{_unitdir}/kresd*.socket
%{_tmpfilesdir}/kresd.conf
%{_sbindir}/kresd
%{_libdir}/libkres.so.*
%{_libdir}/kdns_modules
%{_mandir}/man8/kresd.*

%files devel
%{_includedir}/libkres
%{_libdir}/pkgconfig/libkres.pc
%{_libdir}/libkres.so

%changelog
* Sat Nov 19 2016 Peter Robinson <pbrobinson@fedoraproject.org> 1.1.1-3
- Add ExclusiveArch for architectures with LuaJIT

* Mon Aug 29 2016 Igor Gnatenko <ignatenko@redhat.com> - 1.1.1-2
- Rebuild for LuaJIT 2.1.0

* Wed Aug 24 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 1.1.1-1
- new upstream release:
  + fix name server fallback in case some of the servers are unreachable

* Fri Aug 12 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 1.1.0-1
- new upstream release:
  + RFC7873 DNS Cookies
  + RFC7858 DNS over TLS
  + Metrics exported in Prometheus
  + DNS firewall module
  + Explicit CNAME target fetching in strict mode
  + Query minimisation improvements 
  + Improved integration with systemd

* Tue May 31 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 1.0.0-1
- final release

* Thu May 05 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 1.0.0-0.3.4f463d7
- update to latest git version
- re-enable unit-test

* Sat Apr 09 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 1.0.0-0.2.79a8440
- update to latest git version
- fix package review issues

* Tue Feb 02 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 1.0.0-0.1.beta3
- initial package
