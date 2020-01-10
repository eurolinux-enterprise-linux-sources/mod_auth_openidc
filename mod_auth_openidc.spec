%{!?_httpd_mmn: %{expand: %%global _httpd_mmn %%(cat %{_includedir}/httpd/.mmn || echo 0-0)}}
%{!?_httpd_moddir: %{expand: %%global _httpd_moddir %%{_libdir}/httpd/modules}}
%{!?_httpd_confdir: %{expand: %%global _httpd_confdir %{_sysconfdir}/httpd/conf.d}}

# Optionally build with hiredis if --with hiredis is passed
%{!?_with_hiredis: %{!?_without_hiredis: %global _without_hiredis --without-hiredis}}
# It is an error if both or neither required options exist.
%{?_with_hiredis: %{?_without_hiredis: %{error: both _with_hiredis and _without_hiredis}}}
%{!?_with_hiredis: %{!?_without_hiredis: %{error: neither _with_hiredis nor _without_hiredis}}}

# /etc/httpd/conf.d with httpd < 2.4 and defined as /etc/httpd/conf.modules.d with httpd >= 2.4
%{!?_httpd_modconfdir: %{expand: %%global _httpd_modconfdir %%{_sysconfdir}/httpd/conf.d}}

%global httpd_pkg_cache_dir /var/cache/httpd/mod_auth_openidc

Name:		mod_auth_openidc
Version:	1.8.8
Release:	5%{?dist}
Summary:	OpenID Connect auth module for Apache HTTP Server

Group:		System Environment/Daemons
License:	ASL 2.0
URL:		https://github.com/pingidentity/mod_auth_openidc
Source0:	https://github.com/pingidentity/mod_auth_openidc/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

Patch0: decrypt_aesgcm.patch
Patch1: 0001-don-t-echo-query-params-on-invalid-requests-to-redir.patch
Patch2: 0002-Backport-security-fix-scrub-headers-on-OIDCUnAuthAct.patch
Patch3: 0003-Backport-security-fix-scrub-headers-for-AuthType-oau.patch

BuildRequires:	httpd-devel
BuildRequires:	openssl-devel
BuildRequires:	curl-devel
BuildRequires:	jansson-devel
BuildRequires:	pcre-devel
BuildRequires:	autoconf
BuildRequires:	automake
%{?_with_hiresdis:BuildRequires: hiresdis-devel}
Requires:	httpd-mmn = %{_httpd_mmn}

%description
This module enables an Apache 2.x web server to operate as
an OpenID Connect Relying Party and/or OAuth 2.0 Resource Server.

%prep
%setup -q
%patch0 -p1 -b decrypt_aesgcm
%patch1 -p1 -b echo_req
%patch2 -p1 -b scrub_headers
%patch3 -p1 -b scrub_headers_oauth

%build
# workaround rpm-buildroot-usage
export MODULES_DIR=%{_httpd_moddir}
export APXS2_OPTS='-S LIBEXECDIR=${MODULES_DIR}'
autoreconf
%configure \
  %{?_with_hiredis} \
  %{?_without_hiredis}

make %{?_smp_mflags}

%check
export MODULES_DIR=%{_httpd_moddir}
make %{?_smp_mflags} test

%install
mkdir -p $RPM_BUILD_ROOT%{_httpd_moddir}
make install MODULES_DIR=$RPM_BUILD_ROOT%{_httpd_moddir}

install -m 755 -d $RPM_BUILD_ROOT%{_httpd_modconfdir}
echo 'LoadModule auth_openidc_module modules/mod_auth_openidc.so' > \
	$RPM_BUILD_ROOT%{_httpd_modconfdir}/10-auth_openidc.conf

install -m 755 -d $RPM_BUILD_ROOT%{_httpd_confdir}
install -m 644 auth_openidc.conf $RPM_BUILD_ROOT%{_httpd_confdir}
# Adjust httpd cache location in install config file
sed -i 's!/var/cache/apache2/!/var/cache/httpd/!' $RPM_BUILD_ROOT%{_httpd_confdir}/auth_openidc.conf
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}/metadata
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}/cache


%files
%if 0%{?rhel} && 0%{?rhel} < 7
%doc LICENSE.txt
%else
%license LICENSE.txt
%endif
%doc ChangeLog
%doc AUTHORS
%doc DISCLAIMER
%doc README.md
%{_httpd_moddir}/mod_auth_openidc.so
%config(noreplace) %{_httpd_modconfdir}/10-auth_openidc.conf
%config(noreplace) %{_httpd_confdir}/auth_openidc.conf
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}/metadata
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}/cache

%changelog
* Tue Jan 29 2019 Jakub Hrozek <jhrozek@redhat.com> - 1.8.8-5
- Resolves: rhbz#1626297 - CVE-2017-6413 mod_auth_openidc: OIDC_CLAIM and
                           OIDCAuthNHeader not skipped in an "AuthType oauth20"
                           configuration [rhel-7]

* Tue Jan 29 2019 Jakub Hrozek <jhrozek@redhat.com> - 1.8.8-4
- Resolves: rhbz#1626299 - CVE-2017-6059 mod_auth_openidc: Shows
                           user-supplied content on error pages [rhel-7]

* Thu Mar 31 2016 John Dennis <jdennis@redhat.com> - 1.8.8-3
- fix unit test failure caused by apr_jwe_decrypt_content_aesgcm()
  failing to null terminate decrypted string
  Resolves: bug#1292561 New package: mod_auth_openidc

* Tue Mar 29 2016 John Dennis <jdennis@redhat.com> - 1.8.8-2
- Add %check to run test
  Resolves: bug#1292561 New package: mod_auth_openidc

* Tue Mar 29 2016 John Dennis <jdennis@redhat.com> - 1.8.8-1
- Initial import
  Resolves: bug#1292561 New package: mod_auth_openidc

