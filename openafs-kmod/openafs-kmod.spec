# Openafs Spec $Revision$

%define afsvers 1.6.9
%define pkgvers 1.6.9
# for beta/rc releases make pkgrel 0.<tag>
# for real releases make pkgrel 1 (or more for extra releases)
%define pkgrel 1

%{!?fedorakmod: %define fedorakmod 1}
%{!?build_dkmspkg: %define build_dkmspkg 1}

# Determine presence of rpmbuild command line --define arguments used for
# option specification
%define kernvers_on_cmdline %{?kernvers:1}%{!?kernvers:0}
%define build_userspace_on_cmdline %{?build_userspace:1}%{!?build_userspace:0}
%define build_modules_on_cmdline %{?build_modules:1}%{!?build_modules:0}
%define build_authlibs_on_cmdline %{?build_authlibs:1}%{!?build_authlibs:0}

%if 0%{?rhel} >= 5
%define fedorakmod 1
%endif
%if 0%{?fedora}
%define fedorakmod 1
%endif

%if !%{fedorakmod}
# Determine the version of the kernel to build against
# - automatically select running kernel if there are sources in /lib/modules
# - note that this can be overridden on the command line
#
%if !%{kernvers_on_cmdline}
%define kernvers %(%{_sourcedir}/openafs-kernel-version.sh)
%endif

# If we're building for a 2.4 series kernel, then fedora style kmods aren't
# appropriate - disable them.

%define kern24 %([ `echo "%{kernvers}" | sed -e 's/^\([0-9]*\.[0-9]*\)\..*/\1/'` = "2.4" ] && echo 1 || echo 0)

%if %{kern24}
%define fedorakmod 0
%endif
%endif

%if %{fedorakmod}
%define kmodtool bash %{_sourcedir}/openafs-kmodtool

%define kmod_name openafs
%define kverrel %(%{kmodtool} verrel %{?kernvers} 2>/dev/null)

%define upvar ""
%{!?kvariants: %define kvariants %{?upvar}}

%if %{?ksrcdir:1}%{!?ksrcdir:0}
  if ( -d %{_usrsrc}/kernels/%{kverrel}-%{_target_cpu}) ; then
    %define ksrcdir %{_usrsrc}/kernels/%{kverrel}-%{_target_cpu}}
  else
    %define ksrcdir %{_usrsrc}/kernels/%{kverrel}.%{_target_cpu}}
  fi
%endif

%else # Legacy kernel build stuff 

%define kversis %{_sourcedir}/openafs-kvers-is.sh
%define kvers %(%{kversis} parsev %{kernvers})
%define kvers_is_24 %(%{kversis} %{kvers} "2.4")
%define kvers_is_26 %(%{kversis} %{kvers} "2.6")
%define ktype %(%{kversis} parset %{kernvers})
%define kversion %(%{kversis} kvers %{kernvers})

# This is where to look for kernel build include files.  Default
# is /lib/modules/<kvers>/build, but you can define kbase and
# kend on the commandline to change that.
#
%if %{?kbase:0}%{!?kbase:1}
%define kbase /lib/modules/
%endif
%if %{?kend:0}%{!?kend:1}
%define kend /build
%endif
# Let the buildscript define the ksrcdir directly -- needed for RHEL4
%if %{?ksrcdir:0}%{!?ksrcdir:1}
%define ksrcdir %{kbase}%{kernvers}%{kend}
%endif

%if %{?kmoddir:0}%{!?kmoddir:1}
%define kmoddir /lib/modules
%endif
%define kxmoddir %{kmoddir}/%{kernvers}

# End legacy kernel build stuff
%endif 

%define dkms_version %{pkgvers}-%{pkgrel}%{?dist}

# Set 'debugspec' to 1 if you want to debug the spec file.  This will
# not remove the installed tree as part of the %clean operation
%if %{?debugspec:0}%{!?debugspec:1}
%define debugspec 0
%endif

# Set 'krb5support' to 1 if you want to build the openafs-krb5 package
# to distribute aklog and asetkey
%define krb5support %{?_without_krb5:0}%{!?_without_krb5:1}

# Set 'bootkernelsupport' to 1 if you want to build the
# kernel module for Red Hat BOOT Kernels on x86.
%define bootkernelsupport %{?_with_bootkernel:1}%{!?_with_bootkernel:0}

# Define the location of your init.d directory
%define initdir /etc/rc.d/init.d

#determine if the kernel provides an arch-specific Provides
%define kprovidesarch %(%{kversis} provideskernelarch %{ksrcdir} %{_target_cpu})

# Define the location of the PAM security module directory
%define pamdir /%{_lib}/security

#######################################################################
# You probably don't need to change anything beyond this line
# NOTE: If you do, please email me!!!

# Determine which elements of OpenAFS to build.  For non-x86 arches
# (subject to the ExclusiveArch setting, below), we build both userspace
# and modules.  For most x86 arches, we build just the kernel modules.  For
# i386, we build just the userspace.  If you're running an i386 kernel,
# you'll need to tweak that last bit.
%if !%{build_userspace_on_cmdline} && !%{build_modules_on_cmdline}

%define build_userspace 1
%define build_modules 1
%ifarch %{ix86} x86_64 ia64
%define build_authlibs 1
%else
%define build_authlibs 0
%endif

%else
%if !%{build_userspace_on_cmdline}
%define build_userspace 0
%endif
%if !%{build_modules_on_cmdline}
%define build_modules 0
%endif
%endif

%if !%{build_authlibs_on_cmdline}
%if %{build_userspace_on_cmdline}
%define build_authlibs 1
%else
%define build_authlibs 0
%endif
%endif

%if %{build_modules}
%if !%{fedorakmod}

# Define the set of kernel module variations to be built:
# For 2.4 kernels we just build everything at once for a particular
# kernel.   So we build up, smp, and bigmem all at once.
# For 2.6 kernels we have to build against the specific kernel headers
# for a particular kernel variation.  AFS will handle the specific smp or
# non-smp determination.  So just always build as if it's "up" -- the kernel
# version will have the 'variation' type already in the version #.

%define up_package 0
%define smp_package 0
%define bigmem_package 0
%define hugemem_package 0
%define largesmp_package 0

#######################################################################
# 2.4
%if %{kvers_is_24}
%define kdepend kernel-source
%define up_package 1
%define smp_package 1
%define smp_ext smp

%define bigmem_package %(%{kversis} find %{ksrcdir} %{_target_cpu} bigmem) 
%if %{bigmem_package}
%define bigmem_ext bigmem
%endif

%define hugemem_package %(%{kversis} find %{ksrcdir} %{_target_cpu} hugemem) 
%if %{hugemem_package}
%define hugemem_ext hugemem
%endif

%define kvariations up smp %{?bigmem_ext:%{bigmem_ext}} %{?hugemem_ext:%{hugemem_ext}}

#######################################################################
# 2.6
%else
%if %{kvers_is_26}
%define kvariations up
%ifarch s390x
%define ktype "smp"
%define up_package 1
%else
%define up_package %(%{kversis} "%{ktype}" "")
%define smp_package %(%{kversis} "%{ktype}" "smp")
%define hugemem_package %(%{kversis} "%{ktype}" "hugemem")
%define largesmp_package %(%{kversis} "%{ktype}" "largesmp")
%endif

%if !%{up_package} && !%{smp_package} && !%{hugemem_package} && !%{largesmp_package}
%error "unknown kernel type: %{ktype}"
%endif

%if !%{kernvers_on_cmdline}
%define kdepend %{ksrcdir}/include/linux/version.h
%endif

#######################################################################
# other kernels?
%else
%error "unknown kernel version: ${kvers} (parsed from %{kernvers})"
%endif
%endif

# End of legacy kernel module build
%endif 
%endif

# Make sure RPM doesn't complain about installed but non-packaged files.
#define __check_files  %{nil}

Summary: OpenAFS distributed filesystem
Name: openafs
Version: %{pkgvers}
Release: %{pkgrel}%{?dist}
License: IBM Public License
URL: http://www.openafs.org
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Packager: OpenAFS Gatekeepers <openafs-gatekeepers@openafs.org>
Group: Networking/Filesystems
BuildRequires: %{?kdepend:%{kdepend}, } pam-devel, ncurses-devel, flex, bison
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
BuildRequires: systemd-units
%endif
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 6
BuildRequires: perl-devel
%endif
BuildRequires: perl(ExtUtils::Embed)
%if %{krb5support}
BuildRequires: krb5-devel
%endif
%if %{build_modules}
BuildRequires: kernel-devel
%endif

