# MonCenterLib

Some description

## Modules

|Package|Module|Class|Description|Status|
|---|---|---|---|---|
|gnss |tools4rnx|RtkLibConvbin|This class is based on the RTKLib software package. Convert RTCM, receiver raw data log and RINEX file to RINEX and SBAS/LEX message file. SBAS message file complies with RTKLIB SBAS/LEX message format. See more about RTKLIB here: https://rtklib.com/| Ready|
| |postprocessing|RtkLibPost| |Dev|
| |quality_check|Anubis|This module is designed for monitoring the quality and quantity of multi—GNSS data.See more about G-Nut/Anubis here: https://gnutsoftware.com/software/anubis |Ready|
| |cddis_client|CDDISClient|This module is designed to download one or more GNSS files from the CDDIS archive https://cddis.nasa.gov/ . |Ready|
| |rgs_client|RGSClient|This module allows you to download various GNSS files from the service https://rgs-centre.ru |Ready|
| |gnss_time_series|| |Soon|
|root |stream2file|Stream2File |This class is used to convert a stream to a file. You can choose type of connections: serial and tcpcli and NTRIP. |Ready |
|Soon|| | |

## How to install
### Basic install

1. Download and unpack repository;
2. Move to directory MonCenterLib;
3. Don't forget to enable the python virtual environment;
4. Run `pip install .`
5. Ready to use.


### Install in Google Colab

1. Download repository. `!git clone https://github.com/DanielMamaev/MonCenterLib.git`
2. Move to MonCenterLib directory and run `!cd MonCenterLib && pip install .`
3. Ready to use.

## Usage example

See examples code [here](examples/README.md)

## Release History

* 0.1
    * Work in progress

## Contacts
Official e-mail:
+ moncenter@moncenter.ru
+ support@moncenter.ru

Authors:
- Karpik A. P. - rektorat@ssga.ru
- Mamaev D.S. – mamaev.s.d@gmail.com
- Mareev A.V. – mareevavssugt@gmail.com

![](ssugt.png)

Site RU: [https://sgugit.ru/](https://sgugit.ru/) - Site EN: [https://sgugit.ru/en/](https://sgugit.ru/en/)