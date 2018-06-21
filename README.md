# conan-uploader

### Description

Builds and uploads packages to the user/organization package repository.

### How to use

1. cd to the directory where you want to download packages. The directory should contain json file with this format:

```
{
    "primary": "primary_name",
    "packages": [
        {
            "url": "https://github.com/StiventoUser/conan-date",
            "thread": "testing",
            "secondary": "vkrapivin"
        }
    ]
}
```

Where `primary` is the main remote where you want to upload the packages and `secondary` is an optional additional remote.

Note, that package owner is `primary` until `secondary` is specified which overrides owner for specific package.

2. Invoke python with the path to this script:

`python3 path/to/script.py`