ExclusiveArch: %{ix86} x86_64 ia64 s390 s390x sparc64 ppc ppc64

#    http://dl.openafs.org/dl/openafs/candidate/%{afsvers}/...
Source0: http://www.openafs.org/dl/openafs/%{afsvers}/openafs-%{afsvers}-src.tar.bz2
Source1: http://www.openafs.org/dl/openafs/%{afsvers}/openafs-%{afsvers}-doc.tar.bz2
%define srcdir openafs-%{afsvers}

Source10: http://www.openafs.org/dl/openafs/%{afsvers}/RELNOTES-%{afsvers}
Source11: http://www.openafs.org/dl/openafs/%{afsvers}/ChangeLog

Source20: http://dl.central.org/dl/cellservdb/CellServDB.2013-01-28

Source30: openafs-kernel-version.sh
Source996: openafs-kvers-is.sh
Source997: openafs-buildfedora.pl
Source998: openafs-buildall.sh
Source999: openafs-kmodtool

%description
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides common files shared across all the various
OpenAFS packages but are not necessarily tied to a client or server.

The OpenAFS SRPM can be rebuilt with the following options to control
what gets built:

 --define "kernvers 2.4.20-1.1376_FC3" Specify the specific kernel version 
                                  to build modules against. The default is
                                  to build against the currently-running
                                  kernel.
 --define "kbase /lib/modules/"   The base location to look for kernel headers
 --define "kend /build"           The 'end' location to look for kernels
                                  The build will define ksrvdir as
                                  %%{kbase}<kernvers>%%{kend}

 --without krb5                   Disable krb5 support (default: with krb5)
 --with bitmap-later              Enable "bitmap later" support
 --with bos-restricted            Enable "bos restricted" mode
 --with largefiles                Enable "largefile fileserver" mode
 --with supergroups               Enable "supergroups"

 --target=i386                    The target architecture to build for.
                                  When building for a non-default target
                                  the build may choose whether to build
                                  userspace or kernel modules automatically.
                                  The defaults are probably what you want.

 --define "build_userspace 1"     Request building of userspace tools
 --define "build_modules 1"       Request building of kernel modules
                                  You probably never need to specify these.

 --define "kmoddir /lib/modules"  This is the base location where modules
                                  will be installed.  You probably don't
                                  need to change this ever.

 --define "fedorakmod 0"	  Disable the building of 'Fedora' style kernel 
				  modules, and use the old format.

 --define "kvariants <variants>"  When building Fedora style kernel modules,
                                  this defines the set of kernel variants
                                  to build.
                                  <variants> is a space seperated list which
                                  may contain one or more of
                                  '' (for the generic kernel), smp, PAE, xen
                                  or kdump 

To a kernel module for your running kernel, just run:
  rpmbuild --rebuild --target=`uname -m` openafs-%{pkgvers}-%{pkgrel}%{?dist}.src.rpm

##############################################################################
#
# build the userspace side of things if so requested
#
##############################################################################
%if %{build_userspace}

%package client
Requires: binutils, openafs = %{version}
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
Requires: systemd-units
Requires(post): systemd-units, systemd-sysv
Requires(preun): systemd-units
Requires(postun): systemd-units
%endif

%if %{fedorakmod}
Requires: %{name}-kmod >= %{version}
Provides: %{name}-kmod-common = %{version}
%else
Requires: openafs-kernel
%endif

Summary: OpenAFS Filesystem Client
Group: Networking/Filesystem

%description client
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides basic client support to mount and manipulate
AFS.

%package server
Requires: openafs = %{version}
Summary: OpenAFS Filesystem Server
Group: Networking/Filesystems
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
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

%if %{build_dkmspkg}
%package -n dkms-%{name}
Summary:        DKMS-ready kernel source for AFS distributed filesystem
Group:          Development/Kernel
Provides:       openafs-kernel = %{version}
%if %{fedorakmod}
Provides: %{name}-kmod = %{version}
%endif
Requires(pre):  dkms
Requires(pre):  flex
Requires(post): dkms
Requires:	%{name}-kmod-common = %{version}

%description -n dkms-%{name}
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides the source code to allow DKMS to build an
AFS kernel module.
%endif

%if %{build_authlibs}
%package authlibs
Summary: OpenAFS authentication shared libraries
Group: Networking/Filesystems

%description authlibs
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides a shared version of libafsrpc and libafsauthent. 
None of the programs included with OpenAFS currently use these shared 
libraries; however, third-party software that wishes to perform AFS 
authentication may link against them.
%endif

%package authlibs-devel
%if %{build_authlibs}
Requires: openafs-authlibs = %{version}-%{release}
%endif
Requires: openafs-devel = %{version}-%{release}
Summary: OpenAFS shared library development
Group: Development/Filesystems

%description authlibs-devel
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package includes the static versions of libafsrpc and 
libafsauthent, and symlinks required for building against the dynamic 
libraries.

%package devel
Summary: OpenAFS Development Libraries and Headers
Group: Development/Filesystems
Requires: openafs = %{version}-%{release}

%description devel
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides static development libraries and headers needed
to compile AFS applications.  Note: AFS currently does not provide
shared libraries.

%package docs
Summary: OpenAFS user and administrator documentation
Requires: openafs = %{version}-%{release}
Group: Networking/Filesystems

%description docs
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides HTML documentation for OpenAFS users and system
administrators.

%package kernel-source
Summary: OpenAFS Kernel Module source tree
Group: Networking/Filesystems
Provides: openafs-kernel = %{version}
%if %{fedorakmod}
Provides: %{name}-kmod = %{version}
%endif

%description kernel-source
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides the source code to build your own AFS kernel
module.

%package compat
Summary: OpenAFS client compatibility symlinks
Requires: openafs = %{version}, openafs-client = %{version}
Group: Networking/Filesystems
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

%package kpasswd
Summary: OpenAFS KA kpasswd support
Requires: openafs
Group: Networking/Filesystems

%description kpasswd
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides the compatibility symlink for kpasswd, in case
you are using KAserver instead of Krb5.

%if %{krb5support}
%package krb5
Summary: OpenAFS programs to use with krb5
Requires: openafs = %{version}
Group: Networking/Filesystems
BuildRequires: krb5-devel

%description krb5
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides compatibility programs so you can use krb5
to authenticate to AFS services, instead of using AFS's homegrown
krb4 lookalike services.
%endif

%endif

##############################################################################
#
# build the kernel modules if so requested
#
##############################################################################
%if %{build_modules}

%if %{fedorakmod}
%{expand:%(%{kmodtool} rpmtemplate %{kmod_name} %{kverrel} %{kvariants} 2>/dev/null)}

%else

# Legacy kernel compilation code here ...
%define modkversion %(echo %{kernvers} | cut -d- -f1)
%define modkrelease %(echo %{kernvers} | cut -d- -f2)
%define modpkgrel %{modkversion}_%{modkrelease}_%{pkgrel}

%if %{up_package}
%package kernel
Summary: OpenAFS Kernel Module (compiled for UP)
Release: %{modpkgrel}
Group: Networking/Filesystems
Provides: openafs-kernel = %{version}
%if %{kprovidesarch}
Requires: kernel-%{_target_cpu} = %{kversion}
%else
Requires: /boot/config-%{kernvers}
%endif

%description kernel
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides a precompiled AFS kernel module for %{kernvers}.
%endif

%if %{smp_package}
%package kernel-smp
Summary: OpenAFS Kernel Module (compiled for SMP)
Release: %{modpkgrel}
Provides: openafs-kernel = %{version}
%if %{kprovidesarch}
Requires: kernel-smp-%{_target_cpu} = %{kversion}
%else
Requires: /boot/config-%{kernvers}%{?smp_ext:%{smp_ext}}
%endif
Group: Networking/Filesystems

%description kernel-smp
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides a precompiled AFS kernel module for %{kernvers}.
%endif

%if %{largesmp_package}
%package kernel-largesmp
Summary: OpenAFS Kernel Module (compiled for LARGESMP)
Release: %{modpkgrel}
Provides: openafs-kernel = %{version}
%if %{kprovidesarch}
Requires: kernel-largesmp-%{_target_cpu} = %{kversion}
%else
Requires: /boot/config-%{kernvers}%{?largesmp_ext:%{largesmp_ext}}
%endif
Group: Networking/Filesystems

