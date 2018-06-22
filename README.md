# conan-uploader

### Description

Builds and uploads packages to the user/organization package repository.

### How to use

1. cd to the directory where you want to download packages. The directory should contain json file with this format:

```
{
    "configs": [
        {
            "id": "vc14x64d",
            "args": {"build_type": "Debug", "arch": "x86_64", "compiler": "Visual Studio", "compiler.runtime": "MTd", "compiler.version": "14", "os": "Windows"}
        },
    ]
    "primary": "primary_name",
    "packages": [
        {
            "url": "https://github.com/StiventoUser/conan-date",
            "thread": "testing",
            "secondary": "vkrapivin",
            "configs": [ "vc14x64d" ]
        }
    ]
}
```

Where `primary` is the main remote where you want to upload the packages and `secondary` is an optional additional remote.

Note, that package owner is `primary` until `secondary` is specified which overrides owner for specific package.

`configs` is an optional field which overrides default build configs for specific package. If it's null than all configs are used.

2. Invoke python with the path to this script:

`python3 path/to/script.py`
