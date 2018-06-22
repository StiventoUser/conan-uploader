import os
import ntpath
import pathlib
import json
import re
import platform
import subprocess
import tempfile
import time
import colorama
from colorama import Fore, Back, Style


def wintolin(path):
    path = os.path.abspath(path)
    if path[1:2] == ':':
        drive = path[:1].lower()
        return '/mnt/' + drive + path[2:].replace('\\', '/')


def delete_folder(pth) :
    if not os.path.exists(pth):
        return

    for sub in pth.iterdir() :
        if sub.is_dir() :
            delete_folder(sub)
        else :
            sub.chmod(0o666)
            sub.unlink()
    pth.rmdir()


def run_command(source_command, target_system = None):
    if not target_system:
        target_system = platform.system()

    isWsl = False

    if target_system == 'Windows':
        if platform.system() != 'Windows':
            raise Exception("Building Windows packages on non-Windows system is not supported")

        command = source_command
    elif target_system == 'Linux':
        if platform.system() == 'Linux':
            command = source_command
        elif platform.system() == 'Windows':
            is32bit = platform.architecture()[0] == '32bit'
            system32 = os.path.join(os.environ['SystemRoot'], 'SysNative' if is32bit else 'System32')
            bash = os.path.join(system32, 'bash.exe')

            command = '{} -c "{} > \'{}\'"'.format(bash, source_command, '{}')
            isWsl = True
        else:
            raise Exception("Unknown host system: {}".format(platform.system()))
    else:
        raise Exception("Unknown target system: {}".format(config['os']))

    if not isWsl:
        print(Fore.YELLOW + "Executing: {}".format(command))
        subprocess.check_output(command)
    else:
        with tempfile.NamedTemporaryFile(mode='r', encoding='utf-8') as f:
            command = command.format(wintolin(f.name))

            print("Executing: {}".format(command))
            child = subprocess.Popen(command)

            while 1:
                where = f.tell()
                line = f.readline()
                if not line:
                    return_code = child.poll()
                    if return_code is not None:
                        if return_code != 0:
                            raise Exception("Command return {} exit status.".format(return_code))
                        return

                    time.sleep(1)
                    f.seek(where)
                else:
                    print(line.rstrip())

def load_configs(obj):
    configs = []

    for configObj in obj:
        if not configObj['id'] or not configObj['args']:
            raise Exception("No id or config field was found")

        if configObj['args']['os']:
            target_os = configObj['args']['os']
        else:
            target_os = platform.system()

        configs.append({ 'id': configObj['id'], 'os': target_os, 'args': configObj['args'] })

    return configs

def install_repo(package):
    match = re.search(':\/\/.+?\/.+?\/(.+)', package['url'])
    repo_path = os.path.join(os.getcwd(), match.group(1))

    delete_folder(pathlib.Path(repo_path))

    run_command('git clone --recurse-submodules {}'.format(package['url']))

    return repo_path


def get_package_conan_info(package_path):
    with open(os.path.join(package_path, 'conanfile.py')) as f:
        file_data = f.read()

    result = {}

    match = re.search(r'name\s*=\s*"([a-zA-z0-9-.]+)"', file_data)
    result['name'] = match.group(1)

    match = re.search(r'version\s*=\s*"([a-zA-Z0-9-.]+)"', file_data)
    result['version'] = match.group(1)

    return result


def get_package_build_data(repo_path, package, primary_name, build_configs):
    build_data = get_package_conan_info(repo_path)

    build_data['thread'] = package['thread']
    secondary_name = package['secondary'] if 'secondary' in package else None

    build_data['primary'] = primary_name
    build_data['secondary'] = secondary_name
    build_data['owner'] = secondary_name if secondary_name else primary_name

    build_data['configs'] = [c for c in build_configs if c['id'] in package['configs']]\
        if package['configs'] else build_configs

    return build_data


def create_package(build_data):
    name = build_data['name']
    owner = build_data['owner']
    thread = build_data['thread']

    for config in build_data['configs']:
        params = ['-s {}=\"{}\"'.format(s, v) for (s, v) in config['args'].items()]

        conan_command = ' '.join(
            ['conan', 'create', '.', '{}/{}'.format(owner, thread), *params, '--build=' + name, '--build=missing'])

        run_command(conan_command, config['os'])


def upload_package(build_data):
    command = 'conan upload {}/{}@{}/{} -r {} --all'\
        .format(build_data['name'], build_data['version'], build_data['owner'], build_data['thread'], '{}' )

    for build_os in ['Windows', 'Linux']:
        if build_data['secondary']:
            run_command(command.format(build_data['secondary']), build_os)

        run_command(command.format(build_data['primary']), build_os)


if __name__ == '__main__':
    colorama.init(autoreset=True)

    with open('packages,json') as f:
        config = json.load(f)

    primary_name = config["primary"]
    build_configs = load_configs(config['configs'])

    if not primary_name:
        raise Exception("Primary remote is required")

    for package in config['packages']:
        print(Fore.CYAN + "-------------------------Building package {}...".format(package['url']))

        repo_path = install_repo(package)

        build_data = get_package_build_data(repo_path, package, primary_name, build_configs)

        print(Fore.CYAN + "Package info: {}".format(build_data))

        old_dir = os.getcwd()
        try:
            os.chdir(repo_path)

            create_package(build_data)
        finally:
            os.chdir(old_dir)

        upload_package(build_data)

        print(Fore.GREEN + "-------------------------Built package {}.".format(build_data['name']))