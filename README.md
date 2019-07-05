# Welcome to KernelCI

This repository provides the core functions used on
[kernelci.org](https://kernelci.org) to monitor upstream Linux kernel branches,
build many kernel variants, run tests, run bisections and schedule email
reports.

This software can also be used to set up an independent instance and to build
any arbitrary kernel branches and run any arbitrary tests.

You can find some general information as well as detailed technical
instructions on the KernelCI
[wiki](https://github.com/kernelci/kernelci-doc/wiki/KernelCI).


# Contents of this repository


## Configuration files

All the builds are configured in [`build-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/master/build-configs.yaml), with the list of
branches to monitor and which kernel variants to build for each of them.

Then all the tests are configured in [`test-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/master/test-configs.yaml) with the list of
devices, test suites and which tests to run on which devices.

Details for the format of these files can be found on the wiki pages for
[build configurations](https://github.com/kernelci/kernelci-doc/wiki/Build-configurations)
and [test configurations](https://github.com/kernelci/kernelci-doc/wiki/Test-configurations).


## Python modules

There are Python modules in the `kernelci` package to parse and use the
configuration data from the YAML files, as well as the
[`kci_build`](https://github.com/kernelci/kernelci-core/blob/master/kci_build)
command line tool to access this data directly and implement automated build
jobs.  Each module has some Python docstrings and the command line tool has
detailed help messages for each command it can run.


## Jenkins jobs

All the automated jobs on kernelci.org are run in Jenkins.  Some legacy scripts
are still being used in "freestyle" projects but they are gradually being
replaced with Pipeline jobs.  Each Pipeline job has a `.jpl` file located in
the `jenkins` directory:

* [`jenkins/monitor.jpl`](https://github.com/kernelci/kernelci-core/tree/master/jenkins/monitor.jpl) to monitor kernel branches
* [`jenkins/build-trigger.jpl`](https://github.com/kernelci/kernelci-core/tree/master/jenkins/build-trigger.jpl) to trigger all the builds for a kernel revision
* [`jenkins/build.jpl`](https://github.com/kernelci/kernelci-core/tree/master/jenkins/build.jpl) to build each individual kernel
* [`jenkins/bisect.jpl`](https://github.com/kernelci/kernelci-core/tree/master/jenkins/bisect.jpl) to run boot bisections
* [`jenkins/buster.jpl`](https://github.com/kernelci/kernelci-core/tree/master/jenkins/buster.jpl) to build a Debian Buster file system

There are other variants based on `stretch.jpl` to build other file systems
with extra tools needed to run specific test suites.

In addition to the job files, there are also some common library files located
in the
[`src/org/kernelci`](https://github.com/kernelci/kernelci-core/tree/master/src/org/kernelci)
directory.


## Dockerfiles

Each Jenkins Pipeline job runs in a Docker container.  The Docker images used
by these containers are built from `jenkins/dockerfiles` and pushed to the
[`kernelci Docker repositories`](https://cloud.docker.com/u/kernelci/repository/list).


## Test templates

The kernelci.org tests typically run in [LAVA](https://lavasoftware.org/).
Each LAVA test is generated using template files which can be found in the
[`templates`](https://github.com/kernelci/kernelci-core/tree/master/templates)
directory.

# Reproducing KernelCI steps locally

## Kernel builds

Sample commands to build a kernel locally from linux-next:

1. Optional: set up a local mirror
If you already have a linux check out:
```
git clone \
  --mirror git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git \
  --reference=~/src/linux linux-mirror.git
```
Then to update the mirror, or create it if you skipped the command above:

```
./kci_build update_mirror --config=next --mirror=linux-mirror.git
```

2. Create a local check-out (or update an existing one when running this again)
```
./kci_build update_repo --config=next --kdir=linux --mirror=linux-mirror.git
```
Optionally, to generate additional config fragments (e.g. to then build `defconfig+kselftest`):
```
./kci_build generate_fragments --config=next --kdir=linux
```

3. Build the kernel with defconfig
```
./kci_build build_kernel --defconfig=defconfig --arch=x86 --build-env=gcc-7 --kdir=linux
```

To see the compiler output, add `--verbose`.
The output can be found in `linux/build`.

To build again without regenerating the kernel config file, just omit the `--defconfig` argument:
```
./kci_build build_kernel --arch=x86 --build-env=gcc-7 --kdir=linux
```

Note: the build-env option is only used to populate the meta-data for the KernelCI database, it is not downloading a build environment.  A future improvement would be to enable using a Docker image as with Jenkins builds (`jenkins/build.jpl`).

4. Install the kernel binaries in a local directory
```
./kci_build install_kernel --config=next --kdir=linux
```

See the output in `linux/_install_`.

5. If you have a kernelci-backend instance running, you can send the kernel and also the meta-data with these commands:
```
./kci_build push_kernel --kdir=linux --api=https://localhost:12345 --token=1234-5678
./kci_build publish_kernel --kdir=linux --api=https://localhost:12345 --token=1234-5678
```
Alternatively, to store the meta-data locally in a JSON file:
```
./kci_build publish_kernel --kdir=linux --json-path=build-meta.json
```
