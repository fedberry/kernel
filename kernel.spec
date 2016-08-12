# We have to override the new %%install behavior because, well... the kernel is special.
%global __spec_install_pre %{___build_pre}

# For a stable, released kernel, released_kernel should be 1. For rawhide
# and/or a kernel built from an rc or git snapshot, released_kernel should
# be 0.
%global released_kernel 1


# baserelease defines which build revision of this kernel version we're
# building.  We used to call this fedora_build, but the magical name
# baserelease is matched by the rpmdev-bumpspec tool, which you should use.
#
# We used to have some extra magic weirdness to bump this automatically,
# but now we don't.  Just use: rpmdev-bumpspec -c 'comment for changelog'
# When changing base_sublevel below or going from rc to a final kernel,
# reset this by hand to 1 (or to 0 and then use rpmdev-bumpspec).
# scripts/rebase.sh should be made to do that for you, actually.
#
# NOTE: baserelease must be > 0 or bad things will happen if you switch
#       to a released kernel (released version will be < rc version)
#
# For non-released -rc kernels, this will be appended after the rcX and
# gitX tags, so a 3 here would become part of release "0.rcX.gitX.3"
#
%global baserelease 1
%global fedora_build %{baserelease}

# base_sublevel is the kernel version we're starting with and patching
# on top of -- for example, 3.1-rc7-git1 starts with a 3.0 base,
# which yields a base_sublevel of 0.
%define base_sublevel 5

## If this is a released kernel ##
%if 0%{?released_kernel}

# Do we have a -stable update to apply?
%define stable_update 7
# Set rpm version accordingly
%if 0%{?stable_update}
%define stablerev %{stable_update}
%define stable_base %{stable_update}
%endif
%define rpmversion 4.%{base_sublevel}.%{stable_update}

## The not-released-kernel case ##
%else
# The next upstream release sublevel (base_sublevel+1)
%define upstream_sublevel %(echo $((%{base_sublevel} + 1)))
# The rc snapshot level
%define rcrev 0
# The git snapshot level
%define gitrev 0
# Set rpm version accordingly
%define rpmversion 4.%{upstream_sublevel}.0
%endif
# Nb: The above rcrev and gitrev values automagically define Source1 and Source2 below.

# What parts do we want to build?  We must build at least one kernel.
# These are the kernels that are built IF the architecture allows it.
# All should default to 1 (enabled) and be flipped to 0 (disabled)
# by later arch-specific checks.

# The following build options are enabled by default.
# Use either --without <opt> in your rpmbuild command or force values
# to 0 in here to disable them.
#

# kernel-headers
%define with_headers   %{?_without_headers:   0} %{?!_without_headers:   1}
# perf
%define with_perf      %{?_without_perf:      0} %{?!_without_perf:      1}
# tools
%define with_tools     %{?_without_tools:     0} %{?!_without_tools:     1}
# kernel-debuginfo
%define with_debuginfo %{?_without_debuginfo: 1} %{?!_without_debuginfo: 0}


#
# Additional options for user-friendly one-off kernel building:
#
# Only build the base kernel (--with baseonly):
%define with_baseonly   %{?_with_baseonly:      1} %{?!_with_baseonly:     0}
#
# Cross compile requested?
%define with_cross      %{?_with_cross:         1} %{?!_with_cross:        0}
#
# build a release kernel on rawhide
%define with_release    %{?_with_release:       1} %{?!_with_release:      0}

# Want to build a vanilla kernel build without any non-upstream patches?
%define with_vanilla    %{?_with_vanilla:       1} %{?!_with_vanilla: 0}

# Build the RPi bcm2709 linux kernel port
%define with_bcm2709    %{?_without_bcm2709:    0} %{?!_without_bcm2709: 1}


%if 0%{!?nopatches:1}
%define nopatches 0
%endif

%if %{with_vanilla}
%define nopatches 1
%endif

%if %{nopatches}
%define variant -vanilla
%endif

%define bcm270x 0

%if %{with_bcm2709}
%define bcm270x 1
%define rpi_gitshort 2374021
%define Flavour bcm2709
%define buildid .%{rpi_gitshort}.%{Flavour}
%endif

%if ! %{bcm270x}
%define Flavour bcm283x
%define buildid .%{Flavour}
%endif


# pkg_release is what we'll fill in for the rpm Release: field
%define pkg_release %{fedora_build}%{?buildid}%{?dist}


# The kernel tarball/base version
%define kversion 4.%{base_sublevel}

%define make_target bzImage
%define kernel_image arch/arm/boot/zImage
%define KVERREL %{version}-%{release}.%{_target_cpu}
%define asmarch arm
%define hdrarch arm
%define image_install_path boot
# http://lists.infradead.org/pipermail/linux-arm-kernel/2012-March/091404.html
%define kernel_mflags KALLSYMS_EXTRA_PASS=1


# Overrides for generic default options

# don't build noarch kernels or headers (duh)
%ifarch noarch
%define with_headers 0
%define with_tools 0
%define with_perf 0
%endif


# Should make listnewconfig fail if there's config options
# printed out?
%if %{nopatches}
%define listnewconfig_fail 0
%else
%define listnewconfig_fail 1
%endif

#
# Packages that need to be installed before the kernel is, because the %%post
# scripts use them.
#
%define kernel_prereq  fileutils, systemd >= 203-2
%define initrd_prereq  dracut >= 027


Name: kernel%{?variant}
Group: System Environment/Kernel
License: GPLv2 and Redistributable, no modification permitted
%if !%{bcm270x}
Summary: The Linux kernel for the Raspberry Pi (BCM283x)
URL: http://www.kernel.org
%else
Summary: The BCM270x Linux kernel port for the Raspberry Pi 2 and 3
URL: https://github.com/raspberrypi/linux
%endif
Version: %{rpmversion}
Release: %{pkg_release}
ExclusiveArch: %{arm}
ExclusiveOS: Linux
Requires: kernel-core-uname-r = %{KVERREL}%{?variant}
Requires: kernel-modules-uname-r = %{KVERREL}%{?variant}


#
# List the packages used during the kernel build
#
BuildRequires: kmod, patch, bash, sh-utils, tar
BuildRequires: bzip2, xz, findutils, gzip, m4, perl, perl-Carp, make, diffutils, gawk
BuildRequires: gcc, binutils, redhat-rpm-config, hmaccalc
BuildRequires: net-tools, hostname, bc

%if %{with_perf}
BuildRequires: elfutils-devel zlib-devel binutils-devel newt-devel python-devel perl(ExtUtils::Embed) bison flex
BuildRequires: audit-libs-devel
%endif
%if %{with_tools}
BuildRequires: pciutils-devel gettext ncurses-devel
%endif
BuildConflicts: rhbuildsys(DiskFree) < 500Mb
%if %{with_debuginfo}
BuildRequires: rpm-build, elfutils
%define debuginfo_args --strict-build-id -r
%endif

%if %{with_cross}
BuildRequires: binutils-%{_build_arch}-linux-gnu, gcc-%{_build_arch}-linux-gnu
%define cross_opts CROSS_COMPILE=%{_build_arch}-linux-gnu-
%endif

Source0: ftp://ftp.kernel.org/pub/linux/kernel/v4.x/linux-%{kversion}.tar.xz
Source10: perf-man-%{kversion}.tar.gz
Source16: mod-extra.list
Source17: mod-extra.sh
Source99: filter-modules.sh

# kernel config modifications 
Source1000: bcm2709.cfg
Source1100: bcm283x.config

# Sources for kernel-tools
Source2000: cpupower.service
Source2001: cpupower.config

# Here should be only the patches up to the upstream canonical Linus tree.

# For a stable release kernel
%if 0%{?stable_update}
%if 0%{?stable_base}
Source1: ftp://ftp.kernel.org/pub/linux/kernel/v4.x/patch-4.%{base_sublevel}.%{stable_base}.xz
%endif

# non-released_kernel case
# These are automagically defined by the rcrev and gitrev values set up
# near the top of this spec file.
%else
%if 0%{?rcrev}
Source1: ftp://ftp.kernel.org/pub/linux/kernel/v4.x/patch-4.%{upstream_sublevel}-rc%{rcrev}.xz
%if 0%{?gitrev}
Source2: ftp://ftp.kernel.org/pub/linux/kernel/v4.x/patch-4.%{upstream_sublevel}-rc%{rcrev}-git%{gitrev}.xz
%endif
%else
# pre-{base_sublevel+1}-rc1 case
%if 0%{?gitrev}
Source1: ftp://ftp.kernel.org/pub/linux/kernel/v4.x/patch-4.%{base_sublevel}-git%{gitrev}.xz
%endif
%endif
%endif

# we also need compile fixes for -vanilla
#Patch04: compile-fixes.patch


%if !%{nopatches}

%if !%{bcm270x}
#script for adding device tree trailer to the kernel img
Patch10: add_mkknlimg_knlinfo.patch
%else
# RasperryPi patch
Patch100: patch-linux-rpi-4.5.y-%{rpi_gitshort}.xz
%endif

# END OF PATCH DEFINITIONS
%endif

BuildRoot: %{_tmppath}/kernel-%{KVERREL}-root

%description
The kernel meta package

#
# This macro does requires, provides, conflicts, obsoletes for a kernel package.
#	%%kernel_reqprovconf <subpackage>
# It uses any kernel_<subpackage>_conflicts and kernel_<subpackage>_obsoletes
# macros defined above.
#
%define kernel_reqprovconf \
Provides: kernel = %{rpmversion}-%{pkg_release}\
Provides: kernel-%{_target_cpu} = %{rpmversion}-%{pkg_release}%{?1:+%{1}}\
Provides: kernel-drm-nouveau = 16\
Provides: kernel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires(pre): %{kernel_prereq}\
Requires(pre): %{initrd_prereq}\
Requires(pre): linux-firmware >= 20130724-29.git31f6b30\
Requires(pre): bcm283x-firmware >= 20150909\
Requires(pre): raspberrypi-vc-utils >= 20160321\
Requires(preun): systemd >= 200\
Conflicts: xorg-x11-drv-vmmouse < 13.0.99\
%{expand:%%{?kernel%{?1:_%{1}}_conflicts:Conflicts: %%{kernel%{?1:_%{1}}_conflicts}}}\
%{expand:%%{?kernel%{?1:_%{1}}_obsoletes:Obsoletes: %%{kernel%{?1:_%{1}}_obsoletes}}}\
%{expand:%%{?kernel%{?1:_%{1}}_provides:Provides: %%{kernel%{?1:_%{1}}_provides}}}\
# We can't let RPM do the dependencies automatic because it'll then pick up\
# a correct but undesirable perl dependency from the module headers which\
# isn't required for the kernel proper to function\
AutoReq: no\
AutoProv: yes\
%{nil}

%package headers
Summary: Header files for the Linux kernel for use by glibc
Group: Development/System
Obsoletes: glibc-kernheaders < 3.0-46
Provides: glibc-kernheaders = 3.0-46
%if "0%{?variant}"
Obsoletes: kernel-headers < %{rpmversion}-%{pkg_release}
Provides: kernel-headers = %{rpmversion}-%{pkg_release}
%endif
%description headers
Kernel-headers includes the C header files that specify the interface
between the Linux kernel and userspace libraries and programs.  The
header files define structures and constants that are needed for
building most standard programs and are also needed for rebuilding the
glibc package.

%package debuginfo-common-%{_target_cpu}
Summary: Kernel source files used by %{name}-debuginfo packages
Group: Development/Debug
%description debuginfo-common-%{_target_cpu}
This package is required by %{name}-debuginfo subpackages.
It provides the kernel source files common to all builds.

%if %{with_perf}
%package -n perf
Summary: Performance monitoring for the Linux kernel
Group: Development/System
License: GPLv2
%description -n perf
This package contains the perf tool, which enables performance monitoring
of the Linux kernel.

%package -n perf-debuginfo
Summary: Debug information for package perf
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description -n perf-debuginfo
This package provides debug information for the perf package.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global debuginfo_args %{?debuginfo_args} -p '.*%%{_bindir}/perf(\.debug)?|.*%%{_libexecdir}/perf-core/.*|.*%%{_libdir}/traceevent/plugins/.*|XXX' -o perf-debuginfo.list}

%package -n python-perf
Summary: Python bindings for apps which will manipulate perf events
Group: Development/Libraries
%description -n python-perf
The python-perf package contains a module that permits applications
written in the Python programming language to use the interface
to manipulate perf events.

%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

%package -n python-perf-debuginfo
Summary: Debug information for package perf python bindings
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description -n python-perf-debuginfo
This package provides debug information for the perf python bindings.

# the python_sitearch macro should already be defined from above
%{expand:%%global debuginfo_args %{?debuginfo_args} -p '.*%%{python_sitearch}/perf.so(\.debug)?|XXX' -o python-perf-debuginfo.list}


%endif # with_perf

%if %{with_tools}
%package -n kernel-tools
Summary: Assortment of tools for the Linux kernel
Group: Development/System
License: GPLv2
Provides:  cpupowerutils = 1:009-0.6.p1
Obsoletes: cpupowerutils < 1:009-0.6.p1
Provides:  cpufreq-utils = 1:009-0.6.p1
Provides:  cpufrequtils = 1:009-0.6.p1
Obsoletes: cpufreq-utils < 1:009-0.6.p1
Obsoletes: cpufrequtils < 1:009-0.6.p1
Obsoletes: cpuspeed < 1:1.5-16
Requires: kernel-tools-libs = %{version}-%{release}
%description -n kernel-tools
This package contains the tools/ directory from the kernel source
and the supporting documentation.

%package -n kernel-tools-libs
Summary: Libraries for the kernels-tools
Group: Development/System
License: GPLv2
%description -n kernel-tools-libs
This package contains the libraries built from the tools/ directory
from the kernel source.

%package -n kernel-tools-libs-devel
Summary: Assortment of tools for the Linux kernel
Group: Development/System
License: GPLv2
Requires: kernel-tools = %{version}-%{release}
Provides:  cpupowerutils-devel = 1:009-0.6.p1
Obsoletes: cpupowerutils-devel < 1:009-0.6.p1
Requires: kernel-tools-libs = %{version}-%{release}
Provides: kernel-tools-devel
%description -n kernel-tools-libs-devel
This package contains the development files for the tools/ directory from
the kernel source.

%package -n kernel-tools-debuginfo
Summary: Debug information for package kernel-tools
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description -n kernel-tools-debuginfo
This package provides debug information for package kernel-tools.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global debuginfo_args %{?debuginfo_args} -p '.*%%{_bindir}/cpupower(\.debug)?|.*%%{_libdir}/libcpupower.*|.*%%{_bindir}/turbostat(\.debug)?|.*%%{_bindir}/tmon(\.debug)?|XXX' -o kernel-tools-debuginfo.list}

%endif # with_tools


#
# This macro creates a kernel-<subpackage>-debuginfo package.
#	%%kernel_debuginfo_package <subpackage>
#
%define kernel_debuginfo_package() \
%package %{?1:%{1}-}debuginfo\
Summary: Debug information for package %{name}%{?1:-%{1}}\
Group: Development/Debug\
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}\
Provides: %{name}%{?1:-%{1}}-debuginfo-%{_target_cpu} = %{version}-%{release}\
AutoReqProv: no\
%description %{?1:%{1}-}debuginfo\
This package provides debug information for package %{name}%{?1:-%{1}}.\
This is required to use SystemTap with %{name}%{?1:-%{1}}-%{KVERREL}.\
%{expand:%%global debuginfo_args %{?debuginfo_args} -p '/.*/%%{KVERREL}%{?1:[+]%{1}}/.*|/.*%%{KVERREL}%{?1:\+%{1}}(\.debug)?' -o debuginfo%{?1}.list}\
%{nil}