%description kernel-largesmp
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides a precompiled AFS kernel module for %{kernvers}.
%endif
 
%if %{bigmem_package}
%package kernel-bigmem
Summary: OpenAFS Kernel Module (compiled for SMP & big memory support)
Release: %{modpkgrel}
Provides: openafs-kernel = %{version}
%if %{kprovidesarch}
Requires: kernel-bigmem-%{_target_cpu} = %{kversion}
%else
Requires: /boot/config-%{kernvers}%{?bigmem_ext:%{bigmem_ext}}
%endif
Group: Networking/Filesystems

%description kernel-bigmem
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides a precompiled AFS kernel module for %{kernvers}.
%endif

%if %{hugemem_package}
%package kernel-hugemem
Summary: OpenAFS Kernel Module (compiled for SMP & huge memory support)
Release: %{modpkgrel}
Provides: openafs-kernel = %{version}
%if %{kprovidesarch}
Requires: kernel-hugemem-%{_target_cpu} = %{kversion}
%else
Requires: /boot/config-%{kernvers}%{?hugemem_ext:%{hugemem_ext}}
%endif
Group: Networking/Filesystems

%description kernel-hugemem
The AFS distributed filesystem.  AFS is a distributed filesystem
allowing cross-platform sharing of files among multiple computers.
Facilities are provided for access control, authentication, backup and
administrative management.

This package provides a precompiled AFS kernel module for %{kernvers}.
%endif

%endif
# End legacy kernel compilation code ...
%endif

##############################################################################
#
# PREP
#
##############################################################################

%prep

: @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
: @@@
: @@@ kernel version:     %{kernvers}
%if %{fedorakmod}
: @@@ kernel variations:  %{kvariants}
%else
: @@@ base kernel version:%{kversion}
: @@@ kernel modules dir: %{kxmoddir}
: @@@ kernel source dir:  %{ksrcdir}
%if %{kvers_is_24}
: @@@ kernel variations:  %{kvariations}
%else
%if %{up_package}
: @@@ kernel type:        up
%else
: @@@ kernel type:        %{ktype}
%endif
%endif
%endif
: @@@ PAM modules dir:    %{pamdir}
: @@@ build userspace:    %{build_userspace}
: @@@ build modules:      %{build_modules}
: @@@ arch:               %{_arch}
: @@@ target cpu:         %{_target_cpu}
: @@@
: @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# Install OpenAFS src and doc
#%setup -q -n %{srcdir}
%setup -q -b 1 -n %{srcdir}

##############################################################################
#
# building
#
##############################################################################
%build
%if !%{fedorakmod}
case %{kernvers} in
   2.4.*)
       kv='24'
       ;;
   2.6.* | 3.*)
       kv='26'
       ;;
   *)
       echo "I don't know how to build linux-`expr %{kernvers} : '\(^[0-9]*[.][0-9]*\)'`"
       exit 1
       ;;
esac
%else
kv='26'
%endif

case %{_arch} in
       x86_64)                         sysname=amd64_linux${kv}        ;;
       alpha*)                         sysname=alpha_linux_${kv}       ;;
       i386|i486|i586|i686|athlon)     sysname=i386_linux${kv}         ;;
       *)                              sysname=%{_arch}_linux${kv}     ;;
esac

%ifarch %{ix86}
archlist="i386 i586 i686 athlon"
%if %{bootkernelsupport}
  archlist="${archlist} BOOT"
%endif
%else
archlist=%{_arch}
%endif

#
# PrintDefine var value statements file
#
PrintDefine() {
    case $3 in
    *ifn*)
	echo "#ifndef $1" >> $4
	;;
    esac
    case $3 in
    *und*)
	echo "#undef $1" >> $4
	;;
    esac
    case $3 in
    *def*)
	echo "#define $1 $2" >> $4
	;;
    esac
    case $3 in
    *end*)
	echo "#endif" >> $4
	;;
    esac
    case $3 in
    *inc*)
	echo "#include $1" >> $4
	;;
    esac
    case $3 in
    *nl*)
	echo "" >> $4
	;;
    esac
}

# PrintRedhatKernelFix arch mp file
PrintRedhatKernelFix() {
    arch="$1"
    up=0
    smp=0
    largesmp=0
    ent=0
    bigmem=0
    hugemem=0
    boot=0
    bootsmp=0

    case "$2" in
       up)     up=1;;
       smp)    smp=1;;
       largesmp) largesmp=1;;
       bigmem) bigmem=1;;
       hugemem) hugemem=1;;
       *)
               echo "$2 not supported"
               exit 2;;
    esac

    file="$3"

    rm -f $file
    touch $file

    PrintDefine "REDHAT_FIX_H" "" ifn,def,nl $file

    PrintDefine __BOOT_KERNEL_ENTERPRISE $ent     und,def,nl $file
    PrintDefine __BOOT_KERNEL_BIGMEM     $bigmem  und,def,nl $file
    PrintDefine __BOOT_KERNEL_HUGEMEM    $hugemem und,def,nl $file
    PrintDefine __BOOT_KERNEL_SMP        $smp     und,def,nl $file
    PrintDefine __BOOT_KERNEL_LARGESMP   $largesmp und,def,nl $file
    PrintDefine __BOOT_KERNEL_UP         $up      und,def,nl $file
    PrintDefine __BOOT_KERNEL_BOOT       $boot    und,def,nl $file
    PrintDefine __BOOT_KERNEL_BOOTSMP    $bootsmp und,def,nl $file

    PrintDefine '"/boot/kernel.h"' "" inc,nl $file	# include file

    for ar in $archlist ; do
	if [ "$ar" = "$arch" ]; then
	    PrintDefine "__MODULE_KERNEL_$ar" "1" ifn,def,end $file
	else
	    PrintDefine "__MODULE_KERNEL_$ar" "" und $file	# undef
        fi
    done
    echo "" >> $file

    PrintDefine "" "" end $file

    if [ %{debugspec} = 1 ] ; then
	echo "Kernel Configuration File for Red Hat kernels:"
	cat $file
    fi
}

config_opts="--enable-redhat-buildsys \
	%{?_with_bitmap_later:--enable-bitmap-later} \
	%{?_with_bos_restricted:--enable-bos-restricted-mode} \
	%{?_with_largefiles:--enable-largefile-fileserver} \
	%{?_with_supergroups:--enable-supergroups} \
	--enable-transarc-paths"

# Configure AFS

# If we're using Fedora kmods, work out which is the best kernel module to 
# use for the userland configuration step. If no variants have been specified,
# then use the standard kernel. If variants are specified, use the standard kernel
# if it's listed, otherwise pick the first listed kernel.
ksrc=""
%if %{fedorakmod} 
  for kvariant in %{kvariants} ; do
    if [ -z "${kvariant}" -o -z "$ksrc" ] ; then
      if [ -d %{_usrsrc}/kernels/%{kverrel}${kvariant:+-$kvariant}-%{_target_cpu} ] ; then
        ksrc=%{_usrsrc}/kernels/%{kverrel}${kvariant:+-$kvariant}-%{_target_cpu}
      elif [ -d %{_usrsrc}/kernels/%{kverrel}.%{_target_cpu}${kvariant:++$kvariant} ] ; then
        ksrc=%{_usrsrc}/kernels/%{kverrel}.%{_target_cpu}${kvariant:++$kvariant}
      else
        ksrc=%{_usrsrc}/kernels/%{kverrel}.%{_target_cpu}${kvariant:+.$kvariant}
      fi
    fi
  done
%endif
if [ -z "$ksrc" ] ; then
ksrc=%{ksrcdir}
fi

CFLAGS="$RPM_OPT_FLAGS"; export CFLAGS

%if %{krb5support}
%if %{?krb5config:1}%{!?krb5config:0}
KRB5_CONFIG="%{krb5config}"
export KRB5_CONFIG
%endif
%endif

./configure --with-afs-sysname=${sysname} \
       --prefix=%{_prefix} \
       --libdir=%{_libdir} \
       --bindir=%{_bindir} \
       --sbindir=%{_sbindir} \
       --disable-strip-binaries \
       --enable-debug \
       --with-linux-kernel-packaging \
%if %{build_modules}
       --with-linux-kernel-headers=${ksrc} \
%endif
%if %{krb5support}
	--with-krb5 \
