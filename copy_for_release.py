
import os
import shutil
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))
DIR_FROM = os.path.dirname(os.path.abspath(__file__))
DIR_TO = Path('dist') / 'click_tkcv_yk'

ignore_folders = [
    '.git',
    '.venv',
    'data',
    'ref',
    'dist',
]

ignore_files = [
    '.gitignore',
    'test.py',
]

create_folders = [
    'data',
]


if __name__ == '__main__':
    """
    DIR_TOに、
    ignore_folders, ignore_filesで指定したものと、このファイル自身を除いた、
    DIR_FROM 内の全てのファイル・フォルダをコピーする。
    """

    if DIR_TO.exists():
        raise FileExistsError(f'{DIR_TO} already exists. Please remove it first.')
    DIR_TO.mkdir(parents=True, exist_ok=True)

    def ignore_func(dir, contents):
        ignored = []
        for name in contents:
            path = Path(dir) / name
            if path.is_dir() and name in ignore_folders:
                ignored.append(name)
            if path.is_file() and name in ignore_files:
                ignored.append(name)
            if path == Path(__file__):
                ignored.append(name)
        return ignored

    shutil.copytree(DIR_FROM, DIR_TO, ignore=ignore_func, dirs_exist_ok=True)

    for folder in create_folders:
        (DIR_TO / folder).mkdir(parents=True, exist_ok=True)

    print(f'Copied files to {DIR_TO}')