# MSE-TSM-CloudSys

## Members

- Villagrasa Diego: AWS, GCE
- Bédrunes Nicolas: AWS, SwitchEngine
- Phung Thomas: GCE, Exoscale
- Schroeter Maxime: Azure, Exoscale
- Jaquet Vincent: SwitchEngine, Azure

## Application deployed

https://github.com/TheSnekySnek/SatNOGS-Tracker-Cloud

## Repository GIT with all deployments programs

https://github.com/Vinrobot/MSE-TSM-CloudSys

## Description of the application

The goal of the application used in this project is to display a map of live, past and future communications between satellites and the SatNOGS network, an open source global network of satellite ground-stations.

The application is divided into 3 layers, presentation layer that displays the map, a business logic layer that serves as an api and provides information on orbits, ground-stations and observations, and finally a data layer in the form of an S3 bucket that stores those informations.


To go into more detail, the first layer of the program displays a map of the earth using Mapbox and fetches the following information from the second layer:

- Orbital information of the satellites to correctly display them on the map

- Ground-station data to display their location and name on the map

- Past and scheduled observations in a -1h +1h time window

On startup, the second layer fetches orbital information(TLE) from NORAD and ground-station information from SatNOGS. Both of these are stored as JSON files in an S3 bucket. The data is updated every 2 hours if a user makes a query.


## Comparison 
|              | Documentation                                                                                                                                                                                                                                                                                                                            | Complexité de l'interface                                                                                                                                                                                                                                                                                                                                                                                                                      | Personnalisation des ressources                                                                                                                                                                                                                                                                                                                                                                 |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Azure        | La documention est assez complète, et il y a beaucoup d'exemples, par exemple au niveau du code Python et également pour l'utilisation de l'interface d'Azure. Il est facile de trouver les ressources que l'on cherche.                                                                                                                 | Il est assez difficile d'utiliser l'interface de Azure car elle est assez complexe. Il y a souvent une grande liste d'options qui sont à la suite, ce qui fait qu'on arrive mal à se retrouver. Il faut également naviguer sur plusieurs pages qui ne sont pas forcément faciles à trouver pour configurer un certain élément, par exemple les Security Groups.                                                                                | Il y a beaucoup d'options de personnalisation de ressources. Par exemple, lors de la création d'une instance, on peut choisir l'architecture de la machine, et on peut choisir avec précision le type de composant (disque, zone, networking). Il y a également des options supplémentaires, tels que des backups, du chiffrement, etc.                                                         |
| Exoscale     | La documentation n'est pas exhaustive et certaines informations sont obsolètes, par exemple l'URL pour accéder au Object Storage. L'API Python est seulement documentée pour certaines méthodes.                                                                                                                                         | L'interface est facile d'utilisation, les différents services proposés sont séparés en catégories logiques (storage, compute, ...). On retrouve facilement les fonctions et paramètres qu'on aimerait utiliser.<br>Le coût des ressources ne sont pas affichées directement sur l'interface, il faut utiliser le calcutateur pour savoir combien vont coûter les ressources.                                                                   | Comparé à d'autres services cloud, il y a moins d'options pour personnaliser certaines ressources. Par exemple, il n'est pas possible de choisir quel type de disque à utiliser avec une instance, ce qui est possible sur d'autres services cloud.                                                                                                                                             |
| SwitchEngine | La documentation d'OpenStack est assez complète et contient quelque exemples permettant de rapidement mettre en place une infrastructure simple et fonctionnelle. Tout de même, il n'est pas aisé de trouver certains paramêtre dans les fonctions/classes, la documentation est plus proche d'une JavaDoc sans commentaire à ce niveau. | A première vue l'interface parait simple et légère avec une navigation menant aux différentes ressources mise à disposition, mais en réalité lorsqu'on commence à aller plus loin, on voit qu'en réalité l'interface nous donne accès à une grande quantité d'actions sur celles-ci (par exemple sur les Compute Instances).<br>Il n'y a pas d'information sur le coût, mais ceci peut venir du fait qu'on n'ait accès au système de paiement. | SwitchEngine / OpenStack offre la possibilité de géré les ressources via des réglages par défauts mais aussi de manière libre en nous laissant la possibilité de choisir des valeurs arbitraires (p.ex. CPU, RAM).<br>Tout de même l'infrastructure reste assez simple et ne pousse pas la personnalisation au maximum (par exemple par rapport à Azure ou on gère le network stack en entier). |
| GCE          | La documentation est complète, mais il est difficile de trouver la page correspondante à l'information que l'on recherche. Il y a beaucoup d'exemples d'utilisation de l'interface, du CLI et du SDK (avec beaucoup de langages différents).                                                                                             | L'interface est complexe a utiliser lorsqu'on recherche une fonction particulière. Il y a beaucoup d'options, et beaucoup de menus. Par contre, dans certains cas, par exmple lors de la création d'une instance, les options sont mises dans un ordre logique, et elles sont séparées par plusieurs sections.                                                                                                                                 | Beaucoup d'options de personnalisation sont proposées. Par exemple, il est possible choisir des options de réseaux qui sont très fines, ou bien on peut choisir un certain type de disque. On peut également créer des modèles, ce qui permet de gagner du temps.                                                                                                                               |
| AWS          | La documentation est très complète pour chacun des services proposés avec des exemples d'utilisation sur le CLI. Par contre, il n'y a presque pas d'exemples de code pour l'utilisation du SDK                                                                                                                                           | L'interface peut prendre du temps à prendre en main en fonction des services que l'on veut utiliser. Les interfaces de création sont bien organisées avec plusieurs étapes. Avec la quantité importante de services proposés il peut être difficile de trouver le bon dans l'interface.                                                                                                                                                        | AWS propose un très large choix d'images grace à sa marketplace et beaucoup de types d'instances différentes en fonction du type de travail à effectuer. On peut créé des images d'instances sans les arrêter ce qui n'est pas le case d'autres clouds comme GCE. Par contre il y a moins de personnalisation au niveau du type de stockage.                                                    |

## Conclusion

It was really interesting to try the different cloud providers. Having tries two of them per group member gave us some insight about the differences and similarities between IaaSes.

We were happy to see that almost all of the IaaS that we used implemented the S3 API for the object storage, which let us use the same code for all deployments with minimal changes. However, SwitchEngine doesn't provide an S3 Object Storage, and Microsoft Azure have their own API and implementation.

Creating instances was not too hard but in some IaaS the interface wasn't really easy to use, especially the network options.

This practical work gave us some insight on how to deploy an application using an IaaS, and how to implement them on future projects.