%endif
       $config_opts \
       || exit 1

# Build the libafs tree
make only_libafs_tree || exit 1

# Configure each of our kernel modules

%if %{fedorakmod} && %{build_modules}
for kvariant in %{kvariants} ; do
  if [ -n "${kvariant}" ] ; then

    if [ -d %{_usrsrc}/kernels/%{kverrel}${kvariant:+-$kvariant}-%{_target_cpu} ] ; then
      ksrc=%{_usrsrc}/kernels/%{kverrel}${kvariant:+-$kvariant}-%{_target_cpu}

    elif [ -d %{_usrsrc}/kernels/%{kverrel}.%{_target_cpu}${kvariant:++$kvariant} ] ; then
      # Fedora 20 started putting kernel sources in e.g.
      # 3.12.5-302.fc20.i686+PAE, instead of:
      # 3.12.5-302.fc20.i686.PAE
      ksrc=%{_usrsrc}/kernels/%{kverrel}.%{_target_cpu}${kvariant:++$kvariant}

    else
      ksrc=%{_usrsrc}/kernels/%{kverrel}.%{_target_cpu}${kvariant:+.$kvariant}
    fi

    cp -R libafs_tree _kmod_build_${kvariant}
    pushd _kmod_build_${kvariant}
    ./configure --with-afs-sysname=${sysname} \
  	--prefix=%{_prefix} \
	--libdir=%{_libdir} \
	--bindir=%{_bindir} \
	--sbindir=%{_sbindir} \
        --with-linux-kernel-packaging \
	--with-linux-kernel-headers=${ksrc} \
	--enable-disconnected \
%if %{krb5support}
	--with-krb5-conf=/usr/kerberos/bin/krb5-config \
%endif
	$config_opts \
	|| exit 1
    popd
  fi
done
%endif

%if %{build_userspace}
# Build the user-space AFS stuff
make dest_nolibafs || exit 1
%endif

%if %{build_modules}
%if %{fedorakmod}
for kvariant in %{kvariants}
do
  if [ -n "${kvariant}" ] ; then
    pushd _kmod_build_$kvariant;
    make all
    popd
  else
    make dest_only_libafs
  fi
done

%else
# Begin legacy kernel module building code

%if %{kvers_is_24}
# Build all the kernel modules for linux 2.4.x
for variation in %{kvariations}
do
    if [ ${variation} = up ]
    then
       local_smp_def=-DREDHAT_FIX
       suffix=
    else
       local_smp_def="-DAFS_SMP -DREDHAT_FIX"
       suffix=${variation}
    fi

    PrintRedhatKernelFix %{_target_cpu} $variation src/config/redhat-fix.h
    make dest_only_libafs LOCAL_SMP_DEF="${local_smp_def}" \
	LINUX_MODULE_NAME="${suffix}" MPS=SP

done
rm -f src/config/redhat-fix.h

%elseif %{kvers_is_26}
# Build the kernel module for this version of linux 2.6.x
# Notice how much easier this is than 2.4.  On the other hand,
# we require much more external support to build multiple modules.

  # the MPS=SP just means that we don't add a '.mp' to the name.
  make dest_only_libafs MPS=SP

%endif
# End legacy kernel module building code
%endif
%endif


##############################################################################
#
# installation
#
##############################################################################
%install

export DONT_GPRINTIFY=1

[ $RPM_BUILD_ROOT != / ] && rm -rf $RPM_BUILD_ROOT
%if !%{fedorakmod}
case %{kernvers} in
   2.4.*)
       kv='24'
       kmodend=.o
       ;;
   2.6.* | 3.*)
       kv='26'
       kmodend=.ko
       ;;
   *)
       echo "I don't know how to build linux-`expr %{kernvers} : '\(^[0-9]*[.][0-9]*\)'`"
       exit 1
       ;;
esac
%else
kv='26'
%endif

case %{_arch} in
       x86_64)                         sysname=amd64_linux${kv}        ;;
       alpha*)                         sysname=alpha_linux_${kv}       ;;
       i386|i486|i586|i686|athlon)     sysname=i386_linux${kv}         ;;
       *)                              sysname=%{_arch}_linux${kv}     ;;
esac

# Build install tree
%if %{build_userspace}
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
mkdir -p $RPM_BUILD_ROOT%{_libdir}
mkdir -p $RPM_BUILD_ROOT/etc/sysconfig
%if 0%{?fedora} < 15 && 0%{?rhel} < 7
mkdir -p $RPM_BUILD_ROOT%{initdir}
%else
mkdir -p $RPM_BUILD_ROOT%{_unitdir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/modules
%endif
mkdir -p $RPM_BUILD_ROOT/etc/openafs
mkdir -p $RPM_BUILD_ROOT%{pamdir}
mkdir -p $RPM_BUILD_ROOT%{_prefix}/afs/etc
mkdir -p $RPM_BUILD_ROOT%{_prefix}/afs/logs
mkdir -p $RPM_BUILD_ROOT%{_prefix}/vice/etc
mkdir -p $RPM_BUILD_ROOT%{_prefix}/vice/cache
chmod 700 $RPM_BUILD_ROOT%{_prefix}/vice/cache
mkdir -p $RPM_BUILD_ROOT%{_mandir}

# Copy files from dest to the appropriate places in BuildRoot
tar cf - -C ${sysname}/dest bin include | tar xf - -C $RPM_BUILD_ROOT%{_prefix}
tar cf - -C ${sysname}/dest/lib . | tar xf - -C $RPM_BUILD_ROOT%{_libdir}
tar cf - -C ${sysname}/dest/etc . | tar xf - -C $RPM_BUILD_ROOT%{_sbindir}
tar cf - -C ${sysname}/dest/root.server%{_prefix}/afs bin | tar xf - -C $RPM_BUILD_ROOT%{_prefix}/afs
tar cf - -C ${sysname}/dest/root.client%{_prefix}/vice/etc afsd C | tar xf - -C $RPM_BUILD_ROOT%{_prefix}/vice/etc

# Set the executable bit on libraries in libdir, so rpmbuild knows to
# create "Provides" entries in the package metadata for the libraries
chmod +x $RPM_BUILD_ROOT%{_libdir}/*.so*

# Fix the location of restorevol, since it should be available for
# any user in /usr/bin
mv $RPM_BUILD_ROOT%{_prefix}/afs/bin/restorevol $RPM_BUILD_ROOT%{_bindir}/restorevol

# Link kpasswd to kapasswd
ln -f $RPM_BUILD_ROOT%{_bindir}/kpasswd $RPM_BUILD_ROOT%{_bindir}/kapasswd

# Copy root.client config files
install -m 755 src/packaging/RedHat/openafs.sysconfig $RPM_BUILD_ROOT/etc/sysconfig/openafs
%if 0%{?fedora} < 15 && 0%{?rhel} < 7
install -m 755 src/packaging/RedHat/openafs-client.init $RPM_BUILD_ROOT%{initdir}/openafs-client
install -m 755 src/packaging/RedHat/openafs-server.init $RPM_BUILD_ROOT%{initdir}/openafs-server
%else
install -m 755 src/packaging/RedHat/openafs-client.service $RPM_BUILD_ROOT%{_unitdir}/openafs-client.service
install -m 755 src/packaging/RedHat/openafs-client.modules $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/modules/openafs-client.modules
install -m 755 src/packaging/RedHat/openafs-server.service $RPM_BUILD_ROOT%{_unitdir}/openafs-server.service
%endif

# Copy PAM modules
install -m 755 ${sysname}/dest/lib/pam* $RPM_BUILD_ROOT%{pamdir}

# PAM symlinks
ln -sf pam_afs.so.1 $RPM_BUILD_ROOT%{pamdir}/pam_afs.so
ln -sf pam_afs.krb.so.1 $RPM_BUILD_ROOT%{pamdir}/pam_afs.krb.so

# Populate /usr/vice/etc
uve=$RPM_BUILD_ROOT%{_prefix}/vice/etc
install -p -m 644 src/packaging/RedHat/openafs-ThisCell $uve/ThisCell
install -p -m 644 %{SOURCE20} $uve/CellServDB.dist
install -p -m 644 src/packaging/RedHat/openafs-cacheinfo $uve/cacheinfo

#
# install dkms source
#
install -d -m 755 $RPM_BUILD_ROOT%{_prefix}/src
cp -a libafs_tree $RPM_BUILD_ROOT%{_prefix}/src/%{name}-%{dkms_version}

cat > $RPM_BUILD_ROOT%{_prefix}/src/%{name}-%{dkms_version}/dkms.conf <<"EOF"

PACKAGE_VERSION="%{dkms_version}"

# Items below here should not have to change with each driver version
PACKAGE_NAME="%{name}"
MAKE[0]='./configure --with-linux-kernel-headers=${kernel_source_dir} --with-linux-kernel-packaging && make && case "${kernelver_array[0]}${kernelver[0]}" in 2.4.*) mv src/libafs/MODLOAD-*/libafs-* openafs.o ;; *) mv src/libafs/MODLOAD-*/openafs.ko . ;; esac'
CLEAN="make -C src/libafs clean"

