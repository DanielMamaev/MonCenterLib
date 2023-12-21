# MonCenterLib

Some description

## Modules

|Package|Module|Class|Description|Status|
|---|---|---|---|---|
|GNSS|stream2file| | |Soon |
| |tools4rnx|RtkLibConvbin|This class is based on the RTKLib software package. Convert RTCM, receiver raw data log and RINEX file to RINEX and SBAS/LEX message file. SBAS message file complies with RTKLIB SBAS/LEX message format. See more about RTKLIB here: https://rtklib.com/| Ready|
| |postprocessing|RtkLibPost| |Dev|
| |quality_check|Anubis| |Dev|
| |cddis_client|CDDISClient| |Dev|
| |rgs_client|RGSClient| |Dev|
| |gnss_time_series|| |Soon|
|Soon|| | |

## How to install
### Basic install

1. Download and unpack repository;
2. Install additional programs. `sudo apt install automake gfortran -y`
3. Move to directory MonCenterLib;
4. Don't forget to enable the python virtual environment;
5. Run `pip install .`
6. Ready to use.
7. P.S. After installation, run testing just in case. `python3 -m unittest discover`

### Install in Google Colab

1. Download repository. `!git clone https://github.com/DanielMamaev/MonCenterLib.git`
2. Install additional programs. `!sudo apt install automake gfortran -y`
3. Run `!cd MonCenterLib && pip install .`
4. Ready to use.
7. P.S. After installation, run testing just in case. `!cd MonCenterLib && python3 -m unittest discover`

## Usage example

See examples code [here](examples/)

## Release History

* 0.1
    * Work in progress

## Contacts
Official mail:
+ moncenter@moncenter.ru
+ support@moncenter.ru

Authors:
- Karpik A. P. - rektorat@ssga.ru
- Mamaev D.S. – mamaev.s.d@gmail.com
- Mareev A.V. – mareevavssugt@gmail.com

![](ssugt.png)

Site RU: [https://sgugit.ru/](https://sgugit.ru/) - Site EN: [https://sgugit.ru/en/](https://sgugit.ru/en/)