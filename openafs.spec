# This is the OpenAFS spec file maintained by the CentOS Storage SIG.
# This is just used for building the userspace parts of OpenAFS (the servers,
# the utilities, and parts of the client). This is not used for building the
# client kernel module.

# These two macros are for what version of OpenAFS we're building. afsvers is
# for what openafs.org thinks the version number is, and pkgvers is for what
# RPM thinks the verson is. Usually these are the same, but for prereleases
# and other edge cases they can be different.
%define afsvers 1.6.10
%define pkgvers 1.6.10

# for beta/rc releases make pkgrel 0.<tag>
# for real releases make pkgrel 1 (or more for extra releases)
%define pkgrel 1
%define kmod_name openafs

# Define the location of your init.d directory
%define initdir /etc/rc.d/init.d

# Define the location of the PAM security module directory
%define pamdir /%{_lib}/security

# On Fedora 15 and above, and EL7 and above, use systemd. Otherwise, we use
# our traditional sysv init scripts.
%if 0%{?fedora} >= 15 || 0%{?rhel >= 7}
    %define use_systemd 1
%else
    %define use_systemd 0
%endif

Summary:  OpenAFS distributed filesystem
Name:     openafs
Version:  %{pkgvers}
Release:  %{pkgrel}%{?dist}
License:  IBM Public License
URL:      http://www.openafs.org/
Packager: CentOS Storage SIG <centos-devel@centos.org>
Group:    Applications/System

BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildRequires: %{?kdepend:%{kdepend}, } pam-devel, ncurses-devel, flex, bison
%if %{use_systemd}
BuildRequires: systemd-units
%endif
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 6
BuildRequires: perl-devel
%endif
BuildRequires: perl(ExtUtils::Embed)
BuildRequires: krb5-devel

ExclusiveArch: %{ix86} x86_64 ia64 s390 s390x sparc64 ppc ppc64

# Pre-releases are instead in:
# http://dl.openafs.org/dl/openafs/candidate/afsvers/...
Source0: http://www.openafs.org/dl/openafs/%{afsvers}/openafs-%{afsvers}-src.tar.bz2
Source1: http://www.openafs.org/dl/openafs/%{afsvers}/openafs-%{afsvers}-doc.tar.bz2
%define srcdir openafs-%{afsvers}

Source10: http://www.openafs.org/dl/openafs/%{afsvers}/RELNOTES-%{afsvers}
Source11: http://www.openafs.org/dl/openafs/%{afsvers}/ChangeLog
Source20: http://dl.central.org/dl/cellservdb/CellServDB.2014-11-17

Source30: openafs.sysconfig
Source31: openafs.cacheinfo

Source40: openafs-client.init
Source41: openafs-client.service
Source42: openafs-client.modules

Source50: openafs-server.init
Source51: openafs-server.service

Source60: openafs.files
Source61: openafs-client.files
Source62: openafs-server.files
Source63: openafs-authlibs.files
Source64: openafs-authlibs-devel.files
Source65: openafs-devel.files
Source66: openafs-docs.files
Source67: openafs-kpasswd.files
Source68: openafs-krb5.files
Source69: openafs-compat.files
Source70: openafs-transarc-client.files
Source71: openafs-transarc-server.files

%description
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides common files shared across all the various
OpenAFS packages but are not necessarily tied to a client or server.

%files -f %{_sourcedir}/openafs.files


%package client
Summary: OpenAFS Filesystem Client
Group: System Environment/Daemons

Requires: binutils, openafs = %{version}
Requires: %{name}-kmod >= %{version}
%if %{use_systemd}
Requires: systemd-units
Requires(post): systemd-units, systemd-sysv
Requires(preun): systemd-units
Requires(postun): systemd-units
%endif
Provides: %{name}-kmod-common = %{version}

%description client
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides basic client support to mount and manipulate
AFS.

%post client
if [ $1 = 1 ] ; then 
    # Initial installation, not an upgrade
    %if %{use_systemd}
        /bin/systemctl daemon-reload >/dev/null 2>&1 || :
    %else
        chkconfig --add openafs-client
    %endif
