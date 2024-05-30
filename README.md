# MonCenterLib

<img src="https://raw.githubusercontent.com/DanielMamaev/MonCenterLib/main/img/Moncenter.svg" alt="drawing" width="500"/>

MonCenterLib is a python library for geodetic monitoring. The library contains programs, designed to collect, process, analyze and visualize data for geodetic time series.

The library is being developed by the following concepts:
* open source code;
* python programming language;
* an object-oriented programming;
* the program code is executed on Linux (soon Windows) operating system;
* the library's software modules are able to use in Jupiter Notebook, Google Colaboratory.

The following functions are implemented in the library:
* connection to GNSS receivers, vertical movement sensor (VMS) and video inclinometer (VIM);
* converting GNSS measurements to RINEX and other formats;
* processing multiple GNSS measurements files in the geodetic monitoring network;
* checking quality of GNSS measurements;
* downloading files from the CDDIS online archive (boardcast and precise ephemerides, clock corrections, orbit parameters, observation files);
* downloading files from the RGS Centre web service (observation files, obtaining information about stations of the FAGN);
* documentation and examples of using the program code.

The MonCenterLib library needs to be supplemented with the following modules:
* supporting for Windows system;
* formation of time series of points in the geodetic network;
* processing  of measurement results of the VIM in real time and in post-processing;
* construction of time series inclination for controlling elements in the geodetic network;
* processing measurement results using the projected VMS in real time and in post-processing;
* interaction with the geodetic monitoring database;
* tracking acceptable values of deviations of geodetic monitoring parameters;
* processing time series of the geodetic network to estimate of the structural stability of the monitoring object.

## Modules

|Package|Module|Class|Description|Status|
|---|---|---|---|---|
|root |stream2file|Stream2File |This class is used to convert a stream to a file. You can choose type of connections: serial, TCP client and NTRIP. |Ready |
|gnss |tools4rnx|RtkLibConvbin|This class is based on the RTKLib software package. Convert RTCM, receiver raw data log and RINEX file to RINEX and SBAS/LEX message file. SBAS message file complies with RTKLIB SBAS/LEX message format. See more about RTKLIB here: https://rtklib.com/| Ready|
|     |postprocessing|RtkLibPost| RTKLIB contains a post processing analysis AP RTKPOST. RTKPOST inputs the standard RINEX 2.10, 2.11, 2.12, 3.00, 3.01, 3.02 (draft) observation data and navigation message files (GPS, GLONASS, Galileo, QZSS, BeiDou and SBAS) and can computes the positioning solutions by various positioning modes including Single‐point, DGPS/DGNSS, Kinematic, Static, PPP‐Kinematic and PPP‐Static. See more about RTKLIB here: https://rtklib.com/ |Ready|
|     |quality_check|Anubis|This module is designed for monitoring the quality and quantity of multi-GNSS data.See more about G-Nut/Anubis here: https://gnutsoftware.com/software/anubis |Ready|
|     |cddis_client|CDDISClient|This module is designed to download one or more GNSS files from the CDDIS archive https://cddis.nasa.gov/ |Ready|
|     |rgs_client|RGSClient|This module allows you to download various GNSS files from the service https://rgs-centre.ru |Ready|
|     |gnss_time_series|| |Soon|
|other| vim | |  Video inclinometer|Soon |
|     | vms | |Vertical movement sensor |Soon |
|analysis|  | | |Soon |


## How to install
### Basic install

1. Don't forget to enable the python virtual environment;
2. Run `python -m pip3 install moncenterlib`
3. Ready to use.


### Install in Google Colab

1. Run `!python -m pip3 install moncenterlib`
2. Ready to use.

### Get the Source Code
MonCenterLib is actively developed on GitHub, where the code is [always available](https://github.com/DanielMamaev/MonCenterLib).

1. You can clone the public repository:
```
git clone https://github.com/DanielMamaev/MonCenterLib
```

2. Once you have a copy of the source, you can embed it in your own Python package, or install it into your site-packages easily:

```
cd moncenterlib
python -m pip install .
```

## Documentation and usage example
* See documentation [here](https://moncenterlib.readthedocs.io/)
* See examples code [here](examples/README.md)

## Release History
* 1.0.2
    * Set timeout for ftps (5m).
    * Fix class Anubis.
    * Add new feature for cddis_client (imput range of dates or input list of dates).
* 1.0.1
    * fix rule for bin files (anubis_2.3_aarch64_linux, convbin_2.4.3-34_aarch64_linux, rnx2rtkp_2.4.3-34_aarch64_linux, str2str_2.4.3-34_aarch64_linux)
    * fix readme file
* 1.0.0
    * First release

## Contacts
Official e-mail:
+ moncenter@moncenter.ru
+ support@moncenter.ru

Authors:
- Mamaev D.S. – mamaev.s.d@gmail.com
- Mareev A.V. – mareevavssugt@gmail.com
- Karpik A. P. - rektorat@ssga.ru

<img src="https://github.com/DanielMamaev/MonCenterLib/blob/main/img/ssugt.png?raw=true" width="400"/>

Site RU: [https://sgugit.ru/](https://sgugit.ru/) - Site EN: [https://sgugit.ru/en/](https://sgugit.ru/en/)