%global __python python2.6
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pyver: %define pyver %(%{__python} -c "import sys ; print sys.version[:3]")}
%define version 0.1
%define unmangled_version 0.1
%define build_rev 0

Name:           python-feat-dev
Summary:        Feat development tools
Version: 	%{version}
Release: 	%{?build_rev}%{?dist}
Source0: 	feat-dev-%{unmangled_version}.tar.gz

Group:          Development/Languages
License:        Propietary
URL:            http://flumotion.com

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  python-devel
BuildRequires:  python-setuptools >= 0.6c9
Requires:	python-simplejson
Requires:	python-twisted-core
Requires:	python-twisted-web
Requires:	python-feat
Requires:	python-pydot
Requires:	pygtksourceview2
Provides:	%{name}

%description
Flumotion Asynchronous Autonomous Agent Toolkit

%prep
%setup -q -n feat-dev-%{unmangled_version}

%build
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --skip-build --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
%{__mv} $RPM_BUILD_ROOT/%_usr/bin/run.py $RPM_BUILD_ROOT/%_usr/bin/feattool

install -m 644 src/feattool/data/ui/*.ui \
     $RPM_BUILD_ROOT%{python_sitelib}/feattool/data/ui

%files
%defattr(-,root,root,-)
%{python_sitelib}/*
%_usr/bin/*

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Aug 11 2011 Marek Kowalski <mkowalski@flumotion.com>
- 0.1
- Initial version of spec.