#
# This macro creates a kernel-<subpackage>-devel package.
#	%%kernel_devel_package <subpackage> <pretty-name>
#
%define kernel_devel_package() \
%package %{?1:%{1}-}devel\
Summary: Development package for building kernel modules to match the %{?2:%{2} }kernel\
Group: System Environment/Kernel\
Provides: kernel%{?1:-%{1}}-devel-%{_target_cpu} = %{version}-%{release}\
Provides: kernel-devel-%{_target_cpu} = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel-devel = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel-devel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Provides: installonlypkg(kernel)\
AutoReqProv: no\
Requires(pre): /usr/bin/find\
Requires: perl\
%description %{?1:%{1}-}devel\
This package provides kernel headers and makefiles sufficient to build modules\
against the %{?2:%{2} }kernel package.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules-extra package.
#	%%kernel_modules_extra_package <subpackage> <pretty-name>
#
%define kernel_modules_extra_package() \
%package %{?1:%{1}-}modules-extra\
Summary: Extra kernel modules to match the %{?2:%{2} }kernel\
Group: System Environment/Kernel\
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{version}-%{release}\
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel%{?1:-%{1}}-modules-extra = %{version}-%{release}%{?1:+%{1}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-extra-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires: kernel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires: kernel%{?1:-%{1}}-modules-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules-extra\
This package provides less commonly used kernel modules for the %{?2:%{2} }kernel package.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules package.
#	%%kernel_modules_package <subpackage> <pretty-name>
#
%define kernel_modules_package() \
%package %{?1:%{1}-}modules\
Summary: kernel modules to match the %{?2:%{2}-}core kernel\
Group: System Environment/Kernel\
Provides: kernel%{?1:-%{1}}-modules-%{_target_cpu} = %{version}-%{release}\
Provides: kernel-modules-%{_target_cpu} = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel-modules = %{version}-%{release}%{?1:+%{1}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires: kernel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules\
This package provides commonly used kernel modules for the %{?2:%{2}-}core kernel package.\
%{nil}

#
# this macro creates a kernel-<subpackage> meta package.
#	%%kernel_meta_package <subpackage>
#
%define kernel_meta_package() \
%package %{1}\
summary: kernel meta-package for the %{1} kernel\
group: system environment/kernel\
Requires: kernel-%{1}-core-uname-r = %{KVERREL}%{?variant}+%{1}\
Requires: kernel-%{1}-modules-uname-r = %{KVERREL}%{?variant}+%{1}\
%description %{1}\
The meta-package for the %{1} kernel\
%{nil}

#
# This macro creates a kernel-<subpackage> and its -devel and -debuginfo too.
#	%%define variant_summary The Linux kernel compiled for <configuration>
#	%%kernel_variant_package [-n <pretty-name>] <subpackage>
#
%define kernel_variant_package(n:) \
%package %{?1:%{1}-}core\
Summary: %{variant_summary}\
Group: System Environment/Kernel\
Provides: kernel-%{?1:%{1}-}core-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
%{expand:%%kernel_reqprovconf}\
%if %{?1:1} %{!?1:0} \
%{expand:%%kernel_meta_package %{?1:%{1}}}\
%endif\
%{expand:%%kernel_devel_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%{expand:%%kernel_modules_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%{expand:%%kernel_modules_extra_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%{expand:%%kernel_debuginfo_package %{?1:%{1}}}\
%{nil}

# The main -core package
%if %{bcm270x}
%define variant_summary The Linux kernel for the Raspberry Pi 2/3)
%kernel_variant_package 
%description core
This package includes a patched version of the Linux kernel built for
Raspberry Pi devices that use the Broadcom BCM27XX SOC. The
kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system: memory allocation, process allocation, device
input and output, etc.
%else
%define variant_summary The Linux kernel
%kernel_variant_package 
%description core
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system: memory allocation, process allocation, device
input and output, etc.
%endif

%prep

%if "%{baserelease}" == "0"
echo "baserelease must be greater than zero"
exit 1
%endif

# more sanity checking; do it quietly
if [ "%{patches}" != "%%{patches}" ] ; then
  for patch in %{patches} ; do
    if [ ! -f $patch ] ; then
      echo "ERROR: Patch  ${patch##/*/}  listed in specfile but is missing"
      exit 1
    fi
  done
fi 2>/dev/null

patch_command='patch -p1 -F1 -s'
ApplyPatch()
{
  local patch=$1
  shift
  if [ ! -f $patch ]; then
    exit 1
  fi
  case "$patch" in
  *.bz2) bunzip2 < "$patch" | $patch_command ${1+"$@"} ;;
  *.gz)  gunzip  < "$patch" | $patch_command ${1+"$@"} ;;
  *.xz)  unxz    < "$patch" | $patch_command ${1+"$@"} ;;
  *) $patch_command ${1+"$@"} < "$patch" ;;
  esac
}

# don't apply patch if it's empty
ApplyOptionalPatch()
{
  local patch=$1
  shift
  if [ ! -f $patch ]; then
    exit 1
  fi
  local C=$(wc -l $patch | awk '{print $1}')
  if [ "$C" -gt 9 ]; then
    ApplyPatch $patch ${1+"$@"}
  fi
}

# First we unpack the kernel tarball.
# If this isn't the first make prep, we use links to the existing clean tarball
# which speeds things up quite a bit.

# Update to latest upstream.
%if 0%{?released_kernel}
%define vanillaversion 4.%{base_sublevel}
# non-released_kernel case
%else
%if 0%{?rcrev}
%define vanillaversion 4.%{upstream_sublevel}-rc%{rcrev}
%if 0%{?gitrev}
%define vanillaversion 4.%{upstream_sublevel}-rc%{rcrev}-git%{gitrev}
%endif
%else
# pre-{base_sublevel+1}-rc1 case
%if 0%{?gitrev}
%define vanillaversion 4.%{base_sublevel}-git%{gitrev}
%else
%define vanillaversion 4.%{base_sublevel}
%endif
%endif
%endif

# %%{vanillaversion} : the full version name, e.g. 2.6.35-rc6-git3
# %%{kversion}       : the base version, e.g. 2.6.34

# Use kernel-%%{kversion}%%{?dist} as the top-level directory name
# so we can prep different trees within a single git directory.

# Build a list of the other top-level kernel tree directories.
# This will be used to hardlink identical vanilla subdirs.
sharedirs=$(find "$PWD" -maxdepth 1 -type d -name 'kernel-4.*' \
            | grep -x -v "$PWD"/kernel-%{kversion}%{?dist}) ||:

# Delete all old stale trees.
if [ -d kernel-%{kversion}%{?dist} ]; then
  cd kernel-%{kversion}%{?dist}
  for i in linux-*
  do
     if [ -d $i ]; then
       # Just in case we ctrl-c'd a prep already
       rm -rf deleteme.%{_target_cpu}
       # Move away the stale away, and delete in background.
       mv $i deleteme-$i
       rm -rf deleteme* &
     fi
  done
  cd ..
fi

# Generate new tree
if [ ! -d kernel-%{kversion}%{?dist}/vanilla-%{vanillaversion} ]; then

  if [ -d kernel-%{kversion}%{?dist}/vanilla-%{kversion} ]; then

    # The base vanilla version already exists.
    cd kernel-%{kversion}%{?dist}

    # Any vanilla-* directories other than the base one are stale.
    for dir in vanilla-*; do
      [ "$dir" = vanilla-%{kversion} ] || rm -rf $dir &
    done

  else

    rm -f pax_global_header
    # Look for an identical base vanilla dir that can be hardlinked.
    for sharedir in $sharedirs ; do
      if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{kversion} ]] ; then
        break
      fi
    done
    if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{kversion} ]] ; then
%setup -q -n kernel-%{kversion}%{?dist} -c -T
      cp -al $sharedir/vanilla-%{kversion} .
    else
%setup -q -n kernel-%{kversion}%{?dist} -c
      mv linux-%{kversion} vanilla-%{kversion}
    fi

  fi

%if "%{kversion}" != "%{vanillaversion}"

  for sharedir in $sharedirs ; do
    if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{vanillaversion} ]] ; then
      break
    fi
  done
  if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{vanillaversion} ]] ; then

    cp -al $sharedir/vanilla-%{vanillaversion} .

  else

    # Need to apply patches to the base vanilla version.
    cp -al vanilla-%{kversion} vanilla-%{vanillaversion}
    cd vanilla-%{vanillaversion}

# Update vanilla to the latest upstream.
# (non-released_kernel case only)
%if 0%{?rcrev}
    xzcat %{SOURCE1} | patch -p1 -F1 -s
%if 0%{?gitrev}
    xzcat %{SOURCE2} | patch -p1 -F1 -s
%endif
%else
# pre-{base_sublevel+1}-rc1 case
%if 0%{?gitrev}
    xzcat %{SOURCE1} | patch -p1 -F1 -s
%endif
%endif

    cd ..

  fi

%endif

else

  # We already have all vanilla dirs, just change to the top-level directory.
  cd kernel-%{kversion}%{?dist}

fi

# Now build the fedora kernel tree.
cp -al vanilla-%{vanillaversion} linux-%{KVERREL}

cd linux-%{KVERREL}

# released_kernel with possible stable updates
%if 0%{?stable_base}
# This is special because the kernel spec is HELL and nothing is consistent
xzcat %{SOURCE1} | patch -p1 -F1 -s
%endif

#
# misc small stuff to make things compile
#
#ApplyOptionalPatch compile-fixes.patch

%if !%{nopatches}


for i in %{patches}; do
    ApplyPatch $i
done


# END OF PATCH APPLICATIONS

%endif

# Any further pre-build tree manipulations happen here.

chmod +x scripts/checkpatch.pl

# This Prevents scripts/setlocalversion from mucking with our version numbers.
touch .scmversion

%define make make %{?cross_opts}

# get rid of unwanted files resulting from patch fuzz
find . \( -name "*.orig" -o -name "*~" \) -exec rm -f {} \; >/dev/null

# remove unnecessary SCM files
find . -name .gitignore -exec rm -f {} \; >/dev/null

cd ..

###
### build
###
%build

%ifnarch %{arm}
echo "This build is for arm archiecture only"
exit 1
%endif

%if %{with_debuginfo}
# This override tweaks the kernel makefiles so that we run debugedit on an
# object before embedding it.  When we later run find-debuginfo.sh, it will
# run debugedit again.  The edits it does change the build ID bits embedded
# in the stripped object, but repeating debugedit is a no-op.  We do it
# beforehand to get the proper final build ID bits into the embedded image.
# This affects the vDSO images in vmlinux, and the vmlinux image in bzImage.
export AFTER_LINK=\
'sh -xc "/usr/lib/rpm/debugedit -b $$RPM_BUILD_DIR -d /usr/src/debug \
    				-i $@ > $@.id"'
%endif

cp_vmlinux()
{
  eu-strip --remove-comment -o "$2" "$1"
}

