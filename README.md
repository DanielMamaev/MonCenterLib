# MonCenterLib

![](img/Moncenter.svg)

MonCenterLib is a python library for geodetic monitoring. The library contains a set of programs, methods and tools designed to collect, process, analyze and visualize data for geodetic monitoring.

The library is being developed based on the following concepts:
* open source code;
* the main programming language is Python;
* an object-oriented approach to programming;
* the program code is executed on Linux (soon Winwows) operating system devices;
* the library's software modules are intended for use in software environments such as Jupiter Notebook, for example, Google Colaboratory.

The following functions are implemented in the library:
* module for connection to GNSS receivers, vertical movement sensor and video inclinometer;
* module for converting a set of homogeneous data into file-sharing formats;
* module for processing multiple GNSS measurements in the geodetic monitoring network;
* module for checking quality of GNSS measurements;
* module for downloading files from the CDDIS online archive (board and precise ephemerides, clock corrections, orbit parameters, observation files from stations);
* module for downloading files from the RGS Centre web service (observation files from stations, obtaining information about stations of the FAGS network);
* detailed documentation and examples of using the program code.

The MonCenterLib library needs to be supplemented with the following modules:
* support for Windows system;
* module for the formation of time series of coordinates of points in the geodetic network;
* module for processing measurement results performed using the (VIM) video inclinometer in real time and in post-processing;
* module for the formation of time series of changes in the angles of inclination of controlled elements in the geodetic network;
* module for processing measurement results using the projected vertical movement sensor (VMS) in real time and in post-processing;
* module for the formation of time series of changes in the vertical coordinates of geodetic monitoring points;
* module for interaction with the geodetic monitoring database;
* module for tracking acceptable values of deviations of geodetic monitoring parameters;
* module for processing time series of the geodetic network in order to obtain estimates of the condition of the monitoring object.

## Modules

|Package|Module|Class|Description|Status|
|---|---|---|---|---|
|root |stream2file|Stream2File |This class is used to convert a stream to a file. You can choose type of connections: serial and tcpcli and NTRIP. |Ready |
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

1. Download and unpack repository;
2. Move to directory MonCenterLib;
3. Don't forget to enable the python virtual environment;
4. Run `pip install .`
5. Ready to use.


### Install in Google Colab

1. Download repository. `!git clone https://github.com/DanielMamaev/MonCenterLib.git`
2. Move to MonCenterLib directory and run `!cd MonCenterLib && pip install .`
3. Ready to use.

## Documentation and usage example
* See documentation [here](https://moncenterlib.readthedocs.io/)
* See examples code [here](examples/README.md)

## Release History

* 1.0.0
    * Work in progress

## Contacts
Official e-mail:
+ moncenter@moncenter.ru
+ support@moncenter.ru

Authors:
- Mamaev D.S. – mamaev.s.d@gmail.com
- Mareev A.V. – mareevavssugt@gmail.com
- Karpik A. P. - rektorat@ssga.ru

![](img/ssugt.png)

Site RU: [https://sgugit.ru/](https://sgugit.ru/) - Site EN: [https://sgugit.ru/en/](https://sgugit.ru/en/)