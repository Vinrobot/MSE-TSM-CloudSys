# MSE-TSM-CloudSys

## Members

- Villagrasa Diego: AWS, GCE
- Bédrunes Nicolas: AWS, SwitchEngine
- Phung Thomas: GCE, Exoscale
- Schroeter Maxime: Azure, Exoscale
- Jaquet Vincent: SwitchEngine, Azure

## Application deployed

https://github.com/TheSnekySnek/SatNOGS-Tracker-Cloud

## Description of the application

The goal of the application used in this project is to display a map of live, past and future communications between satellites and the SatNOGS network, an open source global network of satellite ground-stations.

The application is divided into 3 layers, presentation layer that displays the map, a business logic layer that serves as an api and provides information on orbits, ground-stations and observations, and finally a data layer in the form of an S3 bucket that stores those informations.


To go into more detail, the first layer of the program displays a map of the earth using Mapbox and fetches the following information from the second layer:

- Orbital information of the satellites to correctly display them on the map

- Ground-station data to display their location and name on the map

- Past and scheduled observations in a -1h +1h time window

On startup, the second layer fetches orbital information(TLE) from NORAD and ground-station information from SatNOGS. Both of these are stored as JSON files in an S3 bucket. The data is updated every 2 hours if a user makes a query.


## Comparison 


## Conclusion