BuildKernel() {
    MakeTarget=$1
    KernelImage=$2
    Flavour=$3
    Arch=%{asmarch}
    Flav=${Flavour:++${Flavour}}
    InstallName=${4:-vmlinuz}
    DevelDir=/usr/src/kernels/%{KVERREL}

    # When the bootable image is just the ELF kernel, strip it.
    # We already copy the unstripped file into the debuginfo package.
    if [ "$KernelImage" = vmlinux ]; then
      CopyKernel=cp_vmlinux
    else
      CopyKernel=cp
    fi

    #KernelVer=%{version}-%{release}.%{_target_cpu}${Flav}
    KernelVer=%{version}-%{release}.%{_target_cpu}
    echo BUILDING A KERNEL FOR ${Flavour} %{_target_cpu}...

    %if 0%{?stable_update}
    # make sure SUBLEVEL is incremented on a stable release.
    perl -p -i -e "s/^SUBLEVEL.*/SUBLEVEL = %{?stablerev}/" Makefile
    %endif

    # make sure EXTRAVERSION says what we want it to say
    perl -p -i -e "s/^EXTRAVERSION.*/EXTRAVERSION = -%{release}.%{_target_cpu}/" Makefile

    # if pre-rc1 devel kernel, must fix up PATCHLEVEL for our versioning scheme
    %if !0%{?rcrev}
    %if 0%{?gitrev}
    perl -p -i -e 's/^PATCHLEVEL.*/PATCHLEVEL = %{upstream_sublevel}/' Makefile
    %endif
    %endif

    # and now to start the build process
    make -s mrproper
    %if !%{bcm270x}
    #make bcm2835_defconfig
    cp %{SOURCE1100} .config
    %endif
    %if %{with_bcm2709}
    make bcm2709_defconfig
    cp %{SOURCE1000} .
    # merge fedberry kernel config fragments 
    scripts/kconfig/merge_config.sh -m -r .config bcm2709.cfg
    %endif
        
    echo USING ARCH=$Arch
    #make ARCH=$Arch oldnoconfig >/dev/null
    make ARCH=$Arch oldconfig
    %{make} ARCH=$Arch %{?_smp_mflags} $MakeTarget %{?sparse_mflags} %{?kernel_mflags}
    %{make} ARCH=$Arch %{?_smp_mflags} modules %{?sparse_mflags} || exit 1
    
    # Start installing the results
    %if %{with_debuginfo}
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/boot
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/%{image_install_path}
    %endif
    mkdir -p $RPM_BUILD_ROOT/%{image_install_path}
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer
    
    # Device Tree / Overlay
    %{make} ARCH=$Arch dtbs dtbs_install INSTALL_DTBS_PATH=$RPM_BUILD_ROOT/%{image_install_path}/dtb-$KernelVer
    cp -r $RPM_BUILD_ROOT/%{image_install_path}/dtb-$KernelVer $RPM_BUILD_ROOT/lib/modules/$KernelVer/dtb
    %if %{bcm270x}
    cp -p arch/$Arch/boot/dts/overlays/README $RPM_BUILD_ROOT/lib/modules/$KernelVer/dtb/overlays/
    mkdir -p $RPM_BUILD_ROOT/%{image_install_path}/overlays
    %endif
    
    # Start installing the results
    install -m 644 .config $RPM_BUILD_ROOT/boot/config-$KernelVer
    install -m 644 .config $RPM_BUILD_ROOT/lib/modules/$KernelVer/config
    install -m 644 System.map $RPM_BUILD_ROOT/boot/System.map-$KernelVer
    install -m 644 System.map $RPM_BUILD_ROOT/lib/modules/$KernelVer/System.map
    
    # We estimate the size of the initramfs because rpm needs to take this size
    # into consideration when performing disk space calculations. (See bz #530778)
    dd if=/dev/zero of=$RPM_BUILD_ROOT/boot/initramfs-$KernelVer.img bs=1M count=20

    # add the device tree trailer to the kernel img
    chmod +x scripts/mkknlimg
    %if !%{bcm270x}
    scripts/mkknlimg --dtok --283x $KernelImage $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    %else
    scripts/mkknlimg --dtok --270x $KernelImage $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    %endif
    chmod 755 $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    cp $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer $RPM_BUILD_ROOT/lib/modules/$KernelVer/$InstallName
    
    # hmac sign the kernel for FIPS
    echo "Creating hmac file: $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac"
    ls -l $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    sha512hmac $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer | sed -e "s,$RPM_BUILD_ROOT,," > $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac;
    cp $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac $RPM_BUILD_ROOT/lib/modules/$KernelVer/.vmlinuz.hmac

    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer
    # Override $(mod-fw) because we don't want it to install any firmware
    # we'll get it from the linux-firmware package and we don't want conflicts
    %{make} ARCH=$Arch INSTALL_MOD_PATH=$RPM_BUILD_ROOT modules_install KERNELRELEASE=$KernelVer mod-fw=

    # And save the headers/makefiles etc for building modules against
    #
    # This all looks scary, but the end result is supposed to be:
    # * all arch relevant include/ files
    # * all Makefile/Kconfig files
    # * all script/ files

    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/source
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    (cd $RPM_BUILD_ROOT/lib/modules/$KernelVer ; ln -s build source)
    # dirs for additional modules per module-init-tools, kbuild/modules.txt
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/extra
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/updates
    # first copy everything
    cp --parents `find  -type f -name "Makefile*" -o -name "Kconfig*"` $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp Module.symvers $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp System.map $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    if [ -s Module.markers ]; then
      cp Module.markers $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    fi
    # then drop all but the needed Makefiles/Kconfig files
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Documentation
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include
    cp .config $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a scripts $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    if [ -d arch/$Arch/scripts ]; then
      cp -a arch/$Arch/scripts $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/arch/%{_arch} || :
    fi
    if [ -f arch/$Arch/*lds ]; then
      cp -a arch/$Arch/*lds $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/arch/%{_arch}/ || :
    fi
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/*.o
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/*/*.o
    if [ -d arch/%{asmarch}/include ]; then
      cp -a --parents arch/%{asmarch}/include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    fi
    
    # include the machine specific headers
    if [ -d arch/%{asmarch}/mach-${Flavour}/include ]; then
      cp -a --parents arch/%{asmarch}/mach-${Flavour}/include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    fi
    
    # include a few files for 'make prepare'
    cp -a --parents arch/arm/tools/gen-mach-types $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/arm/tools/mach-types $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    
    cp -a include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include
    
    # Make sure the Makefile and version.h have a matching timestamp so that
    # external modules can be built
    touch -r $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Makefile $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/generated/uapi/linux/version.h

    # Copy .config to include/config/auto.conf so "make prepare" is unnecessary.
    cp $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/.config $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/config/auto.conf

%if %{with_debuginfo}
    if test -s vmlinux.id; then
      cp vmlinux.id $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/vmlinux.id
    else
      echo >&2 "*** ERROR *** no vmlinux build ID! ***"
      exit 1
    fi

    #
    # save the vmlinux file for kernel debugging into the kernel-debuginfo rpm
    #
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer
    cp vmlinux $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer
%endif

    find $RPM_BUILD_ROOT/lib/modules/$KernelVer -name "*.ko" -type f >modnames

    # mark modules executable so that strip-to-file can strip them
    xargs --no-run-if-empty chmod u+x < modnames

    # Generate a list of modules for block and networking.

    grep -F /drivers/ modnames | xargs --no-run-if-empty nm -upA |
    sed -n 's,^.*/\([^/]*\.ko\):  *U \(.*\)$,\1 \2,p' > drivers.undef

    collect_modules_list()
    {
      sed -r -n -e "s/^([^ ]+) \\.?($2)\$/\\1/p" drivers.undef |
        LC_ALL=C sort -u > $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.$1
      if [ ! -z "$3" ]; then
        sed -r -e "/^($3)\$/d" -i $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.$1
      fi
    }

    collect_modules_list networking \
    			 'register_netdev|ieee80211_register_hw|usbnet_probe|phy_driver_register|rt(l_|2x00)(pci|usb)_probe|register_netdevice'
    collect_modules_list block \
    			 'ata_scsi_ioctl|scsi_add_host|scsi_add_host_with_dma|blk_alloc_queue|blk_init_queue|register_mtd_blktrans|scsi_esp_register|scsi_register_device_handler|blk_queue_physical_block_size' 'pktcdvd.ko|dm-mod.ko'
    collect_modules_list drm \
    			 'drm_open|drm_init'
    collect_modules_list modesetting \
    			 'drm_crtc_init'

    # detect missing or incorrect license tags
    ( find $RPM_BUILD_ROOT/lib/modules/$KernelVer -name '*.ko' | xargs /sbin/modinfo -l | \
        grep -E -v 'GPL( v2)?$|Dual BSD/GPL$|Dual MPL/GPL$|GPL and additional rights$' ) && exit 1

    # remove files that will be auto generated by depmod at rpm -i time
    pushd $RPM_BUILD_ROOT/lib/modules/$KernelVer/
        rm -f modules.{alias*,builtin.bin,dep*,*map,symbols*,devname,softdep}
    popd

    # Call the modules-extra script to move things around
    %{SOURCE17} $RPM_BUILD_ROOT/lib/modules/$KernelVer %{SOURCE16}

    #
    # Generate the kernel-core and kernel-modules files lists
    #

    # Copy the System.map file for depmod to use, and create a backup of the
    # full module tree so we can restore it after we're done filtering
    cp System.map $RPM_BUILD_ROOT/.
    pushd $RPM_BUILD_ROOT
    mkdir restore
    cp -r lib/modules/$KernelVer/* restore/.

    # don't include anything going into k-m-e in the file lists
    rm -rf lib/modules/$KernelVer/extra

    # Find all the module files and filter them out into the core and modules
    # lists.  This actually removes anything going into -modules from the dir.
    find lib/modules/$KernelVer/kernel -name *.ko | sort -n > modules.list
	cp $RPM_SOURCE_DIR/filter-*.sh .
    %{SOURCE99} modules.list %{_target_cpu}
	rm filter-*.sh

    # Run depmod on the resulting module tree and make sure it isn't broken
    depmod -b . -aeF ./System.map $KernelVer &> depmod.out
    if [ -s depmod.out ]; then
        echo "Depmod failure"
        cat depmod.out
        exit 1
    else
        rm depmod.out
    fi
    # remove files that will be auto generated by depmod at rpm -i time
    pushd $RPM_BUILD_ROOT/lib/modules/$KernelVer/
        rm -f modules.{alias*,builtin.bin,dep*,*map,symbols*,devname,softdep}
    popd

    # Go back and find all of the various directories in the tree.  We use this
    # for the dir lists in kernel-core
    find lib/modules/$KernelVer/kernel -type d | sort -n > module-dirs.list

    # Cleanup
    rm System.map
    cp -r restore/* lib/modules/$KernelVer/.
    rm -rf restore
    popd

    # Make sure the files lists start with absolute paths or rpmbuild fails.
    # Also add in the dir entries
    sed -e 's/^lib*/\/lib/' %{?zipsed} $RPM_BUILD_ROOT/k-d.list > ../kernel-modules.list
    sed -e 's/^lib*/%dir \/lib/' %{?zipsed} $RPM_BUILD_ROOT/module-dirs.list > ../kernel-core.list
    sed -e 's/^lib*/\/lib/' %{?zipsed} $RPM_BUILD_ROOT/modules.list >> ../kernel-core.list

    # Cleanup
    rm -f $RPM_BUILD_ROOT/k-d.list
    rm -f $RPM_BUILD_ROOT/modules.list
    rm -f $RPM_BUILD_ROOT/module-dirs.list

    # Move the devel headers out of the root file system
    mkdir -p $RPM_BUILD_ROOT/usr/src/kernels
    mv $RPM_BUILD_ROOT/lib/modules/$KernelVer/build $RPM_BUILD_ROOT/$DevelDir

    # This is going to create a broken link during the build, but we don't use
    # it after this point.  We need the link to actually point to something
    # when kernel-devel is installed, and a relative link doesn't work across
    # the F17 UsrMove feature.
    ln -sf $DevelDir $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

    # prune junk from kernel-devel
    find $RPM_BUILD_ROOT/usr/src/kernels -name ".*.cmd" -exec rm -f {} \;
}

###
# DO it...
###

# prepare directories
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/boot
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}

cd linux-%{KVERREL}

BuildKernel %make_target %kernel_image %{?Flavour}

%global perf_make \
  make %{?cross_opts} %{?_smp_mflags} -C tools/perf WERROR=0 NO_LIBUNWIND=1 HAVE_CPLUS_DEMANGLE=1 NO_GTK2=1 NO_STRLCPY=1 NO_BIONIC=1 prefix=%{_prefix}
%if %{with_perf}
# perf
%{perf_make} DESTDIR=$RPM_BUILD_ROOT all
%endif

%if %{with_tools}
# cpupower
# make sure version-gen.sh is executable.
chmod +x tools/power/cpupower/utils/version-gen.sh
%{make} %{?_smp_mflags} -C tools/power/cpupower CPUFREQ_BENCH=false
pushd tools/thermal/tmon/
%{make}
popd
%endif


###
### Special hacks for debuginfo subpackages.
###

# This macro is used by %%install, so we must redefine it before that.
%define debug_package %{nil}

%if %{with_debuginfo}

%define __debug_install_post \
  /usr/lib/rpm/find-debuginfo.sh %{debuginfo_args} %{_builddir}/%{?buildsubdir}\
%{nil}

%ifnarch noarch
%global __debug_package 1
%files -f debugfiles.list debuginfo-common-%{_target_cpu}
%defattr(-,root,root)
%endif

%endif

#
# Disgusting hack alert! We need to ensure we sign modules *after* all
# invocations of strip occur, which is in __debug_install_post if
# find-debuginfo.sh runs, and __os_install_post if not.
#
%define __spec_install_post \
  %{?__debug_package:%{__debug_install_post}}\
  %{__arch_install_post}\
  %{__os_install_post}


###
### install
###

%install

cd linux-%{KVERREL}

# We have to do the headers install before the tools install because the
# kernel headers_install will remove any header files in /usr/include that
# it doesn't install itself.

%if %{with_headers}
# Install kernel headers
make ARCH=%{hdrarch} INSTALL_HDR_PATH=$RPM_BUILD_ROOT/usr headers_install

find $RPM_BUILD_ROOT/usr/include \
     \( -name .install -o -name .check -o \
     	-name ..install.cmd -o -name ..check.cmd \) | xargs rm -f

%endif

%if %{with_perf}
# perf tool binary and supporting scripts/binaries
%{perf_make} DESTDIR=$RPM_BUILD_ROOT lib=%{_lib} install-bin install-traceevent-plugins
# remove the 'trace' symlink.
rm -f %{buildroot}%{_bindir}/trace

# python-perf extension
%{perf_make} DESTDIR=$RPM_BUILD_ROOT install-python_ext

# perf man pages (note: implicit rpm magic compresses them later)
mkdir -p %{buildroot}/%{_mandir}/man1
pushd %{buildroot}/%{_mandir}/man1
tar -xf %{SOURCE10}
popd

# remove perf-tips dir
rm -rf %{buildroot}%{_docdir}/perf-tip
%endif

%if %{with_tools}
%{make} -C tools/power/cpupower DESTDIR=$RPM_BUILD_ROOT libdir=%{_libdir} mandir=%{_mandir} CPUFREQ_BENCH=false install
rm -f %{buildroot}%{_libdir}/*.{a,la}
%find_lang cpupower
mv cpupower.lang ../
chmod 0755 %{buildroot}%{_libdir}/libcpupower.so*
mkdir -p %{buildroot}%{_unitdir} %{buildroot}%{_sysconfdir}/sysconfig
install -m644 %{SOURCE2000} %{buildroot}%{_unitdir}/cpupower.service
install -m644 %{SOURCE2001} %{buildroot}%{_sysconfdir}/sysconfig/cpupower
pushd tools/thermal/tmon
make INSTALL_ROOT=%{buildroot} install
popd
%endif


###
### clean
###

%clean
rm -rf $RPM_BUILD_ROOT

###
### scripts
###

%if %{with_tools}
%post -n kernel-tools
/sbin/ldconfig

%postun -n kernel-tools
/sbin/ldconfig
%endif

#
# This macro defines a %%post script for a kernel*-devel package.
#	%%kernel_devel_post [<subpackage>]
#
%define kernel_devel_post() \
%{expand:%%post %{?1:%{1}-}devel}\
if [ -f /etc/sysconfig/kernel ]\
then\
    . /etc/sysconfig/kernel || exit $?\
fi\
if [ "$HARDLINK" != "no" -a -x /usr/sbin/hardlink ]\
then\
    (cd /usr/src/kernels/%{KVERREL}%{?1:+%{1}} &&\
     /usr/bin/find . -type f | while read f; do\
       hardlink -c /usr/src/kernels/*.fc*.*/$f $f\
     done)\
fi\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules-extra package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_extra_post [<subpackage>]
#
%define kernel_modules_extra_post() \
%{expand:%%post %{?1:%{1}-}modules-extra}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules-extra}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_post [<subpackage>]
#
%define kernel_modules_post() \
%{expand:%%post %{?1:%{1}-}modules}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}

