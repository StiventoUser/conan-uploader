import os
import ntpath
from subprocess import run

conanWinSettings = [
    {"build_type": "Debug", "arch": "x86_64", "compiler": "Visual Studio", "compiler.runtime": "MTd", "compiler.version": "14", "os": "Windows"},
    {"build_type": "Release", "arch": "x86_64", "compiler": "Visual Studio", "compiler.runtime": "MT", "compiler.version": "14", "os": "Windows"},
    {"build_type": "Debug", "arch": "x86", "compiler": "Visual Studio", "compiler.runtime": "MTd", "compiler.version": "14", "os": "Windows"},
    {"build_type": "Release", "arch": "x86", "compiler": "Visual Studio", "compiler.runtime": "MT", "compiler.version": "14", "os": "Windows"},

    {"build_type": "Debug", "arch": "x86_64", "compiler": "Visual Studio", "compiler.runtime": "MTd", "compiler.version": "15", "os": "Windows"},
    {"build_type": "Release", "arch": "x86_64", "compiler": "Visual Studio", "compiler.runtime": "MT", "compiler.version": "15", "os": "Windows"},
    {"build_type": "Debug", "arch": "x86", "compiler": "Visual Studio", "compiler.runtime": "MTd", "compiler.version": "15", "os": "Windows"},
    {"build_type": "Release", "arch": "x86", "compiler": "Visual Studio", "compiler.runtime": "MT", "compiler.version": "15", "os": "Windows"}
]


def get_thread(package_name):
    return input("Package {} thread (stable/testing): ".format(package_name))


def create_package(package_info, owner):
    old_dir = os.getcwd()

    try:
        os.chdir(package_info["path"])
        thread = get_thread(package_info["name"])

        for settings in conanWinSettings:
            params = ["-s {}=\"{}\"".format(s, v) for (s, v) in settings.items()]

            command = " ".join(["conan", "create",  ".", "{}/{}".format(owner, thread), *params, "-b=" + package_info["name"]])

            print("Executing: {}".format(command))
            run(command, check=True)
    finally:
        os.chdir(old_dir)


def upload_package(package_info, org_name, user_name):
    command = "conan upload \"{}*\" -r {} --all".format(package_info["name"], "{}")

    if len(user_name) != 0:
        run(command.format(user_name))

    run(command.format(org_name))


if __name__ == "__main__":
    packages = [{ "name": e[len("conan-"):], "path": ntpath.basename(e)} for e in os.listdir(os.getcwd()) if os.path.isdir(e)]

    org_name = input("Organization remote name: ")

    for package in packages:
        user_name = input("User to upload {} (empty to skip): ".format(package["name"]))

        create_package(package, user_name if len(user_name) != 0 else org_name)
        upload_package(package, org_name, user_name)
