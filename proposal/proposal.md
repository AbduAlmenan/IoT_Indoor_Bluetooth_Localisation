% Dynamic Advertising for Supermarkets 

We propose a platform to provide location based advertisements in a shopping centre environment. Combining location data with users’ shopping profiles will enable more accurate and timely advertisements for items nearby, as well as informing users of any coupons they may have to use. Further, gathering the individual paths of the customers will help in designing shop layout and future campaigns. 

# Prototype Design

For the initial prototype we will use an Android phone to provide the interactive experience and to act as a communication gateway. A Nordic nRF51-DK will be used to implement all other local functionality, and a cloud service for data processing.

For a production solution human interaction will be via a low power e-reader type screen integrated into the shopping trolley as well as advertisement screens placed throughout the store. The nRF51-DK localisation functionality will be integrated into the handheld shop-as-you-go device. The handheld device will communicate through the existing dedicated uplink and additionally deployed shared BLE gateways.

# Implementation
The nRF51-DK will track BLE beacons placed throughout the store, as well as integrating data from a multi-axis inertial movement sensor. This data will be processed in a cloud service to identify the location of the device. The location data will be gathered and stored for later usage, and the current location (with relevant advertisements) will be returned to the device.

## Handheld device
* Identifies BLE beacons and their signal strength to triangulate location.
* Records and transmit inertial movement data.
* Manages its data storage, and if needed reduce recorded data granularity.
* Continuously approximates location to display preconfigured advertisements.
* Monitors its battery level and, in case of low battery, reduces communication frequency and processor load.
* Ensures the handheld device remains functional for registering purchased items during a whole shopping session.
* Connects to the cloud, using (in order of precedence) shared gateways and its own dedicated uplink.

## Communication Gateway
For the prototype, the gateway will be implemented on the same mobile phone as the phone app for user interaction. 
The gateway will connect to the handheld device using BLE and relay data to a central processing hub (cloud) via a Wi-Fi connection.

The devices and gateways will share a preconfigured set of keys to encrypt data transmissions. These keys can be updated whenever the devices are placed in a charging dock.

## Mobile application
Android App is mainly made for customers, used for pushing notifications and providing user's position in the store. Third party API and SDK, preferably open source, will be used for visualising shopping cart’s position, map, items in promotion and push notifications.

For simplifying the prototype, the manager view will be alongside the user view within the app. External tools will be used to visualise the results of busiest area in the store and the effectiveness of targeted marketing.

## Cloud Services
### Localisation
The cloud will receive, store and aggregate received data to identify shoppers’ locations.
It will estimate the location of the handheld devices by aggregating detected beacon signals and recorded inertial movement sensor readings to reconstruct the path of the device throughout the store. 

### Advertisement Delivery
As the display mechanism will be preloaded with advertisements, the cloud will simply need to specify the ID of the desired ad. This will be based on the shopping profile and current location. For user-specific custom notifications, the system may deliver a full ad instead of using the preconfigured set.

### Data Analytics 
Data collected such as duration at a sectional place will be used to find the busiest area at a shop. This can be visualised via a heatmap on the store map. 

Sensor data from gyroscope, accelerometer and Bluetooth beacons can be used to predict user's direction and position on a map.

The likelihood of the user going to the item after seeing the mobile notifications can be analysed. This gives an insight of the marketing effectiveness with regards to a user's characteristics and the marketed items.

# Evaluation methodology

## Location Accuracy
We will assess beacon, internal measurement, and combined sensor based accuracy separately. Location accuracy metric will be the distance between reported and actual coordinates on the map.

## Power Consumption
The battery level and power draw will be measured during different sleep-wake patterns of the board. We will calculate the effects of various optimisations on estimated battery life.

## Responsiveness
Most factors that determine the responsiveness are external and cannot be controlled. For example, current gateway traffic and BLE to phone responsiveness, shared gateway availability in current location. However, this can be simulated and the delay in user’s location update on the map can be measured to assess resilience to adverse effects.

# Limitations 
Given the small form factor battery powered nature of the platform, we will need to be conscious of power usage. Fortunately the devices will need to last for a single shopping journey, and can be recharged before the next user will use it.

Care will need to be taken to ensure the privacy of the customers and to not leak their shopper profiles. This applies both to communications and the ads displayed locally and publicly. Advertisement content related privacy concerns are out of scope for this platform.

