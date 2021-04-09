import json
import argparse
import pathlib
import shutil

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-ci", "--ci_file", action="store")

    args = parser.parse_args()
    ci_file = args.ci_file

    with open(ci_file) as f:
      ci = json.load(f)
    name = ci['name']
    deploy = ci['deploy']

    src_path = pathlib.Path(f"{deploy['context']}/{deploy['template']}")
    dst_path = pathlib.Path(f"{name}")
    shutil.copytree(src_path, dst_path)

    src_path = pathlib.Path(f"{deploy['context']}/{deploy['trace']}")
    shutil.copy(src_path, dst_path)
    src_path = pathlib.Path(f"{deploy['context']}/{deploy['trace']}_etc_passwd")
    shutil.copy(src_path, dst_path)
    src_path = pathlib.Path(f"{deploy['context']}/{deploy['trace']}_etc_group")
    shutil.copy(src_path, dst_path)
    src_path = pathlib.Path(ci_file)
    shutil.copy(src_path, dst_path)

    dst_path = pathlib.Path(f"{name}/node_resume.lst")
    with dst_path.open("w") as f:
       f.write(deploy['nodelist'])