# This macro defines a %%posttrans script for a kernel package.
#	%%kernel_variant_posttrans [<subpackage>]
# More text can follow to go at the end of this variant's %%post.
#
%define kernel_variant_posttrans() \
%{expand:%%posttrans %{?1:%{1}-}core}\
/sbin/new-kernel-pkg --package kernel --rpmposttrans %{KVERREL}%{?1:+%{1}} || exit $?\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/vmlinuz /%{image_install_path}/kernel7.img\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/vmlinuz /%{image_install_path}/vmlinuz-%{KVERREL}%{?1:+%{1}}\
%if %{bcm270x}\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/dtb/*.dtb /boot/\
rm -f /boot/overlays/*\
cp /lib/modules/%{KVERREL}%{?1:+%{1}}/dtb/overlays/* /boot/overlays/\
%else\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/dtb/bcm283* /boot/\
%endif\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/config /%{image_install_path}/config-%{KVERREL}%{?1:+%{1}}\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/System.map /%{image_install_path}/System.map-%{KVERREL}%{?1:+%{1}}\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/.vmlinuz.hmac /%{image_install_path}/.vmlinuz.hmac-%{KVERREL}%{?1:+%{1}}\
%{nil}

#
# This macro defines a %%post script for a kernel package and its devel package.
#	%%kernel_variant_post [-v <subpackage>] [-r <replace>]
# More text can follow to go at the end of this variant's %%post.
#
%define kernel_variant_post(v:r:) \
%{expand:%%kernel_devel_post %{?-v*}}\
%{expand:%%kernel_modules_post %{?-v*}}\
%{expand:%%kernel_modules_extra_post %{?-v*}}\
%{expand:%%kernel_variant_posttrans %{?-v*}}\
%{expand:%%post %{?-v*:%{-v*}-}core}\
%{nil}

#
# This macro defines a %%preun script for a kernel package.
#	%%kernel_variant_preun <subpackage>
#
%define kernel_variant_preun() \
%{expand:%%preun %{?1:%{1}-}core}\
/bin/kernel-install remove %{KVERREL}%{?1:+%{1}} /%{image_install_path}/vmlinuz-%{KVERREL}%{?1:+%{1}} || exit $?\
%{nil}

%kernel_variant_preun
%kernel_variant_post -r kernel

if [ -x /sbin/ldconfig ]
then
    /sbin/ldconfig -X || exit $?
fi

###
### file lists
###

%if %{with_headers}
%files headers
%defattr(-,root,root)
/usr/include/*
%endif

%if %{with_perf}
%files -n perf
%defattr(-,root,root)
%{_bindir}/perf
%dir %{_libdir}/traceevent/plugins
%{_libdir}/traceevent/plugins/*
%dir %{_libexecdir}/perf-core
%{_libexecdir}/perf-core/*
%{_datadir}/perf-core/*
%{_mandir}/man[1-8]/perf*
%{_sysconfdir}/bash_completion.d/perf
%doc linux-%{KVERREL}/tools/perf/Documentation/examples.txt
%doc linux-%{KVERREL}/tools/perf/Documentation/tips.txt

%files -n python-perf
%defattr(-,root,root)
%{python_sitearch}

%if %{with_debuginfo}
%files -f perf-debuginfo.list -n perf-debuginfo
%defattr(-,root,root)

%files -f python-perf-debuginfo.list -n python-perf-debuginfo
%defattr(-,root,root)
%endif
%endif # with_perf

%if %{with_tools}
%files -n kernel-tools -f cpupower.lang
%defattr(-,root,root)
%{_bindir}/cpupower
%{_unitdir}/cpupower.service
%{_mandir}/man[1-8]/cpupower*
%config(noreplace) %{_sysconfdir}/sysconfig/cpupower
%{_bindir}/tmon


%if %{with_debuginfo}
%files -f kernel-tools-debuginfo.list -n kernel-tools-debuginfo
%defattr(-,root,root)
%endif

%files -n kernel-tools-libs
%{_libdir}/libcpupower.so.0
%{_libdir}/libcpupower.so.0.0.0

%files -n kernel-tools-libs-devel
%{_libdir}/libcpupower.so
%{_includedir}/cpufreq.h

%endif # with_perf

# empty meta-package
%files
%defattr(-,root,root)

# This is %%{image_install_path} on an arch where that includes ELF files,
# or empty otherwise.
%define elf_image_install_path %{?kernel_image_elf:%{image_install_path}}

#
# This macro defines the %%files sections for a kernel package
# and its devel and debuginfo packages.
#	%%kernel_variant_files [-k vmlinux] <condition> <subpackage>
#
%define kernel_variant_files(k:) \
%{expand:%%files -f kernel-%{?2:%{2}-}core.list %{?2:%{2}-}core}\
%defattr(-,root,root)\
%{!?_licensedir:%global license %%doc}\
%license linux-%{KVERREL}/COPYING\
/%{image_install_path}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-%{KVERREL}%{?2:+%{2}}\
%ghost /%{image_install_path}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-%{KVERREL}%{?2:+%{2}}\
/lib/modules/%{KVERREL}%{?2:+%{2}}/.vmlinuz.hmac \
%ghost /%{image_install_path}/.vmlinuz-%{KVERREL}%{?2:+%{2}}.hmac \
/lib/modules/%{KVERREL}%{?2:+%{2}}/dtb \
%ghost /%{image_install_path}/dtb-%{KVERREL}%{?2:+%{2}} \
%{!?_licensedir:%global license %%doc}\
%license linux-%{KVERREL}/COPYING\
/lib/modules/%{KVERREL}%{?2:+%{2}}/%{?-k:%{-k*}}%{!?-k:vmlinuz}\
%ghost /%{image_install_path}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-%{KVERREL}%{?2:+%{2}}\
/lib/modules/%{KVERREL}%{?2:+%{2}}/.vmlinuz.hmac \
%ghost /%{image_install_path}/.vmlinuz-%{KVERREL}%{?2:+%{2}}.hmac \
/lib/modules/%{KVERREL}%{?2:+%{2}}/dtb \
%ghost /%{image_install_path}/dtb-%{KVERREL}%{?2:+%{2}} \
%attr(600,root,root) /lib/modules/%{KVERREL}%{?2:+%{2}}/System.map\
%ghost /boot/System.map-%{KVERREL}%{?2:+%{2}}\
/lib/modules/%{KVERREL}%{?2:+%{2}}/config\
%ghost /boot/config-%{KVERREL}%{?2:+%{2}}\
%ghost /boot/initramfs-%{KVERREL}%{?2:+%{2}}.img\
%if %{bcm270x}\
%ghost /%{image_install_path}/overlays\
%endif\
%dir /lib/modules\
%dir /lib/modules/%{KVERREL}%{?2:+%{2}}\
%dir /lib/modules/%{KVERREL}%{?2:+%{2}}/kernel\
/lib/modules/%{KVERREL}%{?2:+%{2}}/build\
/lib/modules/%{KVERREL}%{?2:+%{2}}/source\
/lib/modules/%{KVERREL}%{?2:+%{2}}/updates\
/lib/modules/%{KVERREL}%{?2:+%{2}}/modules.*\
%{expand:%%files -f kernel-%{?2:%{2}-}modules.list %{?2:%{2}-}modules}\
%defattr(-,root,root)\
%{expand:%%files %{?2:%{2}-}devel}\
%defattr(-,root,root)\
/usr/src/kernels/%{KVERREL}%{?2:+%{2}}\
%{expand:%%files %{?2:%{2}-}modules-extra}\
%defattr(-,root,root)\
/lib/modules/%{KVERREL}%{?2:+%{2}}/extra\
%if %{with_debuginfo}\
%ifnarch noarch\
%{expand:%%files -f debuginfo%{?2}.list %{?2:%{2}-}debuginfo}\
%defattr(-,root,root)\
%endif\
%endif\
%if %{?2:1} %{!?2:0}\
%{expand:%%files %{2}}\
%defattr(-,root,root)\
%endif\
%{nil}


%kernel_variant_files

# plz don't put in a version string unless you're going to tag
# and build.
#
# 
%changelog
* Thu Aug 11 2016 Vaughan <devel at agrez dot net> - 4.5.7-1
- Split bcm2709 linux kernel port into a separate build option (enabled by default)
- Add a new kernel config for kernel.org (bcm2835) builds (bcm283x.config)
- Add mkknlimg to the bcm283x build (Patch10)
- vmlinuz, System.map, config & .hmac files now installed to '/lib/modules/$KernelVer/'
- Updated kernel %%files & %%posttrans to relfect relocation of kernel files
- Sync RPi patch to git revision: 237402141fd74ca989bd86ebb76d834cb6fa5454
- Update to stable kernel patch v4.5.7
- Misc spec file cleanups

* Sun Mar 20 2016 Vaughan <devel at agrez dot net> - 4.5.0-1.d553aa6
- Modify how we apply patches
- Rebase to 4.5.y kernel branch
- Sync RPi patch to git revision: rpi-4.5.y d553aa6b15b40562813eb5c0d1b640fb83e8fc50
- Kernel now enables by default Device Tree Overlay ConfigFS interface (*.dtbo files)
  Refer: https://github.com/raspberrypi/linux/commit/d95dcfb60819ec448273853e027766bdb241869c
  Refer: https://www.raspberrypi.org/forums/viewtopic.php?f=107&t=139732
- Add Requires: raspberrypi-vc-utils >= 20160321 (kernel now requires dtoverlay util)

* Fri Mar 11 2016 Vaughan <devel at agrez dot net> - 4.4.5-400.418177e
- Sync RPi patch to git revision: rpi-4.4.y 418177e2e57d3ac1248ced154fa1067ca42ba315
- Update to stable kernel patch v4.4.5

* Tue Mar 08 2016 Vaughan <devel at agrez dot net> - 4.4.4-401.4f7b097
- Sync RPi patch to git revision: rpi-4.4.y 4f7b097a399b7d0ed275bca0ec72fb4d05c4094b
- Clean /boot/overlays in %%posttrans to remove any stale *.dtb files.
- Copy everything to /boot/overlays (not just .dbt files).

* Mon Mar 07 2016 Vaughan <devel at agrez dot net> - 4.4.4-400.c5cbb66
- Sync RPi patch to git revision: rpi-4.4.y c5cbb66686e7e289e8a7aff49a954f86893e628d
- Stable kernel.org patch now referenced as a Source1
- Stable patch now applied directly instead of using ApplyPatch() function

* Wed Mar 02 2016 Vaughan <devel at agrez dot net> - 4.4.3-401.36babd8
- Sync patch to RPi git revision: rpi-4.4.y 36babd89241c85258acebe06616f1f1a58356f8e
- Add RPi 3 Model B support (bcm2710)

* Sun Feb 28 2016 Vaughan <devel at agrez dot net> - 4.4.3-400.8547bb0
- Update to stable kernel patch v4.4.3
- Sync patch to RPi git revision: rpi-4.4.y 8547bb07f9d79874648c6a4aab545fbabe0b4765

* Sat Feb 20 2016 Vaughan <devel at agrez dot net> - 4.4.2-400.8941fe4
- Update to stable kernel patch v4.4.2
- Sync patch to RPi git revision: rpi-4.4.y 8941fe4985a1cc8f800be00224c6a2e741789d03

* Sun Feb 14 2016 Vaughan <devel at agrez dot net> - 4.4.1-401.52d3149
- Sync patch to RPi git revision: rpi-4.4.y 52d3149aba3c684db1b6c739ca794dc330d92929
  This includes the significant revision of the bcm2835-sdhost driver

* Tue Feb 09 2016 Vaughan <devel at agrez dot net> - 4.4.1-400.065d2a9
- Rebase to 4.4.y kernel branch
- Update to stable kernel patch v4.4.1
- Sync patch to RPi git revision: rpi-4.4.y 065d2a9ca6e18a16431ced57a40dddc06b792650

* Sun Jan 24 2016 Vaughan <devel at agrez dot net> - 4.3.4-400.4dee941
- Update to stable kernel patch v4.3.4
- Sync rpi patch to git revision: rpi-4.3.y 4dee9412d72abd346c9b7a3bbd8e96a5f0b163f3

* Sat Jan 16 2016 Vaughan <devel at agrez dot net> - 4.3.3-400.547120c
- Rebase to 4.3.y kernel branch
- Update to stable kernel patch v4.3.3
- Sync patch to git revision: rpi-4.3.y 547120c6be9054cd4b7186aee95c6e698f839d44

* Wed Dec 23 2015 Vaughan <devel at agrez dot net> - 4.2.8-400.e0103e9
- Update to stable kernel patch v4.2.8
- Sync patch to git revision: rpi-4.2.y e0103e9645caca6576c1b6c21608c28015857ab8
- Split out config modifications to config-fedberry.cfg
- Apply config 'fragments' (config-fedberry.cfg) at build time using 'merge_config.sh'
- Drop config-bcm2709
- Enable PREEMPT_VOLUNTARY
- Refactor kernel config

* Sat Dec 12 2015 Vaughan <devel at agrez dot net> - 4.2.7-400.c35cc1f
- Sync patch to git revision: rpi-4.2.y c35cc1fea33fcbaa04ddcd8c9733fd66f6d3e7ad
- Update to stable kernel patch v4.2.7
- Drop kbuild-AFTER_LINK.patch as its not used.
- Add TOUCHSCREEN_FT6236=m

* Sat Dec 05 2015 Vaughan <devel at agrez dot net> - 4.2.6-402.806e022
- Disable NFSv2 support
- Enable NFSv4_1 & NFSv4_2 support
- Build NFSD as a module (NFSD=m)

* Sun Nov 29 2015 Vaughan <devel at agrez dot net> - 4.2.6-401.806e022
- Sync patch to git revision: rpi-4.2.y 806e02221caec4ca42adc7aed42f5523bc8fb0dc
- Disable initrd creation for now (we currently don't use it)

* Sun Nov 15 2015 Vaughan <devel at agrez dot net> - 4.2.6-400.429f50d
- Sync patch to git revision: rpi-4.2.y 429f50d21465619822725e5134f51e4782dec4fe
- Update to stable kernel patch v4.2.6

* Sat Oct 31 2015 Vaughan <devel at agrez dot net> - 4.2.5-400.50acac3
- Sync patch to git revision: rpi-4.2.y 50acac3fd0a949f6cd15cdfaac9e2e1588aada0b
- Update to stable kernel patch v4.2.5
- Refactor kernel config

* Wed Oct 14 2015 Vaughan <devel at agrez dot net> - 4.2.3-401.6c1c048
- Sync patch to git revision: rpi-4.2.y 6c1c04868e77b2ff314b42548b12963d824230f8
- Default bcm2709 kernel config (bcm2709_defconfig) does not enable selinux
  support. Enable it!
- Refactor kernel config

* Wed Oct 07 2015 Vaughan <devel at agrez dot net> - 4.2.3-400.30fc66b
- Rebase to 4.2.y kernel branch
- Update to stable kernel patch v4.2.3
- Sync patch to git revision: rpi-4.2.y 30fc66bfd7a538fb620c3b7bc4daaf79f8d92d70
- Refactor kernel config

* Mon Oct 05 2015 Vaughan <devel at agrez dot net> - 4.1.10-300.0b43921
- Update to stable kernel patch v4.1.10
- Sync to latest git revision: rpi-4.1.y 0b439214b09e3f80413c19b7e0a407c34a79411c

* Thu Sep 24 2015 Vaughan <devel at agrez dot net> - 4.1.8-300.d2b2388
- Update to stable kernel patch v4.1.8
- Sync to latest git revision: rpi-4.1.y d2b2388d05d8a97b0ba14fcf2b71f19f66bc4d02

* Thu Sep 17 2015 Vaughan <devel at agrez dot net> - 4.1.7-300.676d8d9
- Update to stable kernel patch v4.1.7
- Sync to latest git revision: rpi-4.1.y 676d8d98ed6ffa1afce9cd6585017db8fe606347
- Refactor kernel config
- install_dtbs target now works correctly, modify spec accordingly.

* Fri Sep 11 2015 Vaughan <devel at agrez dot net> - 4.1.6-302.c8baa97
- Sync to latest git revision: rpi-4.1.y c8baa9702cc99de9614367d0b96de560944e7ccd
- Requires bcm283x-firmware >= 20150909

* Wed Sep 02 2015 Vaughan <devel at agrez dot net> - 4.1.6-301.6b30ac8
- Sync to latest git revision: rpi-4.1.y 6b30ac82c3595887416c7870c35c2cc522f801cc 
- Refactor kernel config

* Wed Aug 19 2015 Vaughan <devel at agrez dot net> - 4.1.6-300.4507c97
- Update to stable kernel patch v4.1.6
- Sync to latest git revision: rpi-4.1.y 4507c9752292506fa6ef136114ad14ffd92b2ca5
- Requires bcm283x-firmware >= 20150819
- Refactor kernel config

* Tue Aug 18 2015 Vaughan <devel at agrez dot net> - 4.1.5-301.5925037
- Drop the extra generated kernel-*.img
- Add device tree trailer to vmlinuz image instead 

* Sun Aug 16 2015 Vaughan <devel at agrez dot net> - 4.1.5-300.5925037
- Sync to latest git revision: rpi-4.1.y 592503752b6951972f161f04280683c5af38d173
- Requires bcm283x-firmware >= 20150815

* Sun Aug 16 2015 Vaughan <devel at agrez dot net> - 4.1.5-300.5925037
- Sync to latest git revision: rpi-4.1.y 592503752b6951972f161f04280683c5af38d173
- Requires bcm283x-firmware >= 20150815

* Sat Aug 08 2015 Vaughan <devel at agrez dot net> - 4.1.4-300.869c3bc
- Update to stable kernel release v4.1.4
- Sync to latest rpi git revision: rpi-4.1.y 869c3bc300150a8afd4bc42efcb0f36f0b041f09
- Requires bcm283x-firmware >= 20150808-11eaffc

* Sat Jul 25 2015 Vaughan <devel at agrez dot net> - 4.0.9-300.4d317a8
- Update to stable kernel release v4.0.9
- Sync to latest rpi git revision: rpi-4.0.y 4d317a835a7b6354e41c2678507f2a894fdceb26
- Requires bcm283x-firmware >= 20150725-1.464ce4f

* Wed Jul 15 2015 Vaughan <devel at agrez dot net> - 4.0.8-300.4259dcc
- Update to stable kernel release v4.0.8
- Sync to latest rpi git revision: rpi-4.0.y 4259dcc8987bd0d88428762c637a18df553de04c
- Refactor kernel config

* Tue Jun 30 2015 Vaughan <devel at agrez dot net> - 4.0.7-300.c53bd46
- Fork from current Fedora spec and make it build on the RaspberryPi 2.
  This involved numermous modifications / changes (too many to list).
- This is a dedicated spec file for building Raspberry Pi 2 kernels only.
  No other arm platforms are presently supported.
- Strip support for all other archs and kernel build types.
- Drop most additional 'fedora' patches
- Update to stable kernel release v4.0.7
- Sync to latest rpi git revision: rpi-4.0.y c53bd4659ef8b3e8161a85f297b93a9408226b6a
  (Patch100)
- Refactor kernel config (config-bcm2709)
- Add requires for bcm283x-firmware >= 20150620-1.8b9d7b (kernel-core)

* Tue Jun 23 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.6-300
- Linux v4.0.6

* Thu Jun 18 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch to fix touchpad issues on Razer machines (rhbz 1227891)

* Fri Jun 12 2015 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2015-XXXX kvm: NULL ptr deref in kvm_apic_has_events (rhbz 1230770 1230774)

* Thu Jun 11 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backport fixes for synaptic 3 finger tap (rhbz 1212230)
- Backport btrfs fixes queued for stable (rhbz 1217191)

* Tue Jun 09 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix touchpad for Thinkpad S540 (rhbz 1223051)

* Mon Jun 08 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Linux v4.0.5

* Thu Jun 04 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backport commit to fix block spew (rhbz 1226621)
- Add patch to fix SMT guests on POWER7 (rhbz 1227877)
- Add patch to turn of WC mmaps on i915 from airlied (rhbz 1226743)

* Wed Jun 03 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix del_timer_sync in mwifiex

* Wed Jun 03 2015 Laura Abbott <labbott@fedoraproject.org>
- Drop that blasted firwmare warning until we get a real fix (rhbz 1133378)

* Wed Jun 03 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix auditing of canonical mode (rhbz 1188695)

* Wed Jun 03 2015 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2015-1420 fhandle race condition (rhbz 1187534 1227417)

* Tue Jun 02 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix fd_do_rw error (rhbz 1218882)

* Tue Jun 02 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix middle button issues on external Lenovo keyboards (rhbz 1225563)

* Thu May 28 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add quirk for Mac Pro backlight (rhbz 1217249)

* Thu May 28 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.4-303
- Add patch to avoid vmmouse being classified as a joystic (rhbz 1214474)

* Wed May 27 2015 Josh Boyer <jwboyer@fedoraproject.org> -4.0.4-302
- Apply queued fixes for crasher reported by Alex Larsson
- Enable in-kernel vmmouse driver (rhbz 1214474)

* Tue May 26 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix signed division error (rhbz 1200353)

* Tue May 26 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backport patch to fix might_sleep splat (rhbz 1220519)

* Thu May 21 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.4-301
- Add patch to fix discard on md RAID0 (rhbz 1223332)
- Add submitted stable fix for i915 flickering on ilk (rhbz 1218688)

* Mon May 18 2015 Laura Abbott <labbott@fedoraproject.org>
- Re-add the v4l2 query caps patch which was dropped

* Mon May 18 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix incorrect bandwidth on some Chicony webcams

* Mon May 18 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.4-300
- Linux v4.0.4

* Fri May 15 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix DVB oops (rhbz 1220118)

* Thu May 14 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.3-301
- Disable i915 verbose state checks

* Thu May 14 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix non-empty dir removal in overlayfs (rhbz 1220915)

* Wed May 13 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix spew from KVM switch (rhbz 1219343)

* Wed May 13 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.3-300
- Linux v4.0.3

* Sat May  9 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Minor ARMv7 updates

* Thu May 07 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.2-300
- Linux v4.0.2 (rhbz 1182816)

* Tue May 05 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backport patch to blacklist TRIM on all Samsung 8xx series SSDs (rhbz 1218662)
- CVE-2015-3636 ping-sockets use-after-free privilege escalation (rhbz 1218074 1218110)

* Thu Apr 30 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix backlight on various Toshiba machines (rhbz 1206036 1215989)

* Wed Apr 29 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.1-300
- Linux v4.0.1

* Tue Apr 28 2015 Justin M. Forbes <jforbes@fedoraproject.org>
- Fix up boot times for live images (rhbz 1210857)

* Mon Apr 27 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backport NFS DIO fixes from 4.1 (rhbz 1211017 1211013)

* Fri Apr 24 2015 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2015-3339 race condition between chown and execve (rhbz 1214030)
- Fix iscsi with QNAP devices (rhbz 1208999)

* Wed Apr 22 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Fix RTC on TrimSlice
- Enable all sound modules for TrimSlice (also needed for other devices)

* Mon Apr 20 2015 Laura Abbott
- Fix sound issues (rhbz 1188741)

* Fri Apr 17 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add support for touchpad on Google Pixel 2 (rhbz 1209088)
- Allow disabling raw mode in logitech-hidpp (rhbz 1210801)

* Wed Apr 15 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch to fix tty closure race (rhbz 1208953)

* Sun Apr 12 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-1
- Linux v4.0

* Fri Apr 10 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc7.git2.1
- Linux v4.0-rc7-42-ge5e02de0665e

* Thu Apr 09 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc7.git1.1
- Linux v4.0-rc7-30-g20624d17963c

* Thu Apr 02 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc6.git2.1
- Linux v4.0-rc6-101-g0a4812798fae

* Thu Apr 02 2015 Josh Boyer <jwboyer@fedoraproject.org>
- DoS against IPv6 stacks due to improper handling of RA (rhbz 1203712 1208491)

* Wed Apr 01 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc6.git1.1
- Linux v4.0-rc6-31-gd4039314d0b1
- CVE-2015-2150 xen: NMIs triggerable by guests (rhbz 1196266 1200397)

* Tue Mar 31 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Enable MLX4_EN_VXLAN (rhbz 1207728)

* Mon Mar 30 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc6.git0.1
- Linux v4.0-rc6

* Fri Mar 27 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git4.1
- Linux v4.0-rc5-96-g3c435c1e472b
- Fixes hangs due to i915 issues (rhbz 1204050 1206056)

* Thu Mar 26 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git3.1
- Linux v4.0-rc5-80-g4c4fe4c24782

* Wed Mar 25 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Add aarch64 patches to fix mustang usb, seattle eth, and console settings

* Wed Mar 25 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git2.4
- Add patches to fix a few more i915 hangs/oopses

* Wed Mar 25 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git2.1
- Linux v4.0-rc5-53-gc875f421097a

* Tue Mar 24 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix ALPS v5 and v7 trackpads (rhbz 1203584)

* Tue Mar 24 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git1.3
- Linux v4.0-rc5-25-g90a5a895cc8b
- Add some i915 fixes

* Mon Mar 23 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git0.3
- Enable CONFIG_SND_BEBOB (rhbz 1204342)
- Validate iovec range in sys_sendto/sys_recvfrom
- Revert i915 commit that causes boot hangs on at least some headless machines
- Linux v4.0-rc5

* Fri Mar 20 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc4.git2.1
- Linux v4.0-rc4-199-gb314acaccd7e
- Fix brightness on Lenovo Ideapad Z570 (rhbz 1187004)

* Thu Mar 19 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc4.git1.3
- Linux v4.0-rc4-88-g7b09ac704bac
- Rename arm64-xgbe-a0.patch

* Thu Mar 19 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Drop arm64 non upstream patch

* Thu Mar 19 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch to fix high cpu usage on direct_read kernfs files (rhbz 1202362)

* Wed Mar 18 2015 Jarod Wilson <jwilson@fedoraproject.org>
- Fix kernel-uname-r Requires/Provides variant mismatches

* Tue Mar 17 2015 Kyle McMartin <kmcmarti@redhat.com> - 4.0.0-0.rc4.git0.3
- Update kernel-arm64.patch, move EDAC to arm-generic, add EDAC_XGENE on arm64.
- Add PCI_ECAM on generic, since it'll be selected most places anyway.

* Mon Mar 16 2015 Jarod Wilson <jwilson@fedoraproject.org>
- Fix bad variant usage in kernel dependencies

* Mon Mar 16 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc4.git0.1
- Linux v4.0-rc4
- Drop arm64 RCU revert patch.  Should be fixed properly upstream now.
- Disable debugging options.

* Sun Mar 15 2015 Jarod Wilson <jwilson@fedoraproject.org>
- Fix kernel-tools sub-packages for variant builds

* Fri Mar 13 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix esrt build on aarch64

* Fri Mar 13 2015 Kyle McMartin <kyle@fedoraproject.org>
- arm64-revert-tlb-rcu_table_free.patch: revert 5e5f6dc1 which
  causes lockups on arm64 machines.
- Also revert ESRT on AArch64 for now.

* Fri Mar 13 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc3.git2.1
- Linux v4.0-rc3-148-gc202baf017ae
- Add patch to support clickpads (rhbz 1201532)

* Thu Mar 12 2015 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2014-8159 infiniband: uverbs: unprotected physical memory access (rhbz 1181166 1200950)

* Wed Mar 11 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc3.git1.1
- Linux v4.0-rc3-111-gaffb8172de39
- CVE-2015-2150 xen: NMIs triggerable by guests (rhbz 1196266 1200397)
- Patch series to fix Lenovo *40 and Carbon X1 touchpads (rhbz 1200777 1200778)
- Revert commit that added bad rpath to cpupower (rhbz 1199312)
- Reenable debugging options.

* Mon Mar 09 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc3.git0.1
- Linux v4.0-rc3
- Disable debugging options.

* Sun Mar  8 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- ARMv7: add patches to fix crash on boot for some devices on multiplatform

* Fri Mar 06 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc2.git2.1
- Linux v4.0-rc2-255-g5f237425f352

* Thu Mar 05 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc2.git1.1
- Linux v4.0-rc2-150-g6587457b4b3d
- Reenable debugging options.

* Wed Mar 04 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Enable MLX4_EN on ppc64/aarch64 (rhbz 1198719)

* Tue Mar 03 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc2.git0.1
- Linux v4.0-rc2
- Enable CONFIG_CM32181 for ALS on Carbon X1
- Disable debugging options.

* Tue Mar 03 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc1.git3.1
- Linux v4.0-rc1-178-g023a6007a08d

* Mon Mar 02 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch to fix nfsd soft lockup (rhbz 1185519)
- Enable ET131X driver (rhbz 1197842)
- Enable YAMA (rhbz 1196825)

* Sat Feb 28 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- ARMv7 OMAP updates, fix panda boot

* Fri Feb 27 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc1.git2.1
- Linux v4.0-rc1-36-g4f671fe2f952

* Wed Feb 25 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add support for AR5B195 devices from Alexander Ploumistos (rhbz 1190947)

* Tue Feb 24 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc1.git1.1
- Linux v4.0-rc1-22-gb24e2bdde4af
- Reenable debugging options.

* Tue Feb 24 2015 Richard W.M. Jones <rjones@redhat.com> - 4.0.0-0.rc1.git0.2
- Add patch to fix aarch64 KVM bug with module loading (rhbz 1194366).

* Tue Feb 24 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Minor ARM config update

* Mon Feb 23 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc1.git0.1
- Add patch for HID i2c from Seth Forshee (rhbz 1188439)

* Mon Feb 23 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Linux v4.0-rc1
- CVE-2015-0275 ext4: fallocate zero range page size > block size BUG (rhbz 1193907 1195178)
- Disable debugging options.

* Fri Feb 20 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.20.0-0.rc0.git10.1
- Linux v3.19-8975-g3d883483dc0a
- Add patch to fix intermittent hangs in nouveau driver
- Move mtpspi and related mods to kernel-core for VMWare guests (rhbz 1194612)

* Wed Feb 18 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.20.0-0.rc0.git9.1
- Linux v3.19-8784-gb2b89ebfc0f0

* Wed Feb 18 2015 Kyle McMartin <kyle@fedoraproject.org> - 3.20.0-0.rc0.git8.2
- kernel-arm64.patch: Revert dropping some of the xgene fixes we carried
  against upstream. (#1193875)
- kernel-arm64-fix-psci-when-pg.patch: make it simpler.
- config-arm64: turn on CONFIG_DEBUG_SECTION_MISMATCH.

* Wed Feb 18 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.20.0-0.rc0.git8.1
- Linux v3.19-8217-gcc4f9c2a91b7

* Tue Feb 17 2015 Kyle McMartin <kyle@fedoraproject.org> - 3.20.0-0.rc0.git7.3
- kernel-arm64.patch turned on.

* Tue Feb 17 2015 Kyle McMartin <kyle@fedoraproject.org> - 3.20.0-0.rc0.git7.2
- kernel-arm64.patch merge, but leave it off.
- kernel-arm64-fix-psci-when-pg.patch: when -pg (because of ftrace) is enabled
  we must explicitly annotate which registers should be assigned, otherwise
  gcc will do unexpected things behind our backs. 

* Tue Feb 17 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.20.0-0.rc0.git7.1
- Linux v3.19-7478-g796e1c55717e
- DRM merge

* Mon Feb 16 2015 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-XXXX-XXXX potential memory corruption in vhost/scsi driver (rhbz 1189864 1192079)
- CVE-2015-1593 stack ASLR integer overflow (rhbz 1192519 1192520)

* Mon Feb 16 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Minor updates for ARMv7/ARM64

* Mon Feb 16 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.20.0-0.rc0.git6.1
- Linux v3.19-6676-g1fa185ebcbce

* Fri Feb 13 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.20.0-0.rc0.git5.1
- Linux v3.19-5015-gc7d7b9867155

* Thu Feb 12 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.20.0-0.rc0.git4.1
- Linux v3.19-4542-g8cc748aa76c9

* Thu Feb 12 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.20.0-0.rc0.git3.1
- Linux v3.19-4020-gce01e871a1d4

* Wed Feb 11 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.20.0-0.rc0.git2.1
- Linux v3.19-2595-gc5ce28df0e7c

* Wed Feb 11 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.20.0-0.rc0.git1.1
- Linux v3.19-463-g3e8c04eb1174
- Reenable debugging options.
- Temporarily disable aarch64 patches

* Mon Feb 09 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-1
- Linux v3.19

* Sat Feb 07 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc7.git3.1
- Linux v3.19-rc7-189-g26cdd1f76a88

* Thu Feb  5 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Allwinner A23 (sun8i) SoC
- Move ARM usb platform options to arm-generic

* Thu Feb 05 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc7.git2.1
- Linux v3.19-rc7-32-g5ee0e962603e

* Wed Feb 04 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc7.git1.1
- Linux v3.19-rc7-22-gdc6d6844111d

* Tue Feb 03 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc7.git0.3
- Add patch to fix NFS backtrace (rhbz 1188638)

* Mon Feb 02 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc7.git0.1
- Linux v3.19-rc7
- Disable debugging options.

* Fri Jan 30 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc6.git3.1
- Linux v3.19-rc6-142-g1c999c47a9f1

* Thu Jan 29 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backport patch from Rob Clark to toggle i915 state machine checks

* Thu Jan 29 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- More ARMv7 updates
- A few more sound config cleanups

* Wed Jan 28 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc6.git2.1
- Linux v3.19-rc6-105-gc59c961ca511

* Tue Jan 27 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Enable SND_SOC and the button array driver on x86 for Baytrail devices

* Tue Jan 27 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc6.git1.1
- Linux v3.19-rc6-21-g4adca1cbc4ce
- Reenable debugging options.

* Mon Jan 26 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc6.git0.1
- Linux v3.19-rc6
- Remove symbolic link hunk from patch-3.19-rc6 (rbhz 1185928)
- Disable debugging options.

* Thu Jan 22 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc5.git2.1
- Linux v3.19-rc5-134-gf8de05ca38b7

* Wed Jan 21 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc5.git1.1
- Linux v3.19-rc5-117-g5eb11d6b3f55
- Reenable debugging options.

* Tue Jan 20 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- More ARM config option cleanups

* Mon Jan 19 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc5.git0.1
- Linux v3.19-rc5
- Disable debugging options.

* Sat Jan 17 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Move Rockchip to ARMv7 generic to support rk32xx on LPAE
- Enable Device Tree Overlays for dynamic DTB
- ARM config updates

* Fri Jan 16 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc4.git4.1
- Linux v3.19-rc4-155-gcb59670870d9

* Thu Jan 15 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Re-enable BUILD_DOCSRC

* Thu Jan 15 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc4.git3.1
- Linux v3.19-rc4-141-gf800c25b7a76

* Wed Jan 14 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc4.git2.1
- Linux v3.19-rc4-46-g188c901941ef
- Enable I40E_VXLAN (rhbz 1182116)

* Tue Jan 13 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Enable Checkpoint/Restore on ARMv7 (rhbz 1146995)

* Tue Jan 13 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add installonlypkg(kernel) to kernel-devel subpackages (rhbz 1079906)

* Tue Jan 13 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc4.git1.1
- Linux v3.19-rc4-23-g971780b70194
- Reenable debugging options.

* Mon Jan 12 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc4.git0.1
- Linux v3.19-rc4
- Disable debugging options.

* Mon Jan 12 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backlight fixes for Samsung and Dell machines (rhbz 1094948 1115713)
- Add various UAS quirks (rhbz 1124119)
- Add patch to fix loop in VDSO (rhbz 1178975)

* Fri Jan 09 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc3.git2.1
- Linux v3.19-rc3-69-g11c8f01b423b

* Wed Jan 07 2015 Kyle McMartin <kyle@fedoraproject.org> - 3.19.0-0.rc3.git1.2
- kernel-arm64.patch: fix up build... no idea if it works.

* Wed Jan 07 2015 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2014-9529 memory corruption or panic during key gc (rhbz 1179813 1179853)

* Wed Jan 07 2015 Josh Boyer <jwboyer@fedoraproject.org> - 3.19.0-0.rc3.git1.1
- Linux v3.19-rc3-38-gbdec41963890
- Enable POWERCAP and INTEL_RAPL options
- Reenable debugging options.

* Tue Jan 06 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Linux v3.19-rc3

* Mon Jan 05 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Linux v3.19-rc2
- Temporarily disable aarch64patches
- Happy New Year

* Sun Dec 28 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Enable F2FS (rhbz 972446)

* Thu Dec 18 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.1-2
- CVE-2014-8989 userns can bypass group restrictions (rhbz 1170684 1170688)
- Fix from Kyle McMartin for target_core_user uapi issue since it's enabled
- Fix dm-cache crash (rhbz 1168434)
- Fix blk-mq crash on CPU hotplug (rhbz 1175261)

* Wed Dec 17 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.1-1
- Linux v3.18.1
- CVE-2014-XXXX isofs: infinite loop in CE record entries (rhbz 1175235 1175250)
- Enable TCM_USER (rhbz 1174986)
- Enable USBIP in modules-extra from Johnathan Dieter (rhbz 1169478)

* Tue Dec 16 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-2
- Add patch from Josh Stone to restore var-tracking via Kconfig (rhbz 1126580)

* Mon Dec 15 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Fix ppc64 boot with smt-enabled=off (rhbz 1173806)
- CVE-2014-8133 x86: espfix(64) bypass via set_thread_area and CLONE_SETTLS (rhbz 1172797 1174374)
- CVE-2014-8559 deadlock due to incorrect usage of rename_lock (rhbz 1159313 1173814)

* Fri Dec 12 2014 Kyle McMartin <kyle@fedoraproject.org>
- build in ahci_platform on aarch64 temporarily.

* Fri Dec 12 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Remove pointless warning in cfg80211 (rhbz 1172543)

* Thu Dec 11 2014 Kyle McMartin <kyle@fedoraproject.org>
- kernel-arm64.patch: update from git.

* Wed Dec 10 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Fix UAS crashes with Seagate and Fresco Logic drives (rhbz 1164945)
- CVE-2014-8134 fix espfix for 32-bit KVM paravirt guests (rhbz 1172765 1172769)

* Tue Dec 09 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-1
- Linux v3.18

* Fri Dec 05 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc7.git3.1
- Linux v3.18-rc7-59-g56c67ce187a8

* Thu Dec 04 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc7.git2.1
- Linux v3.18-rc7-48-g7cc78f8fa02c

* Wed Dec 03 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc7.git1.1
- Linux v3.18-rc7-3-g3a18ca061311

* Mon Dec 01 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc7.git0.1
- Linux v3.18-rc7

* Thu Nov 27 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc6.git1.1
- Linux v3.18-rc6-28-g3314bf6ba2ac
- Gobble Gobble

* Mon Nov 24 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Linux v3.18-rc6
- Add quirk for Laser Mouse 6000 (rhbz 1165206)

* Fri Nov 21 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Move TPM drivers to main kernel package (rhbz 1164937)

* Wed Nov 19 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Disable SERIAL_8250 on s390x (rhbz 1158848)

* Mon Nov 17 2014 Kyle McMartin <kyle@fedoraproject.org> - 3.18.0-0.rc5.git0.2
- Re-merge kernel-arm64.patch

* Mon Nov 17 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc5.git0.1
- Linux v3.18-rc5
- Disable debugging options.

* Fri Nov 14 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Enable I40EVF driver (rhbz 1164029)

* Fri Nov 14 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc4.git2.1
- Linux v3.18-rc4-184-gb23dc5a7cc6e

* Thu Nov 13 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch for MS Surface Pro 3 Type Cover (rhbz 1135338)
- CVE-2014-7843 aarch64: copying from /dev/zero causes local DoS (rhbz 1163744 1163745)

* Thu Nov 13 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc4.git1.1
- Linux v3.18-rc4-52-g04689e749b7e
- Reenable debugging options.

* Wed Nov 12 2014 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2014-7841 sctp: NULL ptr deref on malformed packet (rhbz 1163087 1163095)

* Tue Nov 11 2014 Kyle McMartin <kyle@fedoraproject.org> - 3.18.0-0.rc4.git0.2
- Re-enable kernel-arm64.patch, and fix up merge conflicts with 3.18-rc4

* Mon Nov 10 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Fix Samsung pci-e SSD handling on some macbooks (rhbz 1161805)

* Mon Nov 10 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc4.git0.1
- Linux v3.18-rc4
- Temporarily disable aarch64patches
- Disable debugging options.

* Fri Nov 07 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc3.git4.1
- Linux v3.18-rc3-82-ged78bb846e8b

* Thu Nov 06 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc3.git3.1
- Linux v3.18-rc3-68-g20f3963d8f48

* Wed Nov 05 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc3.git2.1
- Linux v3.18-rc3-61-ga1cff6e25e6e

* Tue Nov 04 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc3.git1.1
- Linux v3.18-rc3-31-g980d0d51b1c9
- Reenable debugging options.

* Mon Nov 03 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Enable CONFIG_KXCJK1013
- Add driver for goodix touchscreen from Bastien Nocera

* Mon Nov 03 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc3.git0.1
- Linux v3.18-rc3
- Disable debugging options.

* Thu Oct 30 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc2.git3.1
- Linux v3.18-rc2-106-ga7ca10f263d7

* Wed Oct 29 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc2.git2.1
- Linux v3.18-rc2-53-g9f76628da20f

* Tue Oct 28 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Add quirk for rfkill on Yoga 3 machines (rhbz 1157327)

* Tue Oct 28 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc2.git1.1
- Linux v3.18-rc2-43-gf7e87a44ef60
- Add two RCU patches to fix a deadlock and a hang
- Reenable debugging options.

* Mon Oct 27 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc2.git0.1
- Linux v3.18-rc2
- Disable debugging options.

* Sun Oct 26 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Update ARM config options, some minor cleanups

* Sun Oct 26 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc1.git4.1
- Linux v3.18-rc1-422-g2cc91884b6b3

* Fri Oct 24 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc1.git3.3
- CVE-2014-3610 kvm: noncanonical MSR writes (rhbz 1144883 1156543)
- CVE-2014-3611 kvm: PIT timer race condition (rhbz 1144878 1156537)
- CVE-2014-3646 kvm: vmx: invvpid vm exit not handled (rhbz 1144825 1156534)
- CVE-2014-8369 kvm: excessive pages un-pinning in kvm_iommu_map error path (rhbz 1156518 1156522)
- CVE-2014-8480 CVE-2014-8481 kvm: NULL pointer dereference during rip relative instruction emulation (rhbz 1156615 1156616)

* Fri Oct 24 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc1.git3.1
- Linux v3.18-rc1-280-g816fb4175c29
- Add touchpad quirk for Fujitsu Lifebook A544/AH544 models (rhbz 1111138)

* Wed Oct 22 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc1.git2.1
- Linux v3.18-rc1-221-gc3351dfabf5c
- Add patch to fix wifi on X550VB machines (rhbz 1089731)

* Tue Oct 21 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Drop pinctrl qcom revert now that it's dependencies should be merged

* Tue Oct 21 2014 Kyle McMartin <kyle@fedoraproject.org> - 3.18.0-0.rc1.git1.2
- Re-enable kernel-arm64.patch after updating.
- CONFIG_SERIAL_8250_FINTEK moved to generic since it appears on x86-generic
  and arm64 now.
- CONFIG_IMX_THERMAL=n added to config-arm64.
- arm64: disable BPF_JIT temporarily

* Tue Oct 21 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc1.git1.1
- Linux v3.18-rc1-68-gc2661b806092
- Make LOG_BUF_SHIFT on arm64 the same as the rest of the arches (rhbz 1123327)
- Enable RTC PL031 driver on arm64 (rhbz 1123882)
- Reenable debugging options.

* Mon Oct 20 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc1.git0.1
- Linux v3.18-rc1
- Disable debugging options.

* Fri Oct 17 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc0.git9.4
- CVE-2014-8086 ext4: race condition (rhbz 1151353 1152608)
- Enable B43_PHY_G to fix b43 driver regression (rhbz 1152502)

* Wed Oct 15 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc0.git9.3
- Revert Btrfs ro snapshot commit that causes filesystem corruption

* Wed Oct 15 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc0.git9.1
- Linux v3.17-9670-g0429fbc0bdc2

* Tue Oct 14 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Add patches to fix elantech touchscreens (rhbz 1149509)

* Tue Oct 14 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc0.git8.1
- Linux v3.17-9283-g2d65a9f48fcd

* Tue Oct 14 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc0.git7.1
- Linux v3.17-8307-gf1d0d14120a8

* Mon Oct 13 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Update armv7/aarch64 config options

* Mon Oct 13 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc0.git6.1
- Linux v3.17-7872-g5ff0b9e1a1da

* Sun Oct 12 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc0.git5.1
- Linux v3.17-7639-g90eac7eee2f4

* Sun Oct 12 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Enable CONFIG_I2C_DESIGNWARE_PCI (rhbz 1045821)

* Fri Oct 10 2014 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2014-7970 VFS: DoS with USER_NS (rhbz 1151095 1151484)

* Fri Oct 10 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc0.git4.1
- Linux v3.17-6136-gc798360cd143

* Thu Oct 09 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc0.git3.1
- Linux v3.17-5585-g782d59c5dfc5

* Thu Oct 09 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc0.git2.1
- Linux v3.17-5503-g35a9ad8af0bb

* Wed Oct 08 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.18.0-0.rc0.git1.1
- Linux v3.17-2860-gef0625b70dac
- Reenable debugging options.
- Temporarily disable aarch64patches
- Add patch to fix ATA blacklist

* Tue Oct 07 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch to fix GFS2 regression (from Bob Peterson)

* Mon Oct 06 2014 Kyle McMartin <kyle@fedoraproject.org>
- enable 64K pages on arm64... (presently) needed to boot on amd seattle
  platforms due to physical memory being unreachable.

* Mon Oct 06 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-1
- Linux v3.17

* Fri Oct 03 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc7.git3.1
- Linux v3.17-rc7-76-g58586869599f
- Various ppc64/ppc64le config changes

* Thu Oct 02 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc7.git2.1
- Linux v3.17-rc7-46-g50dddff3cb9a
- Cleanup dead Kconfig symbols in config-* from Paul Bolle

* Wed Oct 01 2014 Kyle McMartin <kyle@fedoraproject.org>
- Update kernel-arm64.patch from git, again... enable AMD_XGBE on arm64.

* Wed Oct 01 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc7.git1.1
- Linux v3.17-rc7-6-gaad7fb916a10

* Tue Sep 30 2014 Kyle McMartin <kyle@fedoraproject.org> - 3.17.0-0.rc7.git0.2
- Revert some v3.16 changes to mach-highbank which broke L2 cache enablement.
  Will debug upstream separately, but we need F22/21 running there. (#1139762)

* Tue Sep 30 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Don't build Exynos4 on lpae kernel
- Add dts for BananaPi
- Minor ARM updates
- Build 6lowpan modules

* Mon Sep 29 2014 Kyle McMartin <kyle@fedoraproject.org>
- Update kernel-arm64.patch from git.

* Mon Sep 29 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc7.git0.1
- Linux v3.17-rc7

* Wed Sep 24 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc6.git2.1
- Linux v3.17-rc6-180-g452b6361c4d9

* Tue Sep 23 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Fix return code when adding keys (rhbz 1145318)
- Add patch to fix XPS 13 touchpad issue (rhbz 1123584)

* Tue Sep 23 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc6.git1.1
- Linux v3.17-rc6-125-gf3670394c29f

* Mon Sep 22 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc6.git0.1
- Linux v3.17-rc6
- Revert EFI GOT fixes as it causes boot failures
- Disable debugging options.

* Fri Sep 19 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc5.git5.1
- Linux v3.17-rc5-105-g598a0c7d0932

* Fri Sep 19 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Disable NO_HZ_FULL again
- Enable early microcode loading (rhbz 1083716)

* Fri Sep 19 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc5.git4.1
- Linux v3.17-rc5-63-gd9773ceabfaf
- Enable infiniband on s390x

* Thu Sep 18 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc5.git3.1
- Linux v3.17-rc5-25-g8ba4caf1ee15

* Wed Sep 17 2014 Kyle McMartin <kyle@fedoraproject.org>
- I also like to live dangerously. (Re-enable RCU_FAST_NO_HZ which has been off
  since April 2012. Also enable NO_HZ_FULL on x86_64.)
- I added zipped modules ages ago, remove it from TODO.

* Wed Sep 17 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc5.git2.1
- Linux v3.17-rc5-24-g37504a3be90b
- Fix vmwgfx header include (rhbz 1138759)

* Tue Sep 16 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc5.git1.1
- Linux v3.17-rc5-13-g2324067fa9a4
- Reenable debugging options.

* Mon Sep 15 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc5.git0.1
- Linux v3.17-rc5
- Disable debugging options.

* Fri Sep 12 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc4.git4.1
- Linux v3.17-rc4-244-g5874cfed0b04

* Thu Sep 11 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Enable ACPI_I2C_OPREGION

* Thu Sep 11 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc4.git3.1
- Linux v3.17-rc4-168-g7ec62d421bdf
- Add support for touchpad in Asus X450 and X550 (rhbz 1110011)

* Wed Sep 10 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc4.git2.1
- Linux v3.17-rc4-158-ge874a5fe3efa
- Add patch to fix oops on keyring gc (rhbz 1116347)

* Tue Sep 09 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc4.git1.1
- Linux v3.17-rc4-140-g8c68face5548
- Reenable debugging options.

* Mon Sep 08 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Remove ppc32 support

* Mon Sep  8 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Build tools on ppc64le (rhbz 1138884)
- Some minor ppc64 cleanups

* Mon Sep 08 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc4.git0.1
- Linux v3.17-rc4
- Disable debugging options.

* Fri Sep 05 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc3.git3.1
- Linux v3.17-rc3-94-gb7fece1be8b1

* Thu Sep 04 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc3.git2.1
- Linux v3.17-rc3-63-g44bf091f5089
- Enable kexec bzImage signature verification (from Vivek Goyal)
- Add support for Wacom Cintiq Companion from Benjamin Tissoires (rhbz 1134969)

* Wed Sep 03 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc3.git1.1
- Linux v3.17-rc3-16-g955837d8f50e
- Reenable debugging options.

* Tue Sep 02 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Remove with_extra switch

* Mon Sep 01 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc3.git0.1
- Linux v3.17-rc3
- Disable debugging options.

* Fri Aug 29 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc2.git3.1
- Linux v3.17-rc2-89-g59753a805499

* Thu Aug 28 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Fix NFSv3 ACL regression (rhbz 1132786)

* Thu Aug 28 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc2.git2.1
- Linux v3.17-rc2-42-gf1bd473f95e0
- Don't enable CONFIG_DEBUG_WW_MUTEX_SLOWPATH (rhbz 1114160)

* Wed Aug 27 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc2.git1.1
- Disable streams on via XHCI (rhbz 1132666)
- Linux v3.17-rc2-9-g68e370289c29
- Reenable debugging options.

* Tue Aug 26 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Minor tegra updates due to incorrect nvidia kernel config options

* Tue Aug 26 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc2.git0.1
- Linux v3.17-rc2
- Fixup ARM MFD options after I2C=y change
- Disable debugging options.

* Tue Aug 26 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Minor generic ARMv7 updates
- Build tegra on both LPAE and general ARMv7 kernels (thank srwarren RHBZ 1110963)
- Set CMA to 64mb on LPAE kernel (RHBZ 1127000)

* Mon Aug 25 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc1.git4.1
- Linux v3.17-rc1-231-g7be141d05549
- Add patch to fix NFS oops on /proc removal (rhbz 1132368)

* Fri Aug 22 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Drop userns revert patch (rhbz 917708)

* Fri Aug 22 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc1.git3.1
- Linux v3.17-rc1-99-g5317821c0853

* Thu Aug 21 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc1.git2.1
- Linux v3.17-rc1-51-g372b1dbdd1fb

* Wed Aug 20 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc1.git1.1
- Linux v3.17-rc1-22-g480cadc2b7e0
- Reenable debugging options.

* Mon Aug 18 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc1.git0.1
- Linux v3.17-rc1
- Disable debugging options.

* Sat Aug 16 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc0.git7.1
- Linux v3.16-11452-g88ec63d6f85c

* Fri Aug 15 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc0.git6.1
- Linux v3.16-11383-gc9d26423e56c

* Thu Aug 14 2014 Kyle McMartin <kyle@fedoraproject.org>
- kernel-arm64: resynch with git head (no functional change)

* Thu Aug 14 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc0.git5.1
- Linux v3.16-10959-gf0094b28f303

* Wed Aug 13 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- 3.17 ARMv7 updates
- Cleanup some old removed options
- Disable legacy USB OTG (using new configfs equivilents)

* Tue Aug 12 2014 Kyle McMartin <kyle@fedoraproject.org> 3.17.0-0.rc0.git4.2
- tegra-powergate-header-move.patch: deal with armv7hl breakage
- nouveau_platform-fix.patch: handle nouveau_dev() removal

* Tue Aug 12 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc0.git4.1
- Add updated crash driver from Dave Anderson and re-enable

* Tue Aug 12 2014 Kyle McMartin <kyle@fedoraproject.org>
- kernel-arm64.patch: fix up merge conflict and re-enable

* Tue Aug 12 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Linux v3.16-10473-gc8d6637d0497

* Sat Aug 09 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc0.git3.1
- Linux v3.16-10013-gc309bfa9b481
- Temporarily don't apply crash driver patch

* Thu Aug 07 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.17.0-0.rc0.git2.1
- Linux v3.16-7503-g33caee39925b

* Tue Aug 05 2014 Kyle McMartin <kyle@fedoraproject.org>
- kernel-arm64.patch: fix up merge conflict and re-enable

* Tue Aug 05 2014 Josh Boyer <jwboyer@gmail.com> - 3.17.0-0.rc0.git1.1
- Linux v3.16-3652-gf19107379dbc
- Reenable debugging options.

* Mon Aug 04 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-1
- Linux v3.16
- Disable debugging options.

* Sun Aug  3 2014 Peter Robinson <pbrobinson@redhat.com>
- Minor config updates for Armada and Sunxi ARM devices

* Fri Aug 01 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc7.git4.1
- Linux v3.16-rc7-84-g6f0928036bcb

* Thu Jul 31 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc7.git3.1
- Linux v3.16-rc7-76-g3a1122d26c62

* Wed Jul 30 2014 Kyle McMartin <kyle@fedoraproject.org>
- kernel-arm64.patch: fix up merge conflict and re-enable

* Wed Jul 30 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc7.git2.1
- Linux v3.16-rc7-64-g26bcd8b72563
- Temporarily disable aarch64patches

* Wed Jul 30 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Apply different patch from Milan Broz to fix LUKS partitions (rhbz 1115120)

* Tue Jul 29 2014 Kyle McMartin <kyle@fedoraproject.org>
- kernel-arm64.patch: update from upstream git.

* Tue Jul 29 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc7.git1.1
- Linux v3.16-rc7-7-g31dab719fa50
- Reenable debugging options.

* Mon Jul 28 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Make sure acpi brightness_switch is disabled (like forever in Fedora)
- CVE-2014-5077 sctp: fix NULL ptr dereference (rhbz 1122982 1123696)

* Mon Jul 28 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc7.git0.1
- Linux v3.16-rc7
- Disable debugging options.

* Mon Jul 28 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Add patch to fix loading of tegra drm using device tree

* Sat Jul 26 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc6.git3.1
- Linux v3.16-rc6-139-g9c5502189fa0

* Fri Jul 25 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc6.git2.1
- Linux v3.16-rc6-118-g82e13c71bc65
- Fix selinux sock_graft hook for AF_ALG address family (rhbz 1115120)

* Thu Jul 24 2014 Kyle McMartin <kyle@fedoraproject.org>
- kernel-arm64.patch: update from upstream git.
- arm64: update config-arm64 to include PCI support.

* Thu Jul 24 2014 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2014-5045 vfs: refcount issues during lazy umount on symlink (rhbz 1122471 1122482)
- Fix regression in sched_setparam (rhbz 1117942)

* Tue Jul 22 2014 Justin M. Forbes <jforbes@fedoraproject.org> - 3.16.0-0.rc6.git1.1
- Linux v3.16-rc6-75-g15ba223
- Reenable debugging options.

* Mon Jul 21 2014 Justin M. Forbes <jforbes@fedoraproject.org> - 3.16.0-0.rc6.git0.1
- Linux v3.16-rc6
- Disable debugging options.

* Mon Jul 21 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Minor ARMv7 config update

* Thu Jul 17 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc5.git2.1
- Linux v3.16-rc5-143-gb6603fe574af

* Wed Jul 16 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Enable hermes prism driver (rhbz 1120393)

* Wed Jul 16 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc5.git1.1
- Linux v3.16-rc5-130-g2da294474093
- Reenable debugging options.

* Mon Jul 14 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc5.git0.1
- Linux v3.16-rc5
- Fix i915 regression with external monitors (rhbz 1117008)
- Disable debugging options.

* Sat Jul 12 2014 Tom Callaway <spot@fedoraproject.org>
- Fix license handling (I hope)

* Fri Jul 11 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc4.git3.1
- Linux v3.16-rc4-120-g85d90faed31e

* Thu Jul 10 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Rebase Utilute and BeagleBone patches
- Minor ARM updates
- Enable ISL12057 RTC for ARM (NetGear ReadyNAS)

* Wed Jul 09 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc4.git2.1
- Linux v3.16-rc4-28-g163e40743f73
- Fix bogus vdso .build-id links (rhbz 1117563)

* Tue Jul 08 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc4.git1.1
- Linux v3.16-rc4-20-g448bfad8a185
- Reenable debugging options.

* Sun Jul 06 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc4.git0.1
- Linux v3.16-rc4
- Disable debugging options.

* Fri Jul 04 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc3.git3.1
- Linux v3.16-rc3-149-g034a0f6b7db7

* Wed Jul 02 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc3.git2.1
- Linux v3.16-rc3-62-gd92a333a65a1
- Add patch to fix virt_blk oops (rhbz 1113805)

* Wed Jul 02 2014 Kyle McMartin <kyle@fedoraproject.org>
- arm64: build-in ahci, ethernet, and rtc drivers.

* Tue Jul 01 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc3.git1.1
- Linux v3.16-rc3-6-g16874b2cb867
- Reenable debugging options.

* Tue Jul  1 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Minor ARMv7 cleanup

* Mon Jun 30 2014 Kyle McMartin <kyle@fedoraproject.org>
- kernel-arm64.patch, update from git.

* Mon Jun 30 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc3.git0.1.1
- Linux v3.16-rc3
- Enable USB rtsx drivers (rhbz 1114229)
- Disable debugging options.

* Fri Jun 27 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc2.git4.1
- Linux v3.16-rc2-222-g3493860c76eb

* Fri Jun 27 2014 Hans de Goede <hdegoede@redhat.com>
- Add patch to fix wifi on lenove yoga 2 series (rhbz#1021036)

* Thu Jun 26 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Enable rtl8192ee (rhbz 1113422)

* Thu Jun 26 2014 Kyle McMartin <kyle@fedoraproject.org> - 3.16.0-0.rc2.git3.2
- Add kernel-arm64.patch, which contains AArch64 support destined for upstream.
  ssh://git.fedorahosted.org/git/kernel-arm64.git is Mark Salter's source tree
  integrating these patches on the devel branch. I've added a twiddle to the
  top of the spec file to disable the aarch64 patchset, and also set aarch64
  to nobuildarches, so we still get kernel-headers, but no one accidentally
  installs a non-booting kernel if the patchset causes rejects during a
  rebase.

* Thu Jun 26 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Trimmed changelog, see fedpkg git for earlier history.

* Thu Jun 26 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc2.git3.1
- Linux v3.16-rc2-211-gd7933ab727ed

* Wed Jun 25 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc2.git2.1
- Linux v3.16-rc2-69-gd91d66e88ea9

* Wed Jun 25 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Revert commit that breaks Wacom Intuos4 from Benjamin Tissoires

* Tue Jun 24 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc2.git1.1
- Linux v3.16-rc2-35-g8b8f5d971584
- Reenable debugging options.

* Mon Jun 23 2014 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2014-4508 BUG in x86_32 syscall auditing (rhbz 1111590 1112073)

* Mon Jun 23 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc2.git0.1
- Linux v3.16-rc2
- Disable debugging options.

* Sun Jun 22 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Enable Exynos now it's finally multi platform capable
- Minor TI Keystone update
- ARM config cleanups

* Fri Jun 20 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Bring in intel_pstate regression fixes for BayTrail (rhbz 1111920)

* Fri Jun 20 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc1.git4.1
- Linux v3.16-rc1-215-g3c8fb5044583

* Thu Jun 19 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc1.git3.1
- Linux v3.16-rc1-112-g894e552cfaa3

* Thu Jun 19 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Add missing bits for NVIDIA Jetson TK1 (thanks Stephen Warren)

* Wed Jun 18 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc1.git2.1
- Linux v3.16-rc1-17-ge99cfa2d0634

* Tue Jun 17 2014 Dennis Gilmore <dennis@ausil.us>
- when ipuv3 moved out of staging the config was renamed
- adjust the config to suit

* Tue Jun 17 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc1.git1.1
- Linux v3.16-rc1-2-gebe06187bf2a
- Reenable debugging options.

* Mon Jun 16 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Enable Qualcomm SoCs on ARM

* Mon Jun 16 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc1.git0.1
- Linux v3.16-rc1
- Disable debugging options.

* Mon Jun 16 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- ARM config updates for 3.16

* Sat Jun 14 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc0.git11.1
- Linux v3.15-9930-g0e04c641b199
- Enable CONFIG_RCU_NOCB_CPU(_ALL) (rbhz 1109113)

* Fri Jun 13 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Add patch to fix build failure on aarch64

* Fri Jun 13 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc0.git10.1
- Linux v3.15-9837-g682b7c1c8ea8

* Fri Jun 13 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc0.git9.1
- Linux v3.15-8981-g5c02c392cd23

* Fri Jun 13 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc0.git8.1
- Linux v3.15-8835-g859862ddd2b6

* Fri Jun 13 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc0.git7.1
- Linux v3.15-8556-gdfb945473ae8

* Fri Jun 13 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc0.git6.1
- Linux v3.15-8351-g9ee4d7a65383

* Thu Jun 12 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc0.git5.1
- Linux v3.15-8163-g5b174fd6472b

* Thu Jun 12 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc0.git4.1
- Linux v3.15-7926-gd53b47c08d8f

* Thu Jun 12 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc0.git3.1
- Linux v3.15-7378-g14208b0ec569

* Wed Jun 11 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc0.git2.1
- Linux v3.15-7283-gda85d191f58a

* Tue Jun 10 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.16.0-0.rc0.git1.1
- Linux v3.15-7218-g3f17ea6dea8b
- Reenable debugging options.

* Mon Jun 09 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-1
- Linux v3.15
- Disable debugging options.

* Mon Jun  9 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Enable USB_EHCI_HCD_ORION to fix USB on Marvell (fix boot for some devices)

* Fri Jun 06 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc8.git4.1
- CVE-2014-3940 missing check during hugepage migration (rhbz 1104097 1105042)
- Linux v3.15-rc8-81-g951e273060d1

* Thu Jun 05 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc8.git3.1
- Linux v3.15-rc8-72-g54539cd217d6

* Wed Jun 04 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc8.git2.1
- Linux v3.15-rc8-58-gd2cfd3105094

* Tue Jun 03 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Add filter-ppc64p7.sh because ppc64p7 is an entirely separate RPM arch

* Tue Jun 03 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc8.git1.2
- Fixes from Hans de Goede for backlight and platform drivers on various
  machines.  (rhbz 1025690 1012674 1093171 1097436 861573)

* Tue Jun 03 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc8.git1.1
- Add patch to install libtraceevent plugins from Kyle McMartin
- Linux v3.15-rc8-53-gcae61ba37b4c
- Reenable debugging options.

* Mon Jun  2 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Minor ARM MMC config updates

* Mon Jun 02 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc8.git0.1
- Linux v3.15-rc8
- Disable debugging options.

* Sat May 31 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc7.git4.2
- Add patch to fix dentry lockdep splat

* Sat May 31 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc7.git4.1
- Linux v3.15-rc7-102-g1487385edb55

* Fri May 30 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc7.git3.1
- Linux v3.15-rc7-79-gfe45736f4134
- Disable CARL9170 on ppc64le

* Thu May 29 2014 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2014-3917 DoS with syscall auditing (rhbz 1102571 1102715)

* Wed May 28 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc7.git2.1
- Linux v3.15-rc7-53-g4efdedca9326

* Wed May 28 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc7.git1.1
- Linux v3.15-rc7-40-gcd79bde29f00
- Reenable debugging options.

* Mon May 26 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc7.git0.1
- Linux v3.15-rc7
- Disable debugging options.

* Sun May 25 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc6.git1.1
- Linux v3.15-rc6-213-gdb1003f23189
- Reenable debugging options.

* Thu May 22 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Enable CONFIG_R8723AU (rhbz 1100162)

* Thu May 22 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc6.git0.1
- Linux v3.15-rc6
- Disable debugging options.

* Wed May 21 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc5.git4.1
- Linux v3.15-rc5-270-gfba69f042ad9

* Tue May 20 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc5.git3.1
- Linux v3.15-rc5-157-g60b5f90d0fac

* Mon May 19 2014 Dan Horák <dan@danny.cz>
- kernel metapackage shouldn't depend on subpackages we don't build

* Thu May 15 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc5.git2.9
- Fix build fail on s390x

* Wed May 14 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc5.git2.8
- Enable autoprov for kernel module Provides (rhbz 1058331)
- Enable xz compressed modules (from Kyle McMartin)

* Tue May 13 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Don't try and merge local config changes on arches we aren't building

* Tue May 13 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc5.git2.1
- Linux v3.15-rc5-77-g14186fea0cb0

* Mon May 12 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc5.git1.1
- Linux v3.15-rc5-9-g7e338c9991ec
- Reenable debugging options.

* Sat May 10 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Enable Marvell Dove support
- Minor ARM cleanups
- Disable some unneed drivers on ARM

* Sat May 10 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc5.git0.1
- Linux v3.15-rc5
- Disable debugging options.

* Fri May 09 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Move isofs to kernel-core

* Fri May 09 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc4.git4.1
- Linux v3.15-rc4-320-gafcf0a2d9289

* Thu May 08 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc4.git3.1
- Linux v3.15-rc4-298-g9f1eb57dc706

* Wed May 07 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc4.git2.1
- Linux v3.15-rc4-260-g38583f095c5a

* Tue May 06 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc4.git1.1
- Linux v3.15-rc4-202-g30321c7b658a
- Reenable debugging options.

* Mon May  5 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Fix some USB on ARM LPAE kernels

* Mon May 05 2014 Kyle McMartin <kyle@fedoraproject.org>
- Install arch/arm/include/asm/xen headers on aarch64, since the headers in
  arch/arm64/include/asm/xen reference them.

* Mon May 05 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc4.git0.1
- Linux v3.15-rc4
- Disable debugging options.

* Mon May  5 2014 Hans de Goede <hdegoede@redhat.com>
- Add use_native_brightness quirk for the ThinkPad T530 (rhbz 1089545)

* Sun May  4 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- General minor ARM cleanups

* Sun May 04 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Fix k-m-e requires on k-m-uname-r provides
- ONE MORE TIME WITH FEELING

* Sat May  3 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Disable OMAP-3 boards (use DT) and some minor omap3 config updates

* Sat May 03 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc3.git5.1
- Linux v3.15-rc3-159-g6c6ca9c2a5b9

* Sat May 03 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch to fix HID rmi driver from Benjamin Tissoires (rhbz 1090161)

* Sat May 03 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Fix up Provides on kernel-module variant packages
- Enable CONFIG_USB_UAS unconditionally per Hans

* Fri May 02 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc3.git4.1
- Linux v3.15-rc3-121-gb7270cce7db7

* Thu May 01 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Rename kernel-drivers to kernel-modules
- Add kernel metapackages for all flavors, not just debug

* Thu May  1 2014 Hans de Goede <hdegoede@redhat.com>
- Add use_native_backlight quirk for 4 laptops (rhbz 983342 1093120)

* Wed Apr 30 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc3.git3.1
- Linux v3.15-rc3-82-g8aa9e85adac6

* Wed Apr 30 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Add kernel-debug metapackage when debugbuildsenabled is set

* Wed Apr 30 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc3.git2.1
- Linux v3.15-rc3-62-ged8c37e158cb
- Drop noarch from ExclusiveArch.  Nothing is built as noarch

* Tue Apr 29 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc3.git1.10
- Make depmod call fatal if it errors or warns

* Tue Apr 29 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Introduce kernel-core/kernel-drivers split for F21 Feature work

* Tue Apr 29 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc3.git1.1
- Linux v3.15-rc3-41-g2aafe1a4d451
- Reenable debugging options.

* Mon Apr 28 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc3.git0.1
- Linux v3.15-rc3
- Disable debugging options.

* Fri Apr 25 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Drop obsolete ARM LPAE patches

* Fri Apr 25 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch from Will Woods to fix fanotify EOVERFLOW issue (rhbz 696821)
- Fix ACPI issue preventing boot on AMI firmware (rhbz 1090746)

* Fri Apr 25 2014 Hans de Goede <hdegoede@redhat.com>
- Add synaptics min-max quirk for ThinkPad Edge E431 (rhbz#1089689)

* Fri Apr 25 2014 Hans de Goede <hdegoede@redhat.com>
- Add a patch to add support for the mmc controller on sunxi ARM SoCs

* Thu Apr 24 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc2.git3.1
- Linux v3.15-rc2-107-g76429f1dedbc

* Wed Apr 23 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc2.git2.1
- Linux v3.15-rc2-69-g1aae31c8306e

* Tue Apr 22 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc2.git1.1
- Linux v3.15-rc2-42-g4d0fa8a0f012
- Reenable debugging options.

* Tue Apr 22 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch to fix Synaptics touchscreens and HID rmi driver (rhbz 1089583)

* Mon Apr 21 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc2.git0.1
- Linux v3.15-rc2
- Disable debugging options.

* Fri Apr 18 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc1.git4.1
- Linux v3.15-rc1-137-g81cef0fe19e0

* Thu Apr 17 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc1.git3.1
- Linux v3.15-rc1-113-g6ca2a88ad820
- Build perf with unwind support via libdw (rhbz 1025603)

* Thu Apr 17 2014 Hans de Goede <hdegoede@redhat.com>
- Update min/max quirk patch to add a quirk for the ThinkPad L540 (rhbz1088588)

* Thu Apr 17 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Drop OMAP DRM hack to load encoder module now it fully supports DT (YAY!)

* Wed Apr 16 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc1.git2.1
- Linux v3.15-rc1-49-g10ec34fcb100

* Tue Apr 15 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc1.git1.1
- Linux v3.15-rc1-12-g55101e2d6ce1
- Reenable debugging options.

* Mon Apr 14 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc1.git0.1
- Linux v3.15-rc1
- Disable debugging options.
- Turn SLUB_DEBUG off

* Mon Apr 14 2014 Hans de Goede <hdegoede@redhat.com>
- Add min/max quirks for various new Thinkpad touchpads (rhbz 1085582 1085697)

* Mon Apr 14 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Minor ARM config changes and cleanups for 3.15 merge window

* Mon Apr 14 2014 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2014-2851 net ipv4 ping refcount issue in ping_init_sock (rhbz 1086730 1087420)

* Sun Apr 13 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git13.1
- Linux v3.14-12812-g321d03c86732

* Fri Apr 11 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git12.1
- Linux v3.14-12380-g9e897e13bd46
- Add queued urgent efi fixes (rhbz 1085349)

* Thu Apr 10 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git11.1
- Linux v3.14-12376-g4ba85265790b

* Thu Apr 10 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Backported HID RMI driver for Haswell Dell XPS machines from Benjamin Tissoires (rhbz 1048314)

* Wed Apr 09 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git10.1
- Linux v3.14-12042-g69cd9eba3886

* Wed Apr 09 2014 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2014-0155 KVM: BUG caused by invalid guest ioapic redirect table (rhbz 1081589 1085016)

* Thu Apr 03 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git9.1
- Linux v3.14-7333-g59ecc26004e7

* Thu Apr 03 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git8.1
- Linux v3.14-7247-gcd6362befe4c

* Wed Apr 02 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git7.1
- Linux v3.14-5146-g0f1b1e6d73cb

* Wed Apr 02 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git6.1
- Linux v3.14-4600-g467cbd207abd

* Wed Apr 02 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git5.1
- Linux v3.14-4555-gb33ce4429938

* Wed Apr 02 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git4.1
- Linux v3.14-4227-g3e75c6de1ac3

* Wed Apr 02 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git3.1
- Linux v3.14-3893-gc12e69c6aaf7

* Tue Apr 01 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git2.1
- CVE-2014-2678 net: rds: deref of NULL dev in rds_iw_laddr_check (rhbz 1083274 1083280)

* Tue Apr 01 2014 Josh Boyer <jwboyer@fedoraproject.org> 
- Linux v3.14-751-g683b6c6f82a6

* Tue Apr 01 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.15.0-0.rc0.git1.1
- Linux v3.14-313-g918d80a13643
- Reenable debugging options.
- Turn on SLUB_DEBUG

* Mon Mar 31 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-1
- Linux v3.14
- Disable debugging options.

* Mon Mar 31 2014 Hans de Goede <hdegoede@redhat.com>
- Fix clicks getting lost with cypress_ps2 touchpads with recent
  xorg-x11-drv-synaptics versions (bfdo#76341)

* Fri Mar 28 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc8.git1.1
- CVE-2014-2580 xen: netback crash trying to disable due to malformed packet (rhbz 1080084 1080086)
- CVE-2014-0077 vhost-net: insufficent big packet handling in handle_rx (rhbz 1064440 1081504)
- CVE-2014-0055 vhost-net: insufficent error handling in get_rx_bufs (rhbz 1062577 1081503)
- CVE-2014-2568 net: potential info leak when ubuf backed skbs are zero copied (rhbz 1079012 1079013)

* Fri Mar 28 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Linux v3.14-rc8-12-g75c5a52
- Reenable debugging options.

* Fri Mar 28 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Enable Tegra 114/124 SoCs
- Re-enable OMAP cpufreq
- Re-enable CPSW PTP option

* Thu Mar 27 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Switch to CONFIG_TRANSPARENT_HUGEPAGE_MADVISE instead of always on

* Tue Mar 25 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc8.git0.1
- Linux v3.14-rc8
- Disable debugging options.

* Mon Mar 24 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Update some generic ARM config options
- Build in TPS65217 for ARM non lpae kernels (fixes BBW booting)

* Fri Mar 21 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc7.git2.1
- Linux v3.14-rc7-59-g08edb33

* Wed Mar 19 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc7.git1.1
- Linux v3.14-rc7-26-g4907cdc
- Reenable debugging options.

* Tue Mar 18 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Enable TEGRA_FBDEV (rhbz 1073960)

* Mon Mar 17 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Add bootwrapper for ppc64le

* Mon Mar 17 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc7.git0.1
- Linux v3.14-rc7
- Disable debugging options.

* Mon Mar 17 2014 Peter Robinson <pbrobinson@fedoraproject.org> 
- Build in Palmas regulator on ARM to fix ext MMC boot on OMAP5

* Fri Mar 14 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc6.git4.1
- Linux v3.14-rc6-133-gc60f7d5

* Thu Mar 13 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc6.git3.1
- Linux v3.14-rc6-41-gac9dc67

* Wed Mar 12 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc6.git2.1
- Fix locking issue in iwldvm (rhbz 1046495)
- Linux v3.14-rc6-26-g33807f4

* Wed Mar 12 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Add some general missing ARM drivers (mostly sound)
- ARM config tweaks and cleanups
- Update i.MX6 dtb

* Tue Mar 11 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc6.git1.1
- CVE-2014-2309 ipv6: crash due to router advertisment flooding (rhbz 1074471 1075064)
- Linux v3.14-rc6-17-g8712a00
- Reenable debugging options.

* Mon Mar 10 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc6.git0.1
- Linux v3.14-rc6
- Disable debugging options.

* Fri Mar 07 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Revert two xhci fixes that break USB mass storage (rhbz 1073180)

* Thu Mar 06 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Fix stale EC events on Samsung systems (rhbz 1003602)
- Add ppc64le support from Brent Baude (rhbz 1073102)
- Fix depmod error message from hci_vhci module (rhbz 1051748)
- Fix bogus WARN in iwlwifi (rhbz 1071998)

* Wed Mar 05 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc5.git2.1
- Linux v3.14-rc5-185-gc3bebc7

* Tue Mar 04 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc5.git1.1
- Linux v3.14-rc5-43-g0c0bd34
- Reenable debugging options.

* Mon Mar 03 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc5.git0.1
- Linux v3.14-rc5
- Disable debugging options.

* Fri Feb 28 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc4.git3.1
- Linux v3.14-rc4-78-gd8efcf3

* Fri Feb 28 2014 Kyle McMartin <kyle@fedoraproject.org>
- Enable appropriate CONFIG_XZ_DEC_$arch options to ensure we can mount
  squashfs images on supported architectures.

* Fri Feb 28 2014 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2014-0102 keyctl_link can be used to cause an oops (rhbz 1071396)

* Thu Feb 27 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc4.git2.1
- Linux v3.14-rc4-45-gd2a0476

* Wed Feb 26 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc4.git1.1
- Linux v3.14-rc4-34-g6dba6ec
- Reenable debugging options.

* Wed Feb 26 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Re-enable KVM on aarch64 now it builds again

* Tue Feb 25 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Fix mounting issues on cifs (rhbz 1068862)

* Mon Feb 24 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Fix lockdep issue in EHCI when using threaded IRQs (rhbz 1056170)

* Mon Feb 24 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc4.git0.1
- Linux v3.14-rc4
- Disable debugging options.

* Thu Feb 20 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc3.git5.1
- Linux v3.14-rc3-219-gd158fc7

* Thu Feb 20 2014 Kyle McMartin <kyle@fedoraproject.org>
- armv7: disable CONFIG_DEBUG_SET_MODULE_RONX until debugged (rhbz#1067113)

* Thu Feb 20 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc3.git4.1
- Linux v3.14-rc3-184-ge95003c

* Wed Feb 19 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc3.git3.1
- Linux v3.14-rc3-168-g960dfc4

* Tue Feb 18 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc3.git2.1
- Linux v3.14-rc3-43-g805937c

* Tue Feb 18 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc3.git1.1
- Linux v3.14-rc3-20-g60f76ea
- Reenable debugging options.
- Fix r8169 ethernet after suspend (rhbz 1054408)
- Enable INTEL_MIC drivers (rhbz 1064086)

* Mon Feb 17 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc3.git0.1
- Linux v3.14-rc3
- Disable debugging options.
- Enable CONFIG_PPC_DENORMALIZATION (from Tony Breeds)

* Fri Feb 14 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc2.git4.1
- Linux v3.14-rc2-342-g5e57dc8
- CVE-2014-0069 cifs: incorrect handling of bogus user pointers (rhbz 1064253 1062578)

* Thu Feb 13 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc2.git3.1
- Linux v3.14-rc2-271-g4675348

* Wed Feb 12 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc2.git2.1
- Linux v3.14-rc2-267-g9398a10

* Wed Feb 12 2014 Josh Boyer <jwboyer@fedoraproject.org>
- Fix cgroup destroy oops (rhbz 1045755)
- Fix backtrace in amd_e400_idle (rhbz 1031296)

* Tue Feb 11 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc2.git1.1
- Linux v3.14-rc2-26-g6792dfe
- Reenable debugging options.

* Mon Feb 10 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc2.git0.1
- Linux v3.14-rc2
- Disable debugging options.

* Sun Feb  9 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Enable CMA on aarch64
- Disable KVM temporarily on aarch64
- Minor ARM config updates and cleanups

* Sun Feb 09 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc1.git5.1.1
- Linux v3.14-rc1-182-g4944790

* Sat Feb 08 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc1.git4.1
- Linux v3.14-rc1-150-g34a9bff

* Fri Feb 07 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc1.git3.1
- Linux v3.14-rc1-86-g9343224

* Thu Feb 06 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc1.git2.1
- Linux v3.14-rc1-54-gef42c58

* Wed Feb 05 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc1.git1.1
- Linux v3.14-rc1-13-g878a876

* Tue Feb 04 2014 Kyle McMartin <kyle@fedoraproject.org>
- Fix %all_arch_configs on aarch64.

* Tue Feb 04 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc1.git0.2
- Add NUMA oops patches
- Reenable debugging options.

* Mon Feb 03 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc1.git0.1
- Linux v3.14-rc1
- Disable debugging options.
- Disable Xen on ARM temporarily as it doesn't build

* Mon Feb  3 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Re-enable modular Tegra DRM driver
- Add SD driver for ZYNQ SoCs

* Fri Jan 31 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git19.1
- Linux v3.13-10637-ge7651b8
- Enable ZRAM/ZSMALLOC (rhbz 1058072)
- Turn EXYNOS_HDMI back on now that it should build

* Thu Jan 30 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git18.1
- Linux v3.13-10231-g53d8ab2

* Thu Jan 30 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git17.1
- Linux v3.13-10094-g9b0cd30
- Add patches to fix imx-hdmi build, and fix kernfs lockdep oops (rhbz 1055105)

* Thu Jan 30 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git16.1
- Linux v3.13-9240-g1329311

* Wed Jan 29 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git15.1
- Linux v3.13-9218-g0e47c96

* Tue Jan 28 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git14.1
- Linux v3.13-8905-g627f4b3

* Tue Jan 28 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git13.1
- Linux v3.13-8789-g54c0a4b
- Enable CONFIG_CC_STACKPROTECTOR_STRONG on x86

* Mon Jan 27 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Build AllWinner (sunxi) on LPAE too (Cortex-A7 supports LPAE/KVM)

* Mon Jan 27 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git12.1
- Linux v3.13-8631-gba635f8

* Mon Jan 27 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git11.1
- Linux v3.13-8598-g77d143d

* Sat Jan 25 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git10.1
- Linux v3.13-8330-g4ba9920

* Sat Jan 25 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git9.1
- Linux v3.13-6058-g2d08cd0
- Quiet incorrect usb phy error (rhbz 1057529)

* Sat Jan 25 2014 Ville Skyttä <ville.skytta@iki.fi>
- Own the /lib/modules dir.

* Sat Jan 25 2014 Peter Robinson <pbrobinson@fedoraproject.org>
- Initial ARM config updates for 3.14
- Disable highbank cpuidle driver
- Enable mtd-nand drivers on ARM
- Update CPU thermal scaling options for ARM

* Fri Jan 24 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git8.1
- Linux v3.13-5617-g3aacd62

* Thu Jan 23 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git7.1
- Linux v3.13-4156-g90804ed

* Thu Jan 23 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git6.1.1
- Revert fsnotify changes as they cause slab corruption for multiple people
- Linux v3.13-3995-g0dc3fd0

* Thu Jan 23 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git5.1
- Linux v3.13-3667-ge1ba845

* Wed Jan 22 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git4.1
- Linux v3.13-3477-gdf32e43

* Wed Jan 22 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git3.1
- Linux v3.13-3260-g03d11a0

* Wed Jan 22 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git2.1
- Linux v3.13-2502-gec513b1

* Tue Jan 21 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.14.0-0.rc0.git1.1
- Linux v3.13-737-g7fe67a1
- Reenable debugging options.  Enable SLUB_DEBUG

* Mon Jan 20 2014 Kyle McMartin <kyle@fedoraproject.org>
- Enable CONFIG_KVM on AArch64.

* Mon Jan 20 2014 Josh Boyer <jwboyer@fedoraproject.org> - 3.13.0-1
- Linux v3.13
- Disable debugging options.
- Use versioned perf man pages tarball

###
# The following Emacs magic makes C-c C-e use UTC dates.
# Local Variables:
# rpm-change-log-uses-utc: t
# End:
###
