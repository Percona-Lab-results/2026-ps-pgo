# Building MySQL 9.7.0 from Source

This document describes the process used to build MySQL 9.7.0 from source without Profile-Guided Optimization (PGO), package it as a Docker image, and use it in the benchmark tests.

## Overview

The MySQL 9.7.0 non-PGO build was created to compare performance against the official MySQL 9.7.0 PGO-enabled build. The build process involves:

1. Downloading and extracting MySQL source code
2. Configuring the build with CMake
3. Compiling MySQL from source
4. Packaging the compiled binaries into a Docker image
5. Using the Docker image in benchmark tests

## Build Environment

**System Specifications:**
- **OS**: Ubuntu 24.04 LTS (Noble)
- **CPU**: Intel Xeon Gold 6230 @ 2.10GHz
- **RAM**: 192 GB
- **Compiler**: GCC (system default)

**Build Directory Structure:**
```
~/mysql-9.7.0/           # Source code directory
~/mysql-9.7.0-build/     # Build output directory (separate from source)
~/mysql-docker-build/    # Docker image build context
```

## Prerequisites

### Required Packages

Install build dependencies:

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    libssl-dev \
    libncurses5-dev \
    libbison-dev \
    bison \
    pkg-config \
    libldap2-dev \
    libaio-dev \
    libnuma-dev \
    libsasl2-dev \
    libmecab-dev
```

### Docker

Docker is required to package and run the MySQL build:

```bash
sudo apt-get install docker.io
sudo usermod -aG docker $USER
```

## Build Process

### Step 1: Download MySQL Source

Download MySQL 9.7.0 source code from the official MySQL repository:

```bash
cd ~
wget https://cdn.mysql.com/archives/mysql-9.7/mysql-9.7.0.tar.gz
tar -xzf mysql-9.7.0.tar.gz
```

### Step 2: Configure Build with CMake

Create a separate build directory (recommended practice):

```bash
mkdir ~/mysql-9.7.0-build
cd ~/mysql-9.7.0-build
```

Configure the build using CMake with appropriate flags:

```bash
cmake ~/mysql-9.7.0 \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DCMAKE_INSTALL_PREFIX=/usr/local/mysql \
    -DDOWNLOAD_BOOST=1 \
    -DWITH_BOOST=~/mysql-9.7.0-build/boost \
    -DMYSQL_DATADIR=/var/lib/mysql \
    -DSYSCONFDIR=/etc/mysql \
    -DMYSQL_UNIX_ADDR=/var/run/mysqld/mysqld.sock \
    -DWITH_INNODB_MEMCACHED=1 \
    -DENABLED_LOCAL_INFILE=1 \
    -DWITH_PARTITION_STORAGE_ENGINE=1 \
    -DINSTALL_PLUGINDIR=/usr/lib/mysql/plugin \
    -DWITH_SSL=system \
    -DWITH_ZLIB=bundled \
    -DWITH_MECAB=bundled \
    -DBUNDLE_MECAB=ON
```

**Key Configuration Options:**

- **CMAKE_BUILD_TYPE=RelWithDebInfo**: Optimized build with debug info (-O2 -g -DNDEBUG)
- **DOWNLOAD_BOOST=1**: Automatically download required Boost libraries
- **WITH_SSL=system**: Use system OpenSSL instead of bundled
- **WITH_ZLIB=bundled**: Use bundled zlib
- **BUNDLE_MECAB=ON**: Include MeCab for full-text search

**Important**: This build does **NOT** include PGO flags. The official MySQL 9.7.0 Docker image includes PGO optimizations, but this custom build is compiled without them for comparison purposes.

### Step 3: Compile MySQL

Build MySQL using all available CPU cores:

```bash
make -j$(nproc) 2>&1 | tee build.log
```

**Build Time:** Approximately 30-60 minutes depending on system resources.

**Build Output:**
- Binaries: `~/mysql-9.7.0-build/runtime_output_directory/`
- Libraries: `~/mysql-9.7.0-build/library_output_directory/`
- Plugins: `~/mysql-9.7.0-build/plugin_output_directory/`
- Share files: `~/mysql-9.7.0-build/share/`

### Step 4: Package as Docker Image

Create a Docker build context:

```bash
mkdir -p ~/mysql-docker-build
cd ~/mysql-docker-build
```

Copy the compiled build directory:

```bash
cp -r ~/mysql-9.7.0-build ./
```

Create a `Dockerfile` that layers the custom build on top of the official MySQL base image:

```dockerfile
FROM mysql:9.7.0