BUILT_MODULE_NAME[0]="$PACKAGE_NAME"
DEST_MODULE_LOCATION[0]="/kernel/3rdparty/$PACKAGE_NAME/"
STRIP[0]=no
AUTOINSTALL=yes

EOF

#
# install kernel-source
#

# Install the kernel module source tree
mkdir -p $RPM_BUILD_ROOT%{_prefix}/src/openafs-kernel-%{afsvers}/src
tar cf - -C libafs_tree . | \
	tar xf - -C $RPM_BUILD_ROOT%{_prefix}/src/openafs-kernel-%{afsvers}/src

# Next, copy the LICENSE Files, README
install -m 644 src/LICENSE $RPM_BUILD_ROOT%{_prefix}/src/openafs-kernel-%{afsvers}/LICENSE.IBM
install -m 644 src/packaging/RedHat/openafs-LICENSE.Sun $RPM_BUILD_ROOT%{_prefix}/src/openafs-kernel-%{afsvers}/LICENSE.Sun
install -m 644 src/packaging/RedHat/openafs-README $RPM_BUILD_ROOT%{_prefix}/src/openafs-kernel-%{afsvers}/README

#
# Install DOCUMENTATION
#

# Build the DOC directory
mkdir -p $RPM_BUILD_ROOT/$RPM_DOC_DIR/openafs-%{afsvers}
tar cf - -C doc LICENSE html pdf | \
    tar xf - -C $RPM_BUILD_ROOT/$RPM_DOC_DIR/openafs-%{afsvers}
install -m 644 %{SOURCE10} $RPM_BUILD_ROOT/$RPM_DOC_DIR/openafs-%{afsvers}
install -m 644 %{SOURCE11} $RPM_BUILD_ROOT/$RPM_DOC_DIR/openafs-%{afsvers}

#
# man pages
#
tar cf - -C doc/man-pages man1 man5 man8 | \
    tar xf - -C $RPM_BUILD_ROOT%{_mandir}

# Copy the uninstalled krb5 files (or delete the unused krb5 files)
%if %{krb5support}
mv $RPM_BUILD_ROOT%{_prefix}/afs/bin/asetkey $RPM_BUILD_ROOT%{_sbindir}/asetkey
%else
rm -f $RPM_BUILD_ROOT%{_mandir}/man8/asetkey.*
%endif

# remove unused man pages
for x in afs_ftpd afs_inetd afs_login afs_rcp afs_rlogind afs_rsh \
    dkload knfs package runntp symlink symlink_list symlink_make \
    symlink_remove; do
	rm -f $RPM_BUILD_ROOT%{_mandir}/man1/${x}.1
done

# rename kpasswd to kapasswd
mv $RPM_BUILD_ROOT%{_mandir}/man1/kpasswd.1 $RPM_BUILD_ROOT%{_mandir}/man1/kapasswd.1