fi

# Generate CellServDB
[ -f %{_sysconfdir}/openafs/CellServDB.local ] || touch %{_sysconfdir}/openafs/CellServDB.local

( cd %{_sysconfdir}/openafs && \
  cat CellServDB.local CellServDB.dist > CellServDB.tmp && \
  chmod 644 CellServDB.tmp && \
  mv CellServDB.tmp CellServDB )

%preun client
if [ $1 = 0 ] ; then
    # Package removal, not upgrade
    %if %{use_systemd}
        /bin/systemctl --no-reload disable openafs-client.service > /dev/null 2>&1 || :
        /bin/systemctl stop openafs-client.service > /dev/null 2>&1 || :
    %else
        %{initdir}/openafs-client stop
        chkconfig --del openafs-client
    %endif
fi

%if %{use_systemd}
%postun client
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
%endif

%files client -f %{_sourcedir}/openafs-client.files
%defattr(-,root,root)
%if %{use_systemd}
    %{_unitdir}/openafs-client.service
    %{_sysconfdir}/sysconfig/modules/openafs-client.modules
%else
    %{initdir}/openafs-client
%endif


%package server
Summary: OpenAFS Filesystem Server
Group: System Environment/Daemons

Requires: openafs = %{version}
%if %{use_systemd}
Requires: systemd-units
Requires(post): systemd-units, systemd-sysv
Requires(preun): systemd-units
Requires(postun): systemd-units
%endif

%description server
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides basic server support to host files in an AFS
Cell.

%post server
%if %{use_systemd}
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
%else
    if [ $1 -eq 1 ] ; then
        # Initial install, not an upgrade
        chkconfig --add openafs-server
    fi
%endif

%preun server
if [ $1 = 0 ] ; then
    # Package removal, not an upgrade
    %if %{use_systemd}
        /bin/systemctl --no-reload disable openafs-server.service > /dev/null 2>&1 || :
        /bin/systemctl stop openafs-server.service > /dev/null 2>&1 || :
    %else
        %{initdir}/openafs-server stop
        chkconfig --del openafs-server
    %endif
fi

%if %{use_systemd}
%postun server
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
%endif

%files server -f %{_sourcedir}/openafs-server.files
%defattr(-,root,root)
%if %{use_systemd}
    %{_unitdir}/openafs-server.service
%else
    %{initdir}/openafs-server
%endif


%package authlibs
Summary: OpenAFS authentication shared libraries
Group: Applications/System

%description authlibs
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides a shared version of libafsrpc and libafsauthent. 
None of the programs included with OpenAFS currently use these shared 
libraries; however, third-party software that wishes to perform AFS 
authentication may link against them.

%post authlibs
/sbin/ldconfig

%postun authlibs
/sbin/ldconfig

%files authlibs -f %{_sourcedir}/openafs-authlibs.files


%package authlibs-devel
Summary: OpenAFS shared library development
Group: Development/Libraries

Requires: openafs-authlibs = %{version}-%{release}
Requires: openafs-devel = %{version}-%{release}

%description authlibs-devel
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package includes the static versions of libafsrpc and 
libafsauthent, and symlinks required for building against the dynamic 
libraries.

%files authlibs-devel -f %{_sourcedir}/openafs-authlibs-devel.files


%package devel
Summary: OpenAFS Development Libraries and Headers
Group: Development/Libraries
Requires: openafs = %{version}-%{release}

%description devel
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides static development libraries and headers needed
to compile AFS applications.  Note: AFS currently does not provide
shared libraries.

%files devel -f %{_sourcedir}/openafs-devel.files


%package docs
Summary: OpenAFS user and administrator documentation
Group: Documentation
Requires: openafs = %{version}-%{release}

%description docs
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides HTML documentation for OpenAFS users and system
administrators.

%files docs -f %{_sourcedir}/openafs-docs.files


%package kpasswd
Summary: OpenAFS KA kpasswd support
Group: Applications/System
Requires: openafs

%description kpasswd
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides the compatibility symlink for kpasswd, in case
you are using KAserver instead of Krb5.

