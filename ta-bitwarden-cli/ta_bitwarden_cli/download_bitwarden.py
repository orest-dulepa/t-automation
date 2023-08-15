import zipfile
import platform
import os
import requests
import subprocess

from pathlib import Path


class DownloadBitwarden(object):
    """
    Purpose of this class is only downloading of BitWarden CLI
    """

    @staticmethod
    def download_bitwarden():
        """
        Static method that does downloading of CLI corresponding to execution env
        Available environments:
          - linux
          - macos
          - windows
        """
        platforms = {"linux": "linux", "darwin": "macos", "windows": "windows"}
        p = platforms[platform.system().lower()]
        bitwarden_url = (
            "https://vault.bitwarden.com/download/?app=cli&platform={}".format(p)
        )
        cwd = os.getcwd()
        path_to_exe_file = ""
        moved = False

        print("\nDownloading BitWarden binary for {}...\n".format(p))

        path_to_zip_file = os.path.join(cwd, "bitwarden.zip")
        r = requests.get(
            bitwarden_url,
            allow_redirects=True,
        )

        open(path_to_zip_file, "wb").write(r.content)
        with zipfile.ZipFile(path_to_zip_file, "r") as zip_ref:
            zip_ref.extract(zip_ref.namelist()[0], cwd)
            path_to_exe_file = os.path.join(cwd, zip_ref.namelist()[0])

        print(
            "\nSuccessfully extracted BitWarden binary to {}\n".format(path_to_exe_file)
        )

        if platform.system().lower() == 'windows':
            environment_path_var: list = os.getenv("PATH").split(";")
            file_name_with_extension: str = 'bw.exe'
        else:
            environment_path_var: list = os.getenv("PATH").split(":")[1:]
            file_name_with_extension: str = 'bw'

        # Try to move CLI binary to PATH
        for path_dir in environment_path_var:
            try:
                Path(path_to_exe_file).rename(os.path.join(path_dir, file_name_with_extension))
                path_to_exe_file = os.path.join(path_dir, file_name_with_extension)
                moved = True
                break
            except:
                continue

        if moved:
            print(
                "\nSuccessfully moved BitWarden binary to {}\n".format(path_to_exe_file)
            )
        else:
            print(
                "\nFailed to move BitWarden binary. Current path is {}\n".format(
                    path_to_exe_file
                )
            )

        if platform.system().lower() != "windows":
            subprocess.run(
                ["chmod", "+x", path_to_exe_file], capture_output=True, text=True
            )

        print(
            subprocess.run(
                [path_to_exe_file, "--help"],
                capture_output=True,
                text=True,
                timeout=180,
            ).stdout
        )

        print("\nEnd of Bitwarden Output\n")
