import os
from pathlib import Path
import urllib.request
import zipfile
url2rtklib = "http://danisimo.ru:82/index.php/s/GfJ7br5wQwMuZfx/download"

# download RTKLib zip file
print("Download RTKLib zip file")
path2rtklib_zip = str(Path(__file__).resolve().parent) + "/rtklib.zip"
urllib.request.urlretrieve(url2rtklib, path2rtklib_zip)

# unzip RTKLib zip file
print("Unzip RTKLib zip file")
with zipfile.ZipFile(path2rtklib_zip, 'r') as zip_file:
    zip_file.extractall(str(Path(__file__).resolve().parent) + "/")

# make RTKLib
print("Make RTKLib")
PATH_BASE = str(Path(__file__).resolve().parent) + "/RTKLIB-2.4.3-b34"
os.system(f"cd {PATH_BASE}/lib/iers/gcc/ && make")
os.system(f"cd {PATH_BASE}/app/consapp/convbin/gcc/ && make")
os.system(f"cd {PATH_BASE}/app/consapp/rnx2rtkp/gcc/ && make")
