import zipfile
from pathlib import Path


def extract_zip(file_path, output_folder):

    Path(output_folder).mkdir(
        parents=True,
        exist_ok=True
    )

    with zipfile.ZipFile(file_path) as zip_ref:

        zip_ref.extractall(output_folder)

    return output_folder