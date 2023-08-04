import os
from pathlib import Path
import urllib.request
import zipfile

url2rtklib = "http://danisimo.ru:82/index.php/s/pjKGC0Ank72rCkX/download"
PATH_BASE = str(Path(__file__).resolve().parent)

# download Anubis zip file
print("Download Anubis tgz file")
path2anubis_zip = PATH_BASE + "/anubis.zip"
urllib.request.urlretrieve(url2rtklib, path2anubis_zip)

# unzip Anubis zip file
print("Unzip Anubis zip file")
with zipfile.ZipFile(path2anubis_zip, 'r') as zip_file:
    zip_file.extractall(PATH_BASE + "/")

# make Anubis
print('Make Anubis')
os.system(f"chmod -R 755 {PATH_BASE}/Anubis/")
os.system(f"cd {PATH_BASE}/Anubis/ && ./autogen.sh")