%files kpasswd -f %{_sourcedir}/openafs-kpasswd.files


%package krb5
Summary: OpenAFS programs to use with krb5
Group: Applications/System
Requires: openafs = %{version}
BuildRequires: krb5-devel

%description krb5
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides compatibility programs so you can use krb5
to authenticate to AFS services, instead of using AFS's homegrown
krb4 lookalike services.

%files krb5 -f %{_sourcedir}/openafs-krb5.files


%package compat
Summary: OpenAFS client compatibility symlinks
Group: Applications/System
Requires: openafs = %{version}, openafs-client = %{version}
Obsoletes: openafs-client-compat

%description compat
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides compatibility symlinks in /usr/afsws.  It is
completely optional, and is only necessary to support legacy
applications and scripts that hard-code the location of AFS client
programs.

%files compat -f %{_sourcedir}/openafs-compat.files


%package transarc-client
Summary: OpenAFS client compatibility symlinks
Group: System Environment/Daemons
Requires: openafs = %{version}, openafs-client = %{version}

%description transarc-client
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides compatibility symlinks for Transarc paths.  It
is completely optional, and is only necessary to support legacy
applications and scripts that hard-code the location of AFS client
programs.

%files transarc-client -f %{_sourcedir}/openafs-transarc-client.files


%package transarc-server
Summary: OpenAFS client compatibility symlinks
Group: System Environment/Daemons
Requires: openafs = %{version}, openafs-server = %{version}

%description transarc-server
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides compatibility symlinks for Transarc paths.  It
is completely optional, and is only necessary to support legacy
applications and scripts that hard-code the location of AFS client
programs.

%files transarc-server -f %{_sourcedir}/openafs-transarc-server.files


%prep
# '-q' to not print a file listing of everything we extract
# '-b 1' to extract our Source1 (the doc tarball) in addition to Source0
# '-n' to specify our src dir
%setup -q -b 1 -n %{srcdir}

%build

%ifarch %{ix86}
    sysname=i386_linux26

%else
    case %{_arch} in
        x86_64) sysname=amd64_linux26    ;;
        alpha*) sysname=alpha_linux_26   ;;
        *)      sysname=%{_arch}_linux26 ;;
    esac
%endif

%configure \
       afsconfdir="%{_sysconfdir}/openafs/server" \
       viceetcdir="%{_sysconfdir}/openafs" \
       afslogsdir="%{_var}/log/openafs" \
       afslocaldir="%{_var}/lib/openafs/local" \
       --localstatedir="%{_var}/lib" \
       --with-afs-sysname=${sysname} \
       --disable-strip-binaries \
       --disable-kernel-module \
       --enable-debug \
       --enable-debug-lwp \
       --enable-debug-pam \
       --with-krb5 \
       --enable-supergroups \
       --disable-fuse-client \
       || exit 1
make

%install
make install DESTDIR=$RPM_BUILD_ROOT

# Create various dirs
mkdir -p $RPM_BUILD_ROOT/afs
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/openafs
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/openafs/server
mkdir -p $RPM_BUILD_ROOT%{_var}/log/openafs
mkdir -p $RPM_BUILD_ROOT%{_var}/lib/openafs/backup
mkdir -p $RPM_BUILD_ROOT%{_var}/lib/openafs/db
mkdir -p $RPM_BUILD_ROOT%{_var}/lib/openafs/local
mkdir -p $RPM_BUILD_ROOT%{_var}/cache/openafs

mkdir -p                   $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig
install -m 755 %{SOURCE30} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/openafs

%if %{use_systemd}
    mkdir -p                   $RPM_BUILD_ROOT%{_unitdir}
    install -m 755 %{SOURCE41} $RPM_BUILD_ROOT%{_unitdir}/openafs-client.service
    install -m 755 %{SOURCE51} $RPM_BUILD_ROOT%{_unitdir}/openafs-server.service

    mkdir -p                   $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/modules
    install -m 755 %{SOURCE42} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/modules/openafs-client.modules

