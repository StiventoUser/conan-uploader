import os
import ntpath
import pathlib
import json
import re
from subprocess import run

conanWinSettings = [
    {'build_type': 'Debug', 'arch': 'x86_64', 'compiler': 'Visual Studio', 'compiler.runtime': 'MTd', 'compiler.version': '14', 'os': 'Windows'},
    {'build_type': 'Release', 'arch': 'x86_64', 'compiler': 'Visual Studio', 'compiler.runtime': 'MT', 'compiler.version': '14', 'os': 'Windows'},
    {'build_type': 'Debug', 'arch': 'x86', 'compiler': 'Visual Studio', 'compiler.runtime': 'MTd', 'compiler.version': '14', 'os': 'Windows'},
    {'build_type': 'Release', 'arch': 'x86', 'compiler': 'Visual Studio', 'compiler.runtime': 'MT', 'compiler.version': '14', 'os': 'Windows'},

    {'build_type': 'Debug', 'arch': 'x86_64', 'compiler': 'Visual Studio', 'compiler.runtime': 'MTd', 'compiler.version': '15', 'os': 'Windows'},
    {'build_type': 'Release', 'arch': 'x86_64', 'compiler': 'Visual Studio', 'compiler.runtime': 'MT', 'compiler.version': '15', 'os': 'Windows'},
    {'build_type': 'Debug', 'arch': 'x86', 'compiler': 'Visual Studio', 'compiler.runtime': 'MTd', 'compiler.version': '15', 'os': 'Windows'},
    {'build_type': 'Release', 'arch': 'x86', 'compiler': 'Visual Studio', 'compiler.runtime': 'MT', 'compiler.version': '15', 'os': 'Windows'}
]


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


def get_package_info(package_path):
    with open(os.path.join(package_path, 'conanfile.py')) as f:
        file_data = f.read()

    result = {}

    match = re.search(r'name\s*=\s*"([a-zA-z0-9-.]+)"', file_data)
    result['name'] = match.group(1)

    match = re.search(r'version\s*=\s*"([a-zA-Z0-9-.]+)"', file_data)
    result['version'] = match.group(1)

    return result


def create_package(package_info):
    name = package_info['name']
    owner = package_info['owner']
    thread = package_info['thread']

    for settings in conanWinSettings:
        params = ['-s {}=\"{}\"'.format(s, v) for (s, v) in settings.items()]

        command = ' '.join(['conan', 'create',  '.', '{}/{}'.format(owner, thread), *params, '--build=' + name, '--build=missing'])

        print("Executing: {}".format(command))
        run(command, check=True)


def upload_package(package_info, org_name, user_name):
    command = 'conan upload {}/{}@{}/{} -r {} --all'\
        .format(package_info['name'], package_info['version'], package_info['owner'], package_info['thread'], '{}' )

    if user_name:
        run(command.format(user_name))

    run(command.format(org_name))


if __name__ == '__main__':
    with open('packages,json') as f:
        config = json.load(f)

    org_name = config["organization"]

    if not org_name:
        raise Exception("Organization is required")

    for package in config['packages']:
        match = re.search(':\/\/.+?\/.+?\/(.+)', package['url'])
        repo_path = os.path.join(os.getcwd(), match.group(1))

        delete_folder(pathlib.Path(repo_path))

        run('git clone --recurse-submodules {}'.format(package['url']), check=True)

        package_info = get_package_info(repo_path)
        package_info['thread'] = package['thread']

        user_name = package['user'] if 'user' in package else None

        package_info['owner'] = user_name if user_name else org_name

        print("Package info: {}".format(package_info))

        old_dir = os.getcwd()
        try:
            os.chdir(repo_path)

            create_package(package_info)
        finally:
            os.chdir(old_dir)

        upload_package(package_info, org_name, user_name)
