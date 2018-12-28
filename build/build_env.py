#!/usr/bin/env python3
import os
import shutil
import sys

from pyfastogt import run_command
from pyfastogt import system_info
from pyfastogt import utils

OPENSSL_SRC_ROOT = "https://www.openssl.org/source/"
ARCH_OPENSSL_COMP = "gz"
ARCH_OPENSSL_EXT = "tar." + ARCH_OPENSSL_COMP
# ROCKSDB_BRANCH = 'v5.10.2'
g_script_path = os.path.realpath(sys.argv[0])


def print_usage():
    print("Usage:\n"
          "[optional] argv[1] platform\n"
          "[optional] argv[2] architecture\n"
          "[optional] argv[3] build system for common/qscintilla/libssh2 (\"ninja\", \"make\", \"gmake\")\n")


def print_message(progress, message):
    print(message.message())
    sys.stdout.flush()


class BuildRequest(object):
    def __init__(self, platform, arch_bit, dir_path):
        platform_or_none = system_info.get_supported_platform_by_name(platform)

        if not platform_or_none:
            raise utils.BuildError('invalid platform')

        arch = platform_or_none.architecture_by_arch_name(arch_bit)
        if not arch:
            raise utils.BuildError('invalid arch')

        build_dir_path = os.path.abspath(dir_path)
        if os.path.exists(build_dir_path):
            shutil.rmtree(build_dir_path)

        os.mkdir(build_dir_path)
        os.chdir(build_dir_path)

        self.build_dir_path_ = build_dir_path

        self.platform_ = platform_or_none.make_platform_by_arch(arch, platform_or_none.package_types())
        print("Build request for platform: {0}, arch: {1} created".format(platform, arch.name()))

    def __get_system_libs(self):
        platform = self.platform_
        platform_name = platform.name()
        arch = platform.arch()
        dep_libs = []

        if platform_name == 'linux':
            distribution = system_info.linux_get_dist()
            if distribution == 'DEBIAN':
                dep_libs = ['git', 'gcc', 'g++', 'yasm', 'pkg-config', 'libtool', 'rpm',
                            'autogen', 'autoconf',
                            'cmake', 'make', 'ninja-build',
                            'libz-dev', 'libbz2-dev', 'lz4-dev',
                            'qt5']
            elif distribution == 'RHEL':
                dep_libs = ['git', 'gcc', 'gcc-c++', 'yasm', 'pkgconfig', 'libtool', 'rpm-build',
                            'autogen', 'autoconf',
                            'cmake', 'make', 'ninja-build',
                            'zlib-devel', 'bzip2-devel', 'lz4-devel',
                            'qt5-qtbase-devel', 'qt5-linguist']
        elif platform_name == 'windows':
            if arch.name() == 'x86_64':
                dep_libs = ['git', 'make', 'mingw-w64-x86_64-gcc', 'mingw-w64-x86_64-yasm',
                            'mingw-w64-x86_64-ninja', 'mingw-w64-x86_64-make', 'mingw-w64-x86_64-cmake',
                            'mingw-w64-x86_64-qt5']
            elif arch.name() == 'i386':
                dep_libs = ['git', 'make', 'mingw-w64-i686-gcc', 'mingw-w64-i686-yasm',
                            'mingw-w64-i686-ninja', 'mingw-w64-i686-make', 'mingw-w64-i686-cmake',
                            'mingw-w64-i686-qt5']
        elif platform_name == 'macosx':
            dep_libs = ['git', 'yasm', 'make', 'ninja', 'cmake', 'qt5']
        else:
            raise NotImplemented("Unknown platform '%s'" % platform_name)

        return dep_libs

    def build_system(self):
        platform = self.platform_
        dep_libs = self.__get_system_libs()
        for lib in dep_libs:
            platform.install_package(lib)

        # post install step

    def build_snappy(self, cmake_line, make_install):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/snappy.git', abs_dir_path)
            os.chdir(cloned_dir)

            os.mkdir('build_cmake_release')
            os.chdir('build_cmake_release')
            snappy_cmake_line = list(cmake_line)
            snappy_cmake_line.append('-DBUILD_SHARED_LIBS=OFF')
            snappy_cmake_line.append('-DSNAPPY_BUILD_TESTS=OFF')
            cmake_policy = run_command.CmakePolicy(print_message)
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(snappy_cmake_line, cmake_policy)
            run_command.run_command_cb(make_install, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_common(self, cmake_line, make_install):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/common.git', abs_dir_path)
            os.chdir(cloned_dir)

            os.mkdir('build_cmake_release')
            os.chdir('build_cmake_release')
            common_cmake_line = list(cmake_line)
            common_cmake_line.append('-DQT_ENABLED=ON')
            common_cmake_line.append('-DJSON_ENABLED=ON')
            common_cmake_line.append('-DSNAPPY_USE_STATIC=ON')
            cmake_policy = run_command.CmakePolicy(print_message)
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(common_cmake_line, cmake_policy)
            run_command.run_command_cb(make_install, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_openssl(self, prefix_path):
        abs_dir_path = self.build_dir_path_
        try:
            openssl_default_version = '1.1.1'
            compiler_flags = utils.CompileInfo([], ['no-shared'])
            url = '{0}openssl-{1}.{2}'.format(OPENSSL_SRC_ROOT, openssl_default_version, ARCH_OPENSSL_EXT)
            utils.build_from_sources(url, compiler_flags, g_script_path, prefix_path, './config')
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_libssh2(self, cmake_line, prefix_path, make_install):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/libssh2.git', abs_dir_path)
            os.chdir(cloned_dir)

            os.mkdir('build_cmake_release')
            os.chdir('build_cmake_release')
            libssh2_cmake_line = list(cmake_line)
            libssh2_cmake_line.append('-DBUILD_SHARED_LIBS=OFF')
            libssh2_cmake_line.append('-DCRYPTO_BACKEND=OpenSSL')
            libssh2_cmake_line.append('-DENABLE_ZLIB_COMPRESSION=ON')
            libssh2_cmake_line.append('-DBUILD_EXAMPLES=OFF')
            libssh2_cmake_line.append('-DBUILD_TESTING=OFF')
            libssh2_cmake_line.append('-DOPENSSL_USE_STATIC_LIBS=ON')
            libssh2_cmake_line.append('-DZLIB_USE_STATIC=ON')
            libssh2_cmake_line.append('-DOPENSSL_ROOT_DIR={0}'.format(prefix_path))
            cmake_policy = run_command.CmakePolicy(print_message)
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(libssh2_cmake_line, cmake_policy)
            run_command.run_command_cb(make_install, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_jsonc(self, prefix_path):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/json-c.git', abs_dir_path)
            os.chdir(cloned_dir)

            autogen_policy = run_command.CommonPolicy(print_message)
            autogen_jsonc = ['sh', 'autogen.sh']
            run_command.run_command_cb(autogen_jsonc, autogen_policy)

            configure_jsonc = ['./configure', '--prefix={0}'.format(prefix_path), '--disable-shared',
                               '--enable-static']
            configure_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(configure_jsonc, configure_policy)

            make_jsonc = ['make', 'install']  # FIXME
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(make_jsonc, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_qscintilla(self, cmake_line, make_install):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/qscintilla.git', abs_dir_path)
            qsci_src_path = os.path.join(cloned_dir, 'Qt4Qt5')
            os.chdir(qsci_src_path)

            os.mkdir('build_cmake_release')
            os.chdir('build_cmake_release')
            qscintilla_cmake_line = list(cmake_line)
            cmake_policy = run_command.CmakePolicy(print_message)
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(qscintilla_cmake_line, cmake_policy)
            run_command.run_command_cb(make_install, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_hiredis(self, prefix_path):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/hiredis.git', abs_dir_path)
            os.chdir(cloned_dir)

            make_hiredis = ['make', 'LIBSSH2_ENABLED=ON', 'OPENSSL_ROOT_DIR={0}'.format(prefix_path),
                            'PREFIX={0}'.format(prefix_path), 'install']
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(make_hiredis, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_libmemcached(self, prefix_path):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/libmemcached.git', abs_dir_path)
            os.chdir(cloned_dir)

            bootstrap_policy = run_command.CommonPolicy(print_message)
            bootstrap_libmemcached = ['sh', 'bootstrap.sh']
            run_command.run_command_cb(bootstrap_libmemcached, bootstrap_policy)

            configure_libmemcached = ['./configure', '--prefix={0}'.format(prefix_path), '--disable-shared',
                                      '--enable-static', '--enable-sasl']
            configure_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(configure_libmemcached, configure_policy)

            make_libmemcached = ['make', 'install']  # FIXME
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(make_libmemcached, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_unqlite(self, cmake_line, make_install):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/unqlite.git', abs_dir_path)
            os.chdir(cloned_dir)

            os.mkdir('build_cmake_release')
            os.chdir('build_cmake_release')
            common_cmake_line = list(cmake_line)
            cmake_policy = run_command.CmakePolicy(print_message)
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(common_cmake_line, cmake_policy)
            run_command.run_command_cb(make_install, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_lmdb(self, prefix_path):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/lmdb.git', abs_dir_path)
            os.chdir(cloned_dir)

            os.chdir('libraries/liblmdb')
            make_lmdb = ['make', 'install_static_lib', 'prefix={0}'.format(prefix_path)]  # FIXME
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(make_lmdb, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_leveldb(self, cmake_line, make_install):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/leveldb.git', abs_dir_path)
            os.chdir(cloned_dir)

            os.mkdir('build_cmake_release')
            os.chdir('build_cmake_release')
            common_cmake_line = list(cmake_line)
            common_cmake_line.append('-DBUILD_SHARED_LIBS=OFF')
            common_cmake_line.append('-DLEVELDB_BUILD_TESTS=OFF')
            common_cmake_line.append('-DLEVELDB_BUILD_BENCHMARKS=OFF')
            cmake_policy = run_command.CmakePolicy(print_message)
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(common_cmake_line, cmake_policy)
            run_command.run_command_cb(make_install, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_rocksdb(self, cmake_line, make_install):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/rocksdb.git', abs_dir_path)
            os.chdir(cloned_dir)

            os.mkdir('build_cmake_release')
            os.chdir('build_cmake_release')
            common_cmake_line = list(cmake_line)
            common_cmake_line.append('-DFAIL_ON_WARNINGS=OFF')
            common_cmake_line.append('-DPORTABLE=ON')
            common_cmake_line.append('-DWITH_TESTS=OFF')
            common_cmake_line.append('-DWITH_SNAPPY=ON')
            common_cmake_line.append('-DWITH_ZLIB=ON')
            common_cmake_line.append('-DWITH_LZ4=ON')
            common_cmake_line.append('-DROCKSDB_INSTALL_ON_WINDOWS=ON')
            common_cmake_line.append('-DWITH_TOOLS=OFF')
            common_cmake_line.append('-DWITH_GFLAGS=OFF')
            common_cmake_line.append('-DBUILD_SHARED_LIBS=OFF')
            cmake_policy = run_command.CmakePolicy(print_message)
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(common_cmake_line, cmake_policy)
            run_command.run_command_cb(make_install, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_forestdb(self, cmake_line, make_install):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/forestdb.git', abs_dir_path, None, False)
            os.chdir(cloned_dir)

            os.mkdir('build_cmake_release')
            os.chdir('build_cmake_release')
            forestdb_cmake_line = list(cmake_line)
            forestdb_cmake_line.append('-DBUILD_SHARED_LIBS=OFF')
            cmake_policy = run_command.CmakePolicy(print_message)
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(forestdb_cmake_line, cmake_policy)
            run_command.run_command_cb(make_install, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build_fastonosql_core(self, cmake_line, make_install):
        abs_dir_path = self.build_dir_path_
        try:
            cloned_dir = utils.git_clone('git@github.com:fastogt/fastonosql_core.git', abs_dir_path, None, False)
            os.chdir(cloned_dir)

            os.mkdir('build_cmake_release')
            os.chdir('build_cmake_release')
            fastonosql_core_cmake_line = list(cmake_line)
            fastonosql_core_cmake_line.append('-DJSONC_USE_STATIC=ON')
            fastonosql_core_cmake_line.append('-DSNAPPY_USE_STATIC=ON')
            fastonosql_core_cmake_line.append('-DOPENSSL_USE_STATIC_LIBS=ON')
            cmake_policy = run_command.CmakePolicy(print_message)
            make_policy = run_command.CommonPolicy(print_message)
            run_command.run_command_cb(fastonosql_core_cmake_line, cmake_policy)
            run_command.run_command_cb(make_install, make_policy)
            os.chdir(abs_dir_path)
        except Exception as ex:
            os.chdir(abs_dir_path)
            raise ex

    def build(self, bs):
        cmake_project_root_abs_path = '..'
        if not os.path.exists(cmake_project_root_abs_path):
            raise utils.BuildError('invalid cmake_project_root_path: %s' % cmake_project_root_abs_path)

        if not bs:
            bs = system_info.SUPPORTED_BUILD_SYSTEMS[0]

        prefix_path = self.platform_.arch().default_install_prefix_path()

        generator = bs.cmake_generator_arg()
        build_system_args = bs.cmd_line()
        # bs_name = bs.name()

        # project static options
        prefix_args = '-DCMAKE_INSTALL_PREFIX={0}'.format(prefix_path)
        cmake_line = ['cmake', cmake_project_root_abs_path, generator, '-DCMAKE_BUILD_TYPE=RELEASE', prefix_args]

        make_install = build_system_args
        make_install.append('install')

        # abs_dir_path = self.build_dir_path_

        # self.build_system()
        self.build_snappy(cmake_line, make_install)
        self.build_openssl(prefix_path)  #
        self.build_libssh2(cmake_line, prefix_path, make_install)
        self.build_jsonc(prefix_path)
        self.build_qscintilla(cmake_line, make_install)
        self.build_common(cmake_line, make_install)

        # databases libs builds
        self.build_hiredis(prefix_path)
        self.build_libmemcached(prefix_path)  #
        self.build_unqlite(cmake_line, make_install)
        self.build_lmdb(prefix_path)
        self.build_leveldb(cmake_line, make_install)
        self.build_rocksdb(cmake_line, make_install)
        self.build_forestdb(cmake_line, make_install)  #
        self.build_fastonosql_core(cmake_line, make_install)


if __name__ == "__main__":
    argc = len(sys.argv)

    if argc > 1:
        platform_str = sys.argv[1]
    else:
        platform_str = system_info.get_os()

    if argc > 2:
        arch_bit_str = sys.argv[2]
    else:
        arch_bit_str = system_info.get_arch_name()

    if argc > 3:
        bs_str = sys.argv[3]
        args_bs = system_info.get_supported_build_system_by_name(bs_str)
    else:
        args_bs = None

    request = BuildRequest(platform_str, arch_bit_str, 'build_' + platform_str + '_env')
    request.build(args_bs)