%else
    mkdir -p                   $RPM_BUILD_ROOT%{initdir}
    install -m 755 %{SOURCE40} $RPM_BUILD_ROOT%{initdir}/openafs-client
    install -m 755 %{SOURCE50} $RPM_BUILD_ROOT%{initdir}/openafs-server
%endif

# Move PAM modules into correct location
mkdir -p                              $RPM_BUILD_ROOT%{pamdir}
mv $RPM_BUILD_ROOT%{_libdir}/pam_afs* $RPM_BUILD_ROOT%{pamdir}

# PAM symlinks
ln -sf pam_afs.so.1     $RPM_BUILD_ROOT%{pamdir}/pam_afs.so
ln -sf pam_afs.krb.so.1 $RPM_BUILD_ROOT%{pamdir}/pam_afs.krb.so

# Install documentation
mkdir -p $RPM_BUILD_ROOT/$RPM_DOC_DIR/openafs-%{afsvers}
tar cf - -C doc LICENSE html pdf | \
    tar xf - -C $RPM_BUILD_ROOT/$RPM_DOC_DIR/openafs-%{afsvers}
install -m 644 %{SOURCE10} $RPM_BUILD_ROOT/$RPM_DOC_DIR/openafs-%{afsvers}
install -m 644 %{SOURCE11} $RPM_BUILD_ROOT/$RPM_DOC_DIR/openafs-%{afsvers}

# Populate /etc/openafs
echo openafs.org >            $RPM_BUILD_ROOT%{_sysconfdir}/openafs/ThisCell
install -p -m 644 %{SOURCE20} $RPM_BUILD_ROOT%{_sysconfdir}/openafs/CellServDB.dist
touch                         $RPM_BUILD_ROOT%{_sysconfdir}/openafs/CellServDB.local
install -p -m 644 %{SOURCE31} $RPM_BUILD_ROOT%{_sysconfdir}/openafs/cacheinfo

# Move vos from sbin to bin, since it does not require privileges to use many
# useful commands.
mv $RPM_BUILD_ROOT%{_sbindir}/vos $RPM_BUILD_ROOT%{_bindir}/vos

# Move asetkey from bin to sbin, since doing anything with this command
# requires root privileges
mv $RPM_BUILD_ROOT%{_bindir}/asetkey $RPM_BUILD_ROOT%{_sbindir}/asetkey

# Remove unused stuff
for f in \
        %{_bindir}/knfs \
        %{_bindir}/livesys \
        %{_bindir}/kpwvalid \
        %{_sbindir}/kdb \
        %{_sbindir}/rmtsysd \
        %{_mandir}/man1/dlog \
        %{_mandir}/man1/copyauth \
        %{_mandir}/man1/livesys \
        %{_mandir}/man1/knfs \
        %{_mandir}/man1/symlink \
        %{_mandir}/man8/aklog_dynamic_auth \
        %{_mandir}/man8/kdb \
        %{_mandir}/man8/rmtsysd \
        %{_mandir}/man8/xfs_size_check \
        %{_libdir}/libjuafs.a \
        %{_libdir}/libuafs.a \
        ; do
    rm $RPM_BUILD_ROOT"$f"*
done

# Install /usr/afsws/bin compat links
mkdir -p $RPM_BUILD_ROOT%{_prefix}/afsws/bin
for f in \
        afsmonitor \
        bos \
        fs \
        kapasswd \
        klog \
        klog.krb \
        pagsh \
        pagsh.krb \
        pts \
        restorevol \
        scout \
        sys \
        tokens \
        tokens.krb \
        translate_et \
        udebug \
        unlog \
        xstat_cm_test \
        xstat_fs_test \
        ; do
    # Find the file in /usr/bin or /usr/sbin, and symlink it into
    # /usr/afsws/bin.
    if   [ -x $RPM_BUILD_ROOT%{_prefix}/bin/$f ] ; then
        ln -s %{_prefix}/bin/$f $RPM_BUILD_ROOT%{_prefix}/afsws/bin/

    elif [ -x $RPM_BUILD_ROOT%{_prefix}/sbin/$f ] ; then
        ln -s %{_prefix}/sbin/$f $RPM_BUILD_ROOT%{_prefix}/afsws/bin/

    else
        echo "Cannot find $f" >&2
        exit 1
    fi