# gzip man pages
gzip -9 $RPM_BUILD_ROOT%{_mandir}/man*/*

# create list of man pages that go in the 'openafs' package
/bin/ls $RPM_BUILD_ROOT%{_mandir}/man1 \
	|egrep '^afs|^fs|^kas|^klog|kapasswd|pagsh|^pts|^restorevol|^rxdebug|scout|^sys|tokens|translate|^xstat|udebug|unlog|^uss|^vos' \
	|egrep -v '^afs_compile_et' \
	>openafs-man1files

/bin/ls $RPM_BUILD_ROOT%{_mandir}/man5 \
	|egrep 'CellServDB|ThisCell|afsmonitor|^butc|^uss' \
	>openafs-man5files

/bin/ls $RPM_BUILD_ROOT%{_mandir}/man8 \
	|egrep '^backup|^bos|^butc|^fms|^fssync-debug|^fstrace|^kas|^read_tape|^uss' \
	>openafs-man8files

#
# create filelist
#
grep -v "^#" >openafs-file-list <<EOF-openafs-file-list
%{_bindir}/afsmonitor
%{_bindir}/bos
%{_bindir}/fs
%{_bindir}/kapasswd
%{_bindir}/klog
%{_bindir}/klog.krb
%{_bindir}/pagsh
%{_bindir}/pagsh.krb
%{_bindir}/pts
%{_bindir}/restorevol
%{_bindir}/scout
%{_bindir}/sys
%{_bindir}/tokens
%{_bindir}/tokens.krb
%{_bindir}/translate_et
%{_bindir}/xstat_cm_test
%{_bindir}/xstat_fs_test
%{_bindir}/udebug
%{_bindir}/unlog
%{_sbindir}/backup
%{_sbindir}/butc
%{_sbindir}/fms
%{_sbindir}/fstrace
%{_sbindir}/kas
%{_sbindir}/read_tape
%{_sbindir}/rxdebug
%{_sbindir}/uss
%{_sbindir}/vos
%{_sbindir}/vsys
EOF-openafs-file-list

# add man pages to the list
cat openafs-man1files \
	| ( while read x; do echo "%{_mandir}/man1/$x"; done ) \
	>>openafs-file-list
cat openafs-man5files \
	| ( while read x; do echo "%{_mandir}/man5/$x"; done ) \
	>>openafs-file-list
cat openafs-man8files \
	| ( while read x; do echo "%{_mandir}/man8/$x"; done ) \
	>>openafs-file-list

#
# Install compatiblity links
#
for d in bin:bin etc:sbin; do
  olddir=`echo $d | sed 's/:.*$//'`
  newdir=`echo $d | sed 's/^.*://'`
  mkdir -p $RPM_BUILD_ROOT%{_prefix}/afsws/$olddir
  for f in `cat openafs-file-list`; do
    if echo $f | grep -q /$newdir/; then
      fb=`basename $f`
      ln -sf %{_prefix}/$newdir/$fb $RPM_BUILD_ROOT%{_prefix}/afsws/$olddir/$fb
    fi
  done
done

#
# Remove files we're not installing
#

# remove duplicated files from /usr/afs/bin
for f in bos fs kas klog klog.krb kpwvalid pts tokens tokens.krb udebug vos ; do
  rm -f $RPM_BUILD_ROOT%{_prefix}/afs/bin/$f
done

# the rest are not needed.
for f in dlog dpass install knfs livesys ; do
  rm -f $RPM_BUILD_ROOT%{_bindir}/$f
done

# not supported on Linux or duplicated
for f in kdb rmtsysd kpwvalid ; do
  rm -f $RPM_BUILD_ROOT%{_sbindir}/$f
done
# sometimes install sucks and puts down a directory. kill it all.
rm -rf $RPM_BUILD_ROOT%{_sbindir}/kdump*

# remove man pages from programs deleted above
for f in 1/dlog 1/copyauth 1/dpass 1/livesys 8/rmtsysd 8/aklog_dynamic_auth 8/kdb 8/kpwvalid 8/xfs_size_check 1/package_test 5/package 8/package ; do
  rm -f $RPM_BUILD_ROOT%{_mandir}/man$f.*
done

# PAM modules are doubly-installed  Remove the version we don't need
for f in pam_afs.krb.so.1 pam_afs.so.1 ; do
  rm -f $RPM_BUILD_ROOT%{_libdir}/$f
done

%if !%{build_authlibs}
rm -f $RPM_BUILD_ROOT%{_libdir}/libafsauthent.so
rm -f $RPM_BUILD_ROOT%{_libdir}/libafsrpc.so
rm -f $RPM_BUILD_ROOT%{_libdir}/libafsauthent.so.*
rm -f $RPM_BUILD_ROOT%{_libdir}/libafsrpc.so.*
%endif

%endif

%if %{build_modules}
%if %{fedorakmod}
for kvariant in %{kvariants}
do
  if [ -n "$kvariant" ] ; then
    if [ -d _kmod_build_$kvariant/src/libafs/MODLOAD-%{kverrel}${kvariant}-SP ] ; then
      srcdir=_kmod_build_$kvariant/src/libafs/MODLOAD-%{kverrel}${kvariant}-SP
      dstdir=$RPM_BUILD_ROOT/lib/modules/%{kverrel}${kvariant}/extra/openafs
    elif [ -d _kmod_build_$kvariant/src/libafs/MODLOAD-%{kverrel}.%{_target_cpu}+${kvariant}-SP ] ; then
      srcdir=_kmod_build_$kvariant/src/libafs/MODLOAD-%{kverrel}.%{_target_cpu}+${kvariant}-SP
      dstdir=$RPM_BUILD_ROOT/lib/modules/%{kverrel}.%{_target_cpu}+${kvariant}/extra/openafs
    else
      srcdir=_kmod_build_$kvariant/src/libafs/MODLOAD-%{kverrel}.%{_target_cpu}.${kvariant}-SP
      dstdir=$RPM_BUILD_ROOT/lib/modules/%{kverrel}.%{_target_cpu}.${kvariant}/extra/openafs
    fi
  else
    if [ -d ${sysname}/dest/root.client/lib/modules/%{kverrel}/extra/openafs ] ; then
      srcdir=${sysname}/dest/root.client/lib/modules/%{kverrel}/extra/openafs
      dstdir=$RPM_BUILD_ROOT/lib/modules/%{kverrel}/extra/openafs
    else
      srcdir=${sysname}/dest/root.client/lib/modules/%{kverrel}.%{_target_cpu}/extra/openafs
      dstdir=$RPM_BUILD_ROOT/lib/modules/%{kverrel}.%{_target_cpu}/extra/openafs
    fi
  fi

  mkdir -p ${dstdir}
  install -m 755 ${srcdir}/openafs.ko ${dstdir}/openafs.ko
done
%else
# Install the kernel modules
for variation in %{kvariations}
do
    if [ ${variation} = up ]
    then
       kvar=%{kxmoddir}
       modname=openafs${kmodend}
    else
       kvar=%{kxmoddir}${variation}
       modname=openafs${kmodend}
    fi

    srcdir=${sysname}/dest/root.client/lib/modules/%{kverrel}${kvariant}/extra/openafs
    dstdir=$RPM_BUILD_ROOT${kvar}/fs/openafs

    mkdir -p ${dstdir}

    install -m 755 ${srcdir}/${modname} ${dstdir}/openafs${kmodend}
done
%endif
%endif

##############################################################################
###
### clean
###
##############################################################################
%clean
rm -f openafs-file-list
[ "$RPM_BUILD_ROOT" != "/" -a "x%{debugspec}" != "x1" ] && \
	rm -fr $RPM_BUILD_ROOT


##############################################################################
###
### scripts
###
##############################################################################
%if %{build_userspace}

%pre compat
if [ -e %{_prefix}/afsws ]; then
        /bin/rm -fr %{_prefix}/afsws
fi

%post client
%if 0%{?fedora} < 15 && 0%{?rhel} < 7
chkconfig --add openafs-client
%else
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
%endif
if [ ! -d /afs ]; then
	mkdir /afs
	chown root.root /afs
	chmod 0755 /afs
	[ -x /sbin/restorecon ] && /sbin/restorecon /afs
fi

# Create the CellServDB
[ -f /usr/vice/etc/CellServDB.local ] || touch /usr/vice/etc/CellServDB.local

( cd /usr/vice/etc ; \
  cat CellServDB.local CellServDB.dist > CellServDB ; \
  chmod 644 CellServDB )

%post server
#on an upgrade, don't enable if we were disabled
%if 0%{?fedora} < 15 && 0%{?rhel} < 7
if [ $1 = 1 ] ; then
  chkconfig --add openafs-server
fi
%{initdir}/openafs-server condrestart
%else
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
%endif

%if %{build_authlibs}
%post authlibs
/sbin/ldconfig

%postun authlibs
/sbin/ldconfig
%endif

%preun
if [ $1 = 0 ] ; then
	[ -d /afs ] && rmdir /afs
	:
fi

%preun client
%if 0%{?fedora} < 15 && 0%{?rhel} < 7
if [ $1 = 0 ] ; then
        %{initdir}/openafs-client stop
        chkconfig --del openafs-client
fi
%else
if [ $1 -eq 0 ] ; then
    	# Package removal, not upgrade
    	/bin/systemctl --no-reload disable openafs-client.service > /dev/null 2>&1 || :
    	/bin/systemctl stop openafs-client.service > /dev/null 2>&1 || :
fi
%endif

%preun server
%if 0%{?fedora} < 15 && 0%{?rhel} < 7
if [ $1 = 0 ] ; then
        %{initdir}/openafs-server stop
        chkconfig --del openafs-server
fi
%else
if [ $1 -eq 0 ] ; then
    	/bin/systemctl --no-reload disable openafs-server.service > /dev/null 2>&1 || :
    	/bin/systemctl stop openafs-server.service > /dev/null 2>&1 || :
fi
%endif

%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
%postun client
/bin/systemctl daemon-reload >/dev/null 2>&1 || :

%postun server
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
%endif

%if %{build_dkmspkg}
%post -n dkms-%{name}
dkms add -m %{name} -v %{dkms_version} --rpm_safe_upgrade
dkms build -m %{name} -v %{dkms_version} --rpm_safe_upgrade
dkms install -m %{name} -v %{dkms_version} --rpm_safe_upgrade

%preun -n dkms-%{name}
dkms remove -m %{name} -v %{dkms_version} --rpm_safe_upgrade --all ||:
%endif
%endif

%if %{build_modules}
%if !%{fedorakmod}
%if %{up_package}
%post kernel
/sbin/depmod -ae %{kernvers}

%postun kernel
/sbin/depmod -ae %{kernvers}

%endif

%if %{smp_package}
%post kernel-smp
/sbin/depmod -ae %{kernvers}%{?smp_ext:%{smp_ext}}

%postun kernel-smp
/sbin/depmod -ae %{kernvers}%{?smp_ext:%{smp_ext}}
%endif

%if %{largesmp_package}
%post kernel-largesmp
/sbin/depmod -ae %{kernvers}%{?largesmp_ext:%{largesmp_ext}}

%postun kernel-largesmp
/sbin/depmod -ae %{kernvers}%{?largesmp_ext:%{largesmp_ext}}
%endif
 
%if %{bigmem_package}
%post kernel-bigmem
/sbin/depmod -ae %{kernvers}%{?bigmem_ext:%{bigmem_ext}}

%postun kernel-bigmem
/sbin/depmod -ae %{kernvers}%{?bigmem_ext:%{bigmem_ext}}
%endif

%if %{hugemem_package}
%post kernel-hugemem
/sbin/depmod -ae %{kernvers}%{?hugemem_ext:%{hugemem_ext}}

%postun kernel-hugemem
/sbin/depmod -ae %{kernvers}%{?hugemem_ext:%{hugemem_ext}}
%endif
%endif
%endif

%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
%triggerun -- openafs-client < 1.6.0-1
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply httpd
# to migrate them to systemd targets
/usr/bin/systemd-sysv-convert --save openafs-client >/dev/null 2>&1 ||:

# Run this because the SysV package being removed won't do it
/sbin/chkconfig --del openafs-client >/dev/null 2>&1 || :

%triggerun -- openafs-server < 1.6.0-1
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply httpd
# to migrate them to systemd targets
/usr/bin/systemd-sysv-convert --save openafs-server >/dev/null 2>&1 ||:

# Run this because the SysV package being removed won't do it
/sbin/chkconfig --del openafs-server >/dev/null 2>&1 || :
%endif

##############################################################################
###
### file lists
###
##############################################################################
%if %{build_userspace}

%files -f openafs-file-list
%defattr(-,root,root)
%config(noreplace) /etc/sysconfig/openafs
%doc %{_docdir}/openafs-%{afsvers}/LICENSE

%files docs
%defattr(-,root,root)
%docdir %{_docdir}/openafs-%{afsvers}
%dir %{_docdir}/openafs-%{afsvers}
%{_docdir}/openafs-%{afsvers}/ChangeLog
%{_docdir}/openafs-%{afsvers}/RELNOTES-%{afsvers}
%{_docdir}/openafs-%{afsvers}/pdf

%files client
%defattr(-,root,root)
%dir %{_prefix}/vice
%dir %{_prefix}/vice/cache
%dir %{_prefix}/vice/etc
%dir %{_prefix}/vice/etc/C
%{_prefix}/vice/etc/CellServDB.dist
%config(noreplace) %{_prefix}/vice/etc/ThisCell
%config(noreplace) %{_prefix}/vice/etc/cacheinfo
%{_bindir}/afsio
%{_bindir}/cmdebug
%{_bindir}/up
%{_prefix}/vice/etc/afsd
%{_prefix}/vice/etc/C/afszcm.cat
%{pamdir}/pam_afs.krb.so.1
%{pamdir}/pam_afs.krb.so
%{pamdir}/pam_afs.so.1
%{pamdir}/pam_afs.so
%if 0%{?fedora} < 15 && 0%{?rhel} < 7
%{initdir}/openafs-client
%else
%{_unitdir}/openafs-client.service
%{_sysconfdir}/sysconfig/modules/openafs-client.modules
%endif
%{_mandir}/man1/cmdebug.*
%{_mandir}/man1/up.*
%{_mandir}/man5/afs.5.gz
%{_mandir}/man5/afs_cache.5.gz
%{_mandir}/man5/afs_volume_header.5.gz
%{_mandir}/man5/afszcm.cat.5.gz
%{_mandir}/man5/cacheinfo.*
%{_mandir}/man8/afsd.*
%{_mandir}/man8/vsys.*
%{_mandir}/man5/CellAlias.*

%files server
%defattr(-,root,root)
%dir %{_prefix}/afs
%dir %{_prefix}/afs/bin
%dir %{_prefix}/afs/etc
%dir %{_prefix}/afs/logs
%{_prefix}/afs/bin/bosserver
%{_prefix}/afs/bin/bos_util
%{_prefix}/afs/bin/buserver
%{_prefix}/afs/bin/dafileserver
%{_prefix}/afs/bin/dafssync-debug
%{_prefix}/afs/bin/dasalvager
%{_prefix}/afs/bin/davolserver
%{_prefix}/afs/bin/fileserver
%{_prefix}/afs/bin/fssync-debug
# Should we support KAServer?
%{_prefix}/afs/bin/kaserver
%{_prefix}/afs/bin/ka-forwarder
%{_prefix}/afs/bin/pt_util
%{_prefix}/afs/bin/ptserver
%{_prefix}/afs/bin/salvager
%{_prefix}/afs/bin/salvageserver
%{_prefix}/afs/bin/salvsync-debug
%{_prefix}/afs/bin/state_analyzer
%{_prefix}/afs/bin/upclient
%{_prefix}/afs/bin/upserver
%{_prefix}/afs/bin/vlserver
%{_prefix}/afs/bin/volinfo
%{_prefix}/afs/bin/volserver
%{_sbindir}/kadb_check
%{_sbindir}/prdb_check
%{_sbindir}/vldb_check
%{_sbindir}/vldb_convert
%{_sbindir}/voldump
%if 0%{?fedora} < 15 && 0%{?rhel} < 7
%{initdir}/openafs-server
%else
%{_unitdir}/openafs-server.service
%endif
%{_mandir}/man5/AuthLog.*
%{_mandir}/man5/BackupLog.*
%{_mandir}/man5/BosConfig.*
%{_mandir}/man5/BosLog.*
%{_mandir}/man5/FORCESALVAGE.*
%{_mandir}/man5/FileLog.*
%{_mandir}/man5/KeyFile.*
%{_mandir}/man5/NetInfo.*
%{_mandir}/man5/NetRestrict.*
%{_mandir}/man5/NoAuth.*
%{_mandir}/man5/SALVAGE.fs.*
%{_mandir}/man5/SalvageLog.*
%{_mandir}/man5/sysid.*
%{_mandir}/man5/UserList.*
%{_mandir}/man5/VLLog.*
%{_mandir}/man5/VolserLog.*
%{_mandir}/man5/bdb.DB0.*
%{_mandir}/man5/fms.log.*
%{_mandir}/man5/kaserver.DB0.*
%{_mandir}/man5/kaserverauxdb.*
%{_mandir}/man5/krb.conf.*
%{_mandir}/man5/krb.excl.*
%{_mandir}/man5/prdb.DB0.*
%{_mandir}/man5/salvage.lock.*
%{_mandir}/man5/tapeconfig.*
%{_mandir}/man5/vldb.DB0.*
%{_mandir}/man8/buserver.*
%{_mandir}/man8/fileserver.*
%{_mandir}/man8/dafileserver.*
%{_mandir}/man8/dasalvager.*
%{_mandir}/man8/davolserver.*
%{_mandir}/man8/kadb_check.*
%{_mandir}/man8/ka-forwarder.*
%{_mandir}/man8/prdb_check.*
%{_mandir}/man8/ptserver.*
%{_mandir}/man8/pt_util.*
%{_mandir}/man8/salvager.*
%{_mandir}/man8/salvageserver.*
%{_mandir}/man8/state_analyzer.*
%{_mandir}/man8/upclient.*
%{_mandir}/man8/upserver.*
%{_mandir}/man8/vldb_check.*
%{_mandir}/man8/vldb_convert.*
%{_mandir}/man8/vlserver.*
%{_mandir}/man8/voldump.*
%{_mandir}/man8/volinfo.*
%{_mandir}/man8/volserver.*

%if %{build_authlibs}
%files authlibs
%defattr(-,root,root)
%{_libdir}/libafsauthent.so.*
%{_libdir}/libafsrpc.so.*
%{_libdir}/libkopenafs.so.*
%endif

%files authlibs-devel
%defattr(-,root,root)
%{_includedir}/kopenafs.h
%{_libdir}/libafsauthent.a
%{_libdir}/libafscp.a
%{_libdir}/libafsrpc.a
%{_libdir}/libafsauthent_pic.a
%{_libdir}/libafsrpc_pic.a
%{_libdir}/libkopenafs.a
%if %{build_authlibs}
%{_libdir}/libafsauthent.so
%{_libdir}/libafsrpc.so
%{_libdir}/libkopenafs.so
%endif

%files devel
%defattr(-,root,root)
%{_bindir}/afs_compile_et
%{_bindir}/rxgen
%{_includedir}/afs
%{_includedir}/des.h
%{_includedir}/des_conf.h
%{_includedir}/des_odd.h
%{_includedir}/des_prototypes.h
%{_includedir}/lock.h
%{_includedir}/lwp.h
%{_includedir}/mit-cpyright.h
%{_includedir}/preempt.h
%{_includedir}/rx
%{_includedir}/timer.h
%{_includedir}/ubik.h
%{_includedir}/ubik_int.h
%{_libdir}/afs
%{_libdir}/libdes.a
%{_libdir}/liblwp.a
%{_libdir}/librx.a
%{_libdir}/librxkad.a
%{_libdir}/librxstat.a
%{_libdir}/libubik.a
%{_mandir}/man1/rxgen.*
%{_mandir}/man1/afs_compile_et.*

%if %{build_dkmspkg}
%files -n dkms-%{name}
%defattr(-,root,root)
%{_prefix}/src/%{name}-%{dkms_version}
%endif

%files kernel-source
%defattr(-,root,root)
%{_prefix}/src/openafs-kernel-%{afsvers}/LICENSE.IBM
%{_prefix}/src/openafs-kernel-%{afsvers}/LICENSE.Sun
%{_prefix}/src/openafs-kernel-%{afsvers}/README
%{_prefix}/src/openafs-kernel-%{afsvers}/src

%files compat
%defattr(-,root,root)
%{_prefix}/afsws

%files kpasswd
%defattr(-,root,root)
%{_bindir}/kpasswd
%{_bindir}/kpwvalid

%if %{krb5support}
%files krb5
%defattr(-,root,root)
%{_bindir}/aklog
%{_bindir}/klog.krb5
%{_sbindir}/asetkey
%{_mandir}/man1/aklog.*
%{_mandir}/man8/asetkey.*
%endif

%endif

%if %{build_modules}

%if !%{fedorakmod}
%if %{up_package}
%files kernel
%defattr(-,root,root)
%{kxmoddir}/fs/openafs/openafs.*
%endif

%if %{smp_package}
%files kernel-smp
%defattr(-,root,root)
%{kxmoddir}%{?smp_ext:%{smp_ext}}/fs/openafs/openafs.*
%endif

%if %{largesmp_package}
%files kernel-largesmp
%defattr(-,root,root)
%{kxmoddir}%{?largesmp_ext:%{largesmp_ext}}/fs/openafs/openafs.*
%endif
 
%if %{bigmem_package}
%files kernel-bigmem
%defattr(-,root,root)
%{kxmoddir}%{?bigmem_ext:%{bigmem_ext}}/fs/openafs/openafs.*
%endif

%if %{hugemem_package}
%files kernel-hugemem
%defattr(-,root,root)
%{kxmoddir}%{?hugemem_ext:%{hugemem_ext}}/fs/openafs/openafs.*
%endif
%endif

%endif

##############################################################################
###
### openafs.spec change log
###
##############################################################################
%changelog
* Wed Dec 12 2007  Simon Wilkinson <simon@sxw.org.uk> 1.4.5
- Make the RPM mockable

* Mon Oct 29 2007  Simon Wilkinson <simon@sxw.org.uk> 1.4.5
- Update to match the shipped 1.4.5 RPMS
- Fix the kvariant stuff to only configure the 'standard' case once
- Add openafs-kvers.sh back in

* Wed Oct 10 2007  Simon Wilkinson <simon@sxw.org.uk> 1.4.5pre1-1
- Use Fedora style kmods, which allows us to install multiple kernel types

* Thu Jun 07 2007  Simon Wilkinson <simon@sxw.org.uk> 1.4.4-3
- Use distributed files, rather than those in packager's SOURCE directory
- Remove SuidCells stuff, which was unused

* Fri Dec 01 2006  Derrick Brashear <shadow@dementia.org> 1.4.2-2
- integrate s390x changes
- allow for building libafs*.a and not libafs*.so into packages, for platforms
  that won't build the .so files.

* Wed Aug 23 2006  Derrick Brashear <shadow@dementia.org> 1.4.2-1
- update to 1.4.2
- use installed aklog manpage.
- moduleparam patch obsoleted.

* Tue Aug 22 2006  Derek Atkins <warlord@MIT.EDU> 1.4.2-0.1.rc1
- update to 1.4.2-rc1
- hand-apply lee damon's changes to support largesmp kernels from RHEL4
  (but only add support for 2.6 kernels.  No need for the 2.4 kernels).
- don't need the posixlock patch anymore.

* Wed Jul 12 2006  Derek Atkins <warlord@MIT.EDU> 1.4.2-0.beta2
- update to 1.4.2-beta2
- add linux2.4 posixlock API patch

* Mon Jun 26 2006  Derek Atkins <warlord@MIT.EDU>
- moduleparam and krb524 patches no longer required in OA-CVS

* Wed May 17 2006  Derek Atkins <warlord@MIT.EDU>
- change non-target-cpu kernel dep to a file dep
- make sure we use the proper kernel version for the dependency.

* Tue May 16 2006  Derek Atkins <warlord@MIT.EDU>
- allow users to specify local CellServDB and SuidCells entries
  don't overwrite user's changes.  Provide a .dist an let users
  make entries in a ".local"
- build the CellServDB and SuidCells at client startup and at
  client install-time
- add provideskernelarch functionality to openafs-kvers-is.sh
- use that functionality to Require kernel{,-<type>}-targetcpu
  to get better package safety due to RPM bugs where the kernel
  release isn't used so you can install the kernel module against
  any kernel of the same major version.

* Mon May 15 2006  Derek Atkins <warlord@MIT.EDU>
- update the README in openafs-kernel-source
- fix openafs-kvers-is.sh from Alexander Bergolth's patch.
- move kernel module from .../kernel/fs/openafs to .../fs/openafs/

* Fri Apr 21 2006  Derek Atkins <warlord@MIT.EDU>
- build requires autoconf and automake for krb5support
  and autoconf for standard package
- dont setup the krb5 migration kit (or patches) if we don't care.
- require ncurses-devel to build

* Wed Apr 19 2006  Derek Atkins <warlord@MIT.EDU> 1.4.1-3
- look for krb524 functions in libkrb524 if we can't find them
  in the standard locations.

* Tue Apr 18 2006  Derek Atkins <warlord@MIT.EDU> 1.4.1-2
- fix the module_param_array macro for Linux 2.6.9.

* Sat Apr 15 2006  Derek Atkins <warlord@MIT.EDU> 1.4.1-1
- update to 1.4.1 release.
- distribute asetkey from openafs instead of krb5-migration kit
- don't need to apply the FC5 patches because they are part of the distro.
- install asetkey into the "proper" place
- dont list a manpage twice.
- package asetkey man page.  delete it when not needed.

* Thu Apr  6 2006  Derek Atkins <warlord@MIT.EDU>
- turn authlibs back on, because RT #18767 was applied to CVS.

* Wed Mar 29 2006  Derek Atkins <warlord@MIT.EDU> 1.4.1rc10-1
- update to 1.4.1rc10, build on FC5
- fix the man pages (distribute into various packages)
- include patches for FC5, RT #29112 and #29122

* Mon Dec 19 2005  Derek Atkins <warlord@MIT.EDU>
- openafs-server shouldn't depend on the kernel module.

* Thu Nov 17 2005  Derek Atkins <warlord@MIT.EDU>
- patch from Mike Polek <mike at pictage.com> to run depmod for
  the target kernel and not the running kernel.

* Tue Nov  8 2005  Derek Atkins <warlord@MIT.EDU>
- build aklog from the openafs sources, not from the krb5 migration kit.

* Fri Nov  4 2005  Derek Atkins <warlord@MIT.EDU>
- set openafs-kernel-source to Provide openafs-kernel

* Thu Oct 20 2005  Derek Atkins <warlord@MIT.EDU> 1.4.0-1
- update afs-krb5 res_search patch: look for res_search and __res_search
- update to 1.4.0 final

* Mon Oct 10 2005  Derek Atkins <warlord@MIT.EDU>
- remove all kdump builds.

* Thu Oct  6 2005  Derek Atkins <warlord@MIT.EDU>
- fix openafs-kernel-version.sh so it will build an RPM for the
  currently-running kernel even if it's smp on 2.6.

* Tue Sep 27 2005  Derek Atkins <warlord@MIT.EDU> 1.4.0rc5-1
- upgrade to 1.4.0rc5
- turn off authlibs packages

* Fri Sep 23 2005  Derek Atkins <warlord@MIT.EDU> 1.4.0rc4-2
- add kmodule26 patch: fix the kernel module name on 2.6 kernels so
  it's called "openafs" and not "libafs".  This fixes the shutdown
  problem.

* Thu Sep 22 2005  Derek Atkins <warlord@MIT.EDU>
- update kversis script, add 'kvers' operation
- fix bug that 2.6 smp/hugemem kernels don't provide
  kernel-foo = %{kernvers} with 'smp', 'hugemem', etc.
- add patch to remove res_search from the afs-krb5 configure

* Thu Sep 15 2005  Derek Atkins <warlord@MIT.EDU> 1.4.0rc4-1
- Update to 1.4.0rc4
- Update the afs-krb5 krb524 patch so it actually works on
  some older systems like RHEL3 that still need -lkrb524.
- Update the buildall script so choose better architecture support,
  e.g. don't build i586 on RHEL.
- Update the rebuild information in the SPEC file.
- Add support for finding .EL kernels in openafs-kvers-is.sh
- Add additional error messages when kernel version/type parsing fails.
- Update the buildall script to use the kernel srcdir directly.

* Wed Sep 14 2005  Derek Atkins <warlord@MIT.EDU> 1.4.0rc3-2
- Add "hugemem" to 2.4 configs
- Add checks to support scripts to determine whether to build
  the bigmem and/or hugemem kernels for 2.4.

* Mon Sep 12 2005  Derek Atkins <warlord@MIT.EDU> 1.4.0rc3-1
- Added some afs-krb5 patches to get the migration kit to build
  on modern AFS and modern Kerberos.
- Added authlibs and authlibs-devel packages as per UMich changes.

* Sun Sep 11 2005  Derek Atkins <warlord@MIT.EDU>
- Merged in some of the 2.6 changes from wingc@engin.umich.edu

* Sat Sep 10 2005  Derek Atkins <warlord@MIT.EDU>
- Merged in lots of changes from David Howells and Nalin Dahyabhai
  from Red Hat.   Initial attempt at a release of 1.4.  Still need
  to work in a 2.6 build system.
