%define debug_package %{nil}

%define mybuildnumber %{?build_number}%{?!build_number:1}

Name:           git-remote-qubes
Version:        0.0.4
Release:        %{mybuildnumber}%{?dist}
Summary:        Inter-VM git push and pull for Qubes OS AppVMs and StandaloneVMs
BuildArch:      noarch

License:        GPLv3+
URL:            https://github.com/Rudd-O/git-remote-qubes
Source0:        https://github.com/Rudd-O/%{name}/archive/{%version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  make
BuildRequires:  sed
BuildRequires:  python2

Requires:       python2
Requires:       git-core
# systemd is required because of systemd-escape.
Requires:       systemd

%package dom0
Summary:        Policy package for Qubes OS dom0s that arbitrates %{name}

%description
This package lets you setup Git servers on your Qubes OS VMs.
You are meant to install this package on TemplateVMs that are the templates
for AppVMs where you want to either serve git repos from, or push/pull git
repos from, as well as StandaloneVMs where you wish to do the same things.

%description dom0
This package contains the Qubes OS execution policy for the %{name} package.
You are meant to install this package on the dom0 of the machine where you
have VMs that have the %{name} package installed.

%prep
%setup -q

%build
# variables must be kept in sync with install
make DESTDIR=$RPM_BUILD_ROOT BINDIR=%{_bindir} SYSCONFDIR=%{_sysconfdir} SITELIBDIR=%{python_sitelib} LIBEXECDIR=%{_libexecdir}

%install
rm -rf $RPM_BUILD_ROOT
# variables must be kept in sync with build
for target in install-vm install-dom0; do
    make $target DESTDIR=$RPM_BUILD_ROOT BINDIR=%{_bindir} SYSCONFDIR=%{_sysconfdir} SITELIBDIR=%{python_sitelib} LIBEXECDIR=%{_libexecdir}
done

%check
if grep -r '@.*@' $RPM_BUILD_ROOT ; then
    echo "Check failed: files with AT identifiers appeared" >&2
    exit 1
fi

%files
%attr(0755, root, root) %{_libexecdir}/git-local-qubes
%attr(0755, root, root) %{_libexecdir}/git-core/git-remote-qubes
%attr(0644, root, root) %{python_sitelib}/gitremotequbes/*.py
%attr(0644, root, root) %{python_sitelib}/gitremotequbes/*.pyc
%attr(0644, root, root) %{python_sitelib}/gitremotequbes/*.pyo
%attr(0755, root, root) %{_sysconfdir}/qubes-rpc/ruddo.Git.Receive
%attr(0755, root, root) %{_sysconfdir}/qubes-rpc/ruddo.Git.Upload
%doc README.md

%files dom0
%config(noreplace) %attr(0655, root, root) %{_sysconfdir}/qubes-rpc/policy/ruddo.Git.Receive
%config(noreplace) %attr(0655, root, root) %{_sysconfdir}/qubes-rpc/policy/ruddo.Git.Upload
%doc README.md

%changelog
* Wed Feb 01 2017 Bahtiar Gadimov (kalkin-) <bahtiar@gadimov.de>
- Add caching support

* Mon Oct 24 2016 Manuel Amador (Rudd-O) <rudd-o@rudd-o.com>
- Initial release.