done

# Install /usr/afsws/etc compat links
mkdir -p $RPM_BUILD_ROOT%{_prefix}/afsws/etc
for f in \
        backup \
        butc \
        fms \
        fstrace \
        kas \
        read_tape \
        rxdebug \
        uss \
        vos \
        vsys \
        ; do
    # Find the file in /usr/bin or /usr/sbin, and symlink it into
    # /usr/afsws/etc.
    if   [ -x $RPM_BUILD_ROOT%{_prefix}/bin/$f ] ; then
        ln -s %{_prefix}/bin/$f $RPM_BUILD_ROOT%{_prefix}/afsws/etc/

    elif [ -x $RPM_BUILD_ROOT%{_prefix}/sbin/$f ] ; then
        ln -s %{_prefix}/sbin/$f $RPM_BUILD_ROOT%{_prefix}/afsws/etc/

    else
        echo "Cannot find $f" >&2
        exit 1
    fi
done

# Install client transarc compat links
mkdir                        $RPM_BUILD_ROOT%{_prefix}/vice
ln -s %{_sysconfdir}/openafs $RPM_BUILD_ROOT%{_prefix}/vice/etc
ln -s %{_var}/cache/openafs  $RPM_BUILD_ROOT%{_prefix}/vice/cache

# Install server transarc compat links
mkdir                               $RPM_BUILD_ROOT%{_prefix}/afs
ln -s %{_sysconfdir}/openafs/server $RPM_BUILD_ROOT%{_prefix}/afs/etc
ln -s %{_var}/log/openafs           $RPM_BUILD_ROOT%{_prefix}/afs/logs
ln -s %{_var}/lib/openafs/backup    $RPM_BUILD_ROOT%{_prefix}/afs/backup
ln -s %{_var}/lib/openafs/db        $RPM_BUILD_ROOT%{_prefix}/afs/db
ln -s %{_var}/lib/openafs/local     $RPM_BUILD_ROOT%{_prefix}/afs/local

# Install server compat links for /usr/afs/bin
mkdir                               $RPM_BUILD_ROOT%{_prefix}/afs/bin
for f in \
        asetkey \
        bos \
        bosserver \
        bos_util \
        buserver \
        dafileserver \
        dafssync-debug \
        dasalvager \
        davolserver \
        fileserver \
        fs \
        fssync-debug \
        kadb_check \
        ka-forwarder \
        kas \
        kaserver \
        klog \
        klog.krb \
        prdb_check \
        pts \
        ptserver \
        pt_util \
        restorevol \
        salvager \
        salvageserver \
        salvsync-debug \
        state_analyzer \
        tokens \
        tokens.krb \
        udebug \
        upclient \
        upserver \
        vldb_check \
        vldb_convert \
        vlserver \
        volinfo \
        volscan \
        volserver \
        vos \
        ; do

    # Find the file in /usr/sbin, /usr/bin, or /usr/libexec/openafs, and
    # symlink it into /usr/afs/bin.
    if   [ -x $RPM_BUILD_ROOT%{_prefix}/sbin/$f ] ; then
        ln -s %{_prefix}/sbin/$f $RPM_BUILD_ROOT%{_prefix}/afs/bin/

    elif [ -x $RPM_BUILD_ROOT%{_prefix}/bin/$f ] ; then
        ln -s %{_prefix}/bin/$f $RPM_BUILD_ROOT%{_prefix}/afs/bin/

    elif [ -x $RPM_BUILD_ROOT%{_libexecdir}/openafs/$f ] ; then
        ln -s %{_libexecdir}/openafs/$f $RPM_BUILD_ROOT%{_prefix}/afs/bin/

    else
        echo "Cannot find $f" >&2
        exit 1
    fi
done

%clean
[ "$RPM_BUILD_ROOT" != "/" -a "x%{debugspec}" != "x1" ] && \
        rm -rf $RPM_BUILD_ROOT