# Remove the original MySQL binaries and libraries
RUN rm -rf /usr/bin/mysql* /usr/bin/my* /usr/sbin/mysqld* && \
    rm -rf /usr/lib/mysql /usr/lib/x86_64-linux-gnu/libmysql*

# Create directories
RUN mkdir -p /usr/lib/mysql-custom /usr/lib/mysql/plugin

# Copy the custom MySQL build
COPY mysql-9.7.0-build/runtime_output_directory/ /usr/bin/
COPY mysql-9.7.0-build/library_output_directory/ /usr/lib/mysql-custom/
COPY mysql-9.7.0-build/plugin_output_directory/ /usr/lib/mysql/plugin/
COPY mysql-9.7.0-build/share/ /usr/share/mysql/

# Set library path
ENV LD_LIBRARY_PATH=/usr/lib/mysql-custom:$LD_LIBRARY_PATH

# Ensure mysqld is executable and in the right location
RUN if [ -f /usr/bin/mysqld ]; then \
        ln -sf /usr/bin/mysqld /usr/sbin/mysqld; \
    fi

# Keep the original entrypoint and configuration
ENTRYPOINT ["docker-entrypoint.sh"]
EXPOSE 3306 33060
CMD ["mysqld"]
```

Build the Docker image:

```bash
docker build -t mysql:9.7.0-non-pgo .
```

Save the image for distribution:

```bash
docker save mysql:9.7.0-non-pgo > ~/mysql-non-pgo-9.7.0.tar
gzip ~/mysql-non-pgo-9.7.0.tar
```

## Build Verification

### Verify the Build

Check that the compiled mysqld was built without PGO:

```bash
# Check build type
grep CMAKE_BUILD_TYPE ~/mysql-9.7.0-build/CMakeCache.txt

# Verify compiler flags (should NOT contain -fprofile-use or similar)
grep CMAKE_CXX_FLAGS ~/mysql-9.7.0-build/CMakeCache.txt
```

### Test the Docker Image

Start the MySQL container:

```bash
docker run -d \
    --name mysql-non-pgo-test \
    -e MYSQL_ROOT_PASSWORD=password \
    -p 3307:3306 \
    mysql:9.7.0-non-pgo
```

Connect and verify:

```bash
mysql -h 127.0.0.1 -P 3307 -u root -ppassword -e "SELECT VERSION(), @@version_comment;"
```

Clean up:

```bash
docker stop mysql-non-pgo-test
docker rm mysql-non-pgo-test
```

## Usage in Benchmarks

The Docker image is used in the benchmark scripts via Docker Compose. See the project's benchmark configuration for details on how to specify the custom MySQL image.

### Load Docker Image

On a new system, load the saved image:

```bash
gunzip mysql-non-pgo-9.7.0.tar.gz
docker load < mysql-non-pgo-9.7.0.tar
```

### Configure Benchmarks

The benchmark script can be configured to use this image by specifying:

```bash
./run_metrics.sh "mysql-non-pgo" "9.7.0" [read_only] [binlog_enabled]
```

## Build Artifacts

**Key Files Generated:**

- `~/mysql-9.7.0-build/build.log` - Complete build log (690KB)
- `~/mysql-9.7.0-build/CMakeCache.txt` - CMake configuration cache
- `~/mysql-9.7.0-build/runtime_output_directory/` - mysqld and client binaries
- `~/mysql-9.7.0-build/library_output_directory/` - Shared libraries
- `~/mysql-non-pgo-9.7.0.tar.gz` - Docker image archive (428MB compressed)

## Differences from Official MySQL 9.7.0

The official MySQL 9.7.0 Docker image from Oracle includes:

✅ Profile-Guided Optimization (PGO) enabled  
✅ Enterprise-grade compiler optimizations  
✅ Performance tuning for production workloads  

This custom build:

❌ **No PGO** - Compiled without profile-guided optimization  
✅ Standard optimizations (RelWithDebInfo: -O2 -g -DNDEBUG)  
✅ Same source code version (9.7.0)  
✅ Same features and plugins enabled  

**Performance Difference:** The PGO-enabled official build shows approximately **6.5% better performance** on average across OLTP workloads compared to this non-PGO build. See the main [README.md](README.md) for detailed benchmark results.

## References

- [MySQL Source Building Documentation](https://dev.mysql.com/doc/refman/9.0/en/source-installation.html)
- [CMake Build Options](https://dev.mysql.com/doc/refman/9.0/en/source-configuration-options.html)
- [Profile-Guided Optimization](https://en.wikipedia.org/wiki/Profile-guided_optimization)

---

**Build Date:** May 2026  
**MySQL Version:** 9.7.0  
**Build Type:** RelWithDebInfo (Non-PGO)
