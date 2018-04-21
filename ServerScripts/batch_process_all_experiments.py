import requests
import math
import numpy as np
import csv
from datetime import date
from time import mktime
from haversine import haversine
from scipy.optimize import minimize

# EXTERNAL SOURCES HAVE BEEN CITED APPROPIATELY AND LOOK AT MAIN FUNCTION FOR STUDENT'S WORK (FINN ZHAN CHEN)

###################### EXISTING SOLUTION FOR TRILATERATION IN 2D ##############################
# Source from https://github.com/noomrevlis/trilateration
# http://en.wikipedia.org/wiki/Trilateration

class point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class circle(object):
    def __init__(self, point, radius):
        self.center = point
        self.radius = radius


def get_two_points_distance(p1, p2):
    return math.sqrt(pow((p1.x - p2.x), 2) + pow((p1.y - p2.y), 2))


def get_two_circles_intersecting_points(c1, c2):
    p1 = c1.center
    p2 = c2.center
    r1 = c1.radius
    r2 = c2.radius

    d = get_two_points_distance(p1, p2)
    # if to far away, or self contained - can't be done
    if d >= (r1 + r2) or d <= math.fabs(r1 - r2):
        return None

    a = (pow(r1, 2) - pow(r2, 2) + pow(d, 2)) / (2 * d)
    h = math.sqrt(pow(r1, 2) - pow(a, 2))
    x0 = p1.x + a * (p2.x - p1.x) / d
    y0 = p1.y + a * (p2.y - p1.y) / d
    rx = -(p2.y - p1.y) * (h / d)
    ry = -(p2.x - p1.x) * (h / d)
    return [point(x0 + rx, y0 - ry), point(x0 - rx, y0 + ry)]


def get_all_intersecting_points(circles):
    points = []
    num = len(circles)
    for i in range(num):
        j = i + 1
        for k in range(j, num):
            res = get_two_circles_intersecting_points(circles[i], circles[k])
            if res:
                points.extend(res)
    return points


def is_contained_in_circles(point, circles):
    for i in range(len(circles)):
        if (get_two_points_distance(point, circles[i].center) >= (circles[i].radius)):
            return False
    return True


def get_polygon_center(points):
    center = point(0, 0)
    num = len(points)
    for i in range(num):
        center.x += points[i].x
        center.y += points[i].y
    center.x /= num
    center.y /= num
    return center


######################## SCRIPTS FROM UTM PACKAGE  ###############################################
# THIS IS COPY PASTED HERE SO THAT THE MAIN PACKAGE DOESN'T HAVE TO BE INSTALLED ON THE SERVER
# I CONTACTED TOM TO INSTALL THIS PACKAGE BUT HE HAD TROUBLE IN INSTALLING IT SO THIS IS THE EASY ALTERNATIVE
# SOURCE: https://pypi.org/project/utm/
K0 = 0.9996

E = 0.00669438
E2 = E * E
E3 = E2 * E
E_P2 = E / (1.0 - E)

SQRT_E = math.sqrt(1 - E)
_E = (1 - SQRT_E) / (1 + SQRT_E)
_E2 = _E * _E
_E3 = _E2 * _E
_E4 = _E3 * _E
_E5 = _E4 * _E

M1 = (1 - E / 4 - 3 * E2 / 64 - 5 * E3 / 256)
M2 = (3 * E / 8 + 3 * E2 / 32 + 45 * E3 / 1024)
M3 = (15 * E2 / 256 + 45 * E3 / 1024)
M4 = (35 * E3 / 3072)

P2 = (3. / 2 * _E - 27. / 32 * _E3 + 269. / 512 * _E5)
P3 = (21. / 16 * _E2 - 55. / 32 * _E4)
P4 = (151. / 96 * _E3 - 417. / 128 * _E5)
P5 = (1097. / 512 * _E4)

R = 6378137

ZONE_LETTERS = "CDEFGHJKLMNPQRSTUVWXX"


def to_latlon(easting, northing, zone_number, zone_letter=None, northern=None, strict=True):
    if not zone_letter and northern is None:
        raise ValueError('either zone_letter or northern needs to be set')

    elif zone_letter and northern is not None:
        raise ValueError('set either zone_letter or northern, but not both')

    if strict:
        if not 100000 <= easting < 1000000:
            raise IndexError('easting out of range (must be between 100.000 m and 999.999 m)')
        if not 0 <= northing <= 10000000:
            raise IndexError('northing out of range (must be between 0 m and 10.000.000 m)')
    if not 1 <= zone_number <= 60:
        raise IndexError('zone number out of range (must be between 1 and 60)')

    if zone_letter:
        zone_letter = zone_letter.upper()

        if not 'C' <= zone_letter <= 'X' or zone_letter in ['I', 'O']:
            raise IndexError('zone letter out of range (must be between C and X)')

        northern = (zone_letter >= 'N')

    x = easting - 500000
    y = northing

    if not northern:
        y -= 10000000

    m = y / K0
    mu = m / (R * M1)

    p_rad = (mu +
             P2 * math.sin(2 * mu) +
             P3 * math.sin(4 * mu) +
             P4 * math.sin(6 * mu) +
             P5 * math.sin(8 * mu))

    p_sin = math.sin(p_rad)
    p_sin2 = p_sin * p_sin

    p_cos = math.cos(p_rad)

    p_tan = p_sin / p_cos
    p_tan2 = p_tan * p_tan
    p_tan4 = p_tan2 * p_tan2

    ep_sin = 1 - E * p_sin2
    ep_sin_sqrt = math.sqrt(1 - E * p_sin2)

    n = R / ep_sin_sqrt
    r = (1 - E) / ep_sin

    c = _E * p_cos ** 2
    c2 = c * c

    d = x / (n * K0)
    d2 = d * d
    d3 = d2 * d
    d4 = d3 * d
    d5 = d4 * d
    d6 = d5 * d

    latitude = (p_rad - (p_tan / r) *
                (d2 / 2 -
                 d4 / 24 * (5 + 3 * p_tan2 + 10 * c - 4 * c2 - 9 * E_P2)) +
                d6 / 720 * (61 + 90 * p_tan2 + 298 * c + 45 * p_tan4 - 252 * E_P2 - 3 * c2))

    longitude = (d -
                 d3 / 6 * (1 + 2 * p_tan2 + c) +
                 d5 / 120 * (5 - 2 * c + 28 * p_tan2 - 3 * c2 + 8 * E_P2 + 24 * p_tan4)) / p_cos

    return (math.degrees(latitude),
            math.degrees(longitude) + zone_number_to_central_longitude(zone_number))


def from_latlon(latitude, longitude, force_zone_number=None):
    if not -80.0 <= latitude <= 84.0:
        raise IndexError('latitude out of range (must be between 80 deg S and 84 deg N)')
    if not -180.0 <= longitude <= 180.0:
        raise IndexError('longitude out of range (must be between 180 deg W and 180 deg E)')

    lat_rad = math.radians(latitude)
    lat_sin = math.sin(lat_rad)
    lat_cos = math.cos(lat_rad)

    lat_tan = lat_sin / lat_cos
    lat_tan2 = lat_tan * lat_tan
    lat_tan4 = lat_tan2 * lat_tan2

    if force_zone_number is None:
        zone_number = latlon_to_zone_number(latitude, longitude)
    else:
        zone_number = force_zone_number

    zone_letter = latitude_to_zone_letter(latitude)

    lon_rad = math.radians(longitude)
    central_lon = zone_number_to_central_longitude(zone_number)
    central_lon_rad = math.radians(central_lon)

    n = R / math.sqrt(1 - E * lat_sin ** 2)
    c = E_P2 * lat_cos ** 2

    a = lat_cos * (lon_rad - central_lon_rad)
    a2 = a * a
    a3 = a2 * a
    a4 = a3 * a
    a5 = a4 * a
    a6 = a5 * a

    m = R * (M1 * lat_rad -
             M2 * math.sin(2 * lat_rad) +
             M3 * math.sin(4 * lat_rad) -
             M4 * math.sin(6 * lat_rad))

    easting = K0 * n * (a +
                        a3 / 6 * (1 - lat_tan2 + c) +
                        a5 / 120 * (5 - 18 * lat_tan2 + lat_tan4 + 72 * c - 58 * E_P2)) + 500000

    northing = K0 * (m + n * lat_tan * (a2 / 2 +
                                        a4 / 24 * (5 - lat_tan2 + 9 * c + 4 * c ** 2) +
                                        a6 / 720 * (61 - 58 * lat_tan2 + lat_tan4 + 600 * c - 330 * E_P2)))

    if latitude < 0:
        northing += 10000000

    return easting, northing, zone_number, zone_letter


def latitude_to_zone_letter(latitude):
    if -80 <= latitude <= 84:
        return ZONE_LETTERS[int(latitude + 80) >> 3]
    else:
        return None


def latlon_to_zone_number(latitude, longitude):
    if 56 <= latitude < 64 and 3 <= longitude < 12:
        return 32

    if 72 <= latitude <= 84 and longitude >= 0:
        if longitude <= 9:
            return 31
        elif longitude <= 21:
            return 33
        elif longitude <= 33:
            return 35
        elif longitude <= 42:
            return 37

    return int((longitude + 180) / 6) + 1


def zone_number_to_central_longitude(zone_number):
    return (zone_number - 1) * 6 - 180 + 3


####################### EXISITING SOLUTION FOR OPTIMASATION ALGORITHM FOR INTERPOLATION ##########################
# Source: https://www.alanzucconi.com/2017/03/13/positioning-and-trilateration/#part3
# Heavily modified this to suit my needs

# Mean Square Error
# locations: [ (lat1, long1), ... ]
# distances: [ distance1, ... ]
def mse(x, locations, distances):
    mse = 0.0
    for location, distance in zip(locations, distances):
        distance_calculated = haversine(x, location)
        mse += math.pow(distance_calculated - distance, 2.0)
    return mse / len(list(zip(locations, distances)))

# initial_location: (lat, long)
# locations: [ (lat1, long1), ... ]
# distances: [ distance1,     ... ]
def getOptimisedResult(initial_location, inner_points):
    distances = list()
    locations = list()
    for point in inner_points:
        coordinate = (point.x, point.y)
        locations.append(coordinate)
        distances.append(haversine(initial_location, coordinate))
    #print(distances)
    #print(locations)
    result = minimize(
        mse,                         # The error function
        initial_location,            # The initial guess
        args=(locations, distances), # Additional parameters for mse
        method='L-BFGS-B',           # The optimisation algorithm
        options={
            'ftol':1e-5,         # Tolerance
            'maxiter': 1e+7      # Maximum iterations
        })
    return result.x

######################## WRITTEN BY STUNDET FINN ZHAN CHEN ########################################

class Beacon(object):
    def __init__(self, deviceMac, lat, lng, txPower):
        self.deviceMac = deviceMac
        self.lat = lat
        self.lng = lng
        # Tx is the strength of the transmission signal measured at a distance of one meter from the transmitter.
        # The following tx power has been calculated by collecting more than 30 rssi of the beacon
        # around 1 metres from the beacon, outliers have been removed and the mean is calculated
        # data collected are saved on an excel file and input to this algorithm
        # https://www.kdnuggets.com/2017/02/removing-outliers-standard-deviation-python.html
        self.umtPoint = self.createUTMPoint(lat, lng)
        # Do not know the radius at this point
        self.circle = circle(self.umtPoint, 0)
        self.txPower = txPower
        self.pastRssi = list()

    def convertLatLngToUTM(self, lat, lng):
        (x, y, _, _) = from_latlon(lat, lng)
        return x, y

    def createUTMPoint(self, lat, lng):
        x, y = self.convertLatLngToUTM(lat, lng)
        # print(x, y)
        return point(x, y)

    def getDistanceToBeacon(self):
        return self.getDistanceFromRSSI(rssi=self.getPastRssiAverage(), txPower=self.txPower)

    def getPastRssiAverage(self):
        if len(self.pastRssi) == 0:
            return 0
        else:
            ##################### EXISING SOLUTION FOR REMOVING OUTLIERS ###########################
            # Source from https://www.kdnuggets.com/2017/02/removing-outliers-standard-deviation-python.html
            elements = np.array(self.pastRssi)
            mean = np.mean(elements, axis=0)
            sd = np.std(elements, axis=0)
            # Removes outliers and return filtered mean past RSSIs
            final_list = [x for x in self.pastRssi if (x >= mean - 2 * sd)]
            final_list = [x for x in final_list if (x <= mean + 2 * sd)]
            return np.mean(final_list)

    ##################### EXISING SOLUTION FOR CALCULATING DISTANCE FROM RSSI ################
    # Source from https://stackoverflow.com/questions/22784516/estimating-beacon-proximity-distance-based-on-rssi-bluetooth-le

    def getDistanceFromRSSI(self, rssi, txPower):  # in metres
        # tx values usually ranges from -59 to -65
        if rssi == 0:
            return -1
        return math.pow(10, (txPower - rssi) / (10 * 2))
    #########################################################################################

    def debug(self):
        print(self.deviceMac + " " + str(self.pastRssi) + " " + str(self.getPastRssiAverage()))

    def resetPastRssi(self):
        self.pastRssi = list()


def getThreeBeaconsForTrilateration(discoveredBeacons):
    # Return 3 closest beacons as a list
    threeBeacons = dict()
    distances = dict()  # key is distance and value is Beacon object
    for deviceMac in discoveredBeacons:
        distances[beaconsMap[deviceMac].getDistanceToBeacon()] = beaconsMap[deviceMac]

    # Return the 3 closest beacons by sorting the key which is the distance
    # print("Three closest beacon")
    for distance in sorted(distances)[:3]:
        # distances[distance].debug()
        # print(distances[distance].deviceMac + " " + str(distance))
        threeBeacons[distances[distance].deviceMac] = distances[distance]

    return threeBeacons


def getSeconds(lastTimestamp):
    # Timestamp is of this string format "yyyy-MM-dd HH:mm:ss.SSS"
    # Returns the total seconds passed since the start of the day
    hourMinuteSecondMillisecondReference = lastTimestamp.split(" ")[1].split(":")
    totalSecondsReference = float(hourMinuteSecondMillisecondReference[2]) \
                            + float(hourMinuteSecondMillisecondReference[1]) * 60 \
                            + float(hourMinuteSecondMillisecondReference[0]) * 60 * 60
    return totalSecondsReference


def timeDifference(oldtime, newtime):
    return newtime - oldtime


def setUpCircleRadius(beacons):
    for deviceMac in beacons:
        beacons[deviceMac].circle.radius = beacons[deviceMac].getDistanceToBeacon()


def getTrilaterationResult(beacons):
    circle_list = list()
    for deviceMac in beacons.keys():
        circle_list.append(beacons[deviceMac].circle)

    inner_points = []
    for p in get_all_intersecting_points(circle_list):
        inner_points.append(p)
        # print("x: " + str(p.x) + " y:" + str(p.y))
        # Gives more 2x more weight if all of circles intersects
        if is_contained_in_circles(p, circle_list):
            inner_points.append(p)
            inner_points.append(p)

    if len(inner_points) > 0:
        center = get_polygon_center(inner_points)
        initialGuess = (center.x, center.y)
        result = getOptimisedResult(initialGuess, inner_points)
        #print("initial Guess: " +  str(initialGuess) + "  Optimised Result: " + str(result))
        (lat, lng) = to_latlon(result[0], result[1], 30, 'U')
        return lat, lng
    else:
        return "nan", "nan"


def computeResult(discoveredBeacons):
    global estimatedLocations
    setUpCircleRadius(discoveredBeacons)
    # filter all beacons that has distance to user bigger than 20 metres because in the prototype, it is impossible
    # in AT lvl 5 and the further the distance the more unreliable
    # skip the dictionary changed size error by using a list copy of the keys
    for deviceMac in list(discoveredBeacons.keys()):
        if discoveredBeacons[deviceMac].getDistanceToBeacon() > 10:
            del discoveredBeacons[deviceMac]
    # Treats last known position as a beacon to help in interpolating the new position
    estimatedPositionResponse = requests.get(estimatedPositionUrl, headers=myheaders)
    if (len(estimatedPositionResponse.json()) > 0):
        lastEstimatedPositionItem = estimatedPositionResponse.json()[len(estimatedPositionResponse.json()) - 1]
        pastTimestamp = lastEstimatedPositionItem["timestamp"]
        past_lat = lastEstimatedPositionItem["lat"]
        past_lon = lastEstimatedPositionItem["lon"]
        # Only uses last estimated location which were in the past 10 seconds
        # time difference is also used to estimated how far the user has gone from the past position
        # using the assumption that the user moves at 0.5 metres per second
        # This could be improved using gyroscope and accelerometer
        # This is used to make the last known position as a beacon with the distance travelled by user as a
        # clue for interpolation
        timeDif = timeDifference(getSeconds(pastTimestamp), timeReference)
        if timeDif <= 5 and timeDif >= 0:
            setUpCircleRadius(discoveredBeacons)
            discoveredBeacons["LastKnownPosition"] = Beacon("LastKnownPosition", float(past_lat), float(past_lon),
                                                                txPower=None)
            discoveredBeacons["LastKnownPosition"].circle.radius = 0.5 * timeDif
            estimated_lat, estimated_lon = getTrilaterationResult(discoveredBeacons)

            if (str(estimated_lat) != "nan" or str(estimated_lon) != "nan"):
                # Successful estimated the position
                # post estimated position to the Cloud
                requests.post(estimatedPositionUrl, data={"timestamp": lastTimestamp, "lat": repr(estimated_lat),
                                                              "lon": repr(estimated_lon)}, headers=myheaders)
                # print("successfuly interpolated last position with 2 beacons")
                string = lastTimestamp + "," + str(estimated_lat) + "," + str(estimated_lon)
                print(string)  # might need to calibrate the algorithm response
                estimatedLocations.append(string)
                print("Successfully estimated position using last known position")
                return
            else:
                # Cannot estimate because there is no overlapping areas between the base stations
                # print("Failed to interpolate")
                del discoveredBeacons["LastKnownPosition"]

    # Could not interpolate, so get center of the intersections of the 2 beacons
    estimated_lat, estimated_lon = getTrilaterationResult(discoveredBeacons)

    if (str(estimated_lat) != "nan" or str(estimated_lon) != "nan"):
        # Successful estimated the position, post estimated position to the Cloud
        requests.post(estimatedPositionUrl, data={"timestamp": lastTimestamp, "lat": repr(estimated_lat),
                                                      "lon": repr(estimated_lon)}, headers=myheaders)

        string = lastTimestamp + "," + str(estimated_lat) + "," + str(estimated_lon)
        print("Estimated position with known beacons")
        print(string)  # might need to calibrate the algorithm response
        estimatedLocations.append(string)
    else:
        # Cannot estimate because there is no overlapping areas between the base stations
        print("Failed to interpolate")

def printTraces(locations):
    print("\n\n\n\n\n\n\n\n")
    for item in locations:
        trace = item.split(",")
        print(trace[2] + "," + trace[1] + ",0")


def writeCVS(locations):
    count = 0
    with open('FinnZhanChenResults.csv', 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'latitude', 'longitude']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for i in range(len(locations) - 1):
            content = locations[i].split(",")
            #print(content)
            currentTimestamp = content[0]
            dateFormat = currentTimestamp.split(" ")[0].split("-")
            #print(dateFormat)
            start = date(int(dateFormat[0]), int(dateFormat[1]), int(dateFormat[2]))
            unixTime = int(mktime(start.timetuple()) * 1000 + getSeconds(currentTimestamp) * 1000)
            #print(unixTime)
            writer.writerow({'timestamp': unixTime, 'latitude': content[1], 'longitude': content[2]})

            # repeat the last estimated location every 3 seconds if there is not an estimated location in that interval
            nextTimestamp = locations[i + 1].split(",")[0]
            timeToNextTimestamp = timeDifference(getSeconds(currentTimestamp), getSeconds(nextTimestamp))
            while timeToNextTimestamp > 3:
                unixTime = unixTime + 3*1000
                writer.writerow({'timestamp': unixTime, 'latitude': content[1], 'longitude': content[2]})
                timeToNextTimestamp = timeToNextTimestamp - 3
                count = count + 1

    print("Number of times the interval between timestamps is bigger than 3 seconds: " + str(count))


# Experimenting variables such as timeWindow and RSSI calibration with collected data
class ExperimentPoints(object):
    def __init__(self, id, lat, lng, startTimestamp, endTimestamp):
        self.id = id
        self.lat = lat
        self.lng = lng
        self.startTime = self.getSeconds(startTimestamp)
        self.endTime = self.getSeconds(endTimestamp)
        self.estimatedLocations = list()

    def getSeconds(self, lastTimestamp):
        # Timestamp is of this string format "yyyy-MM-dd HH:mm:ss.SSS"
        # Returns the total seconds passed since the start of the day
        hourMinuteSecondMillisecondReference = lastTimestamp.split(" ")[1].split(":")
        totalSecondsReference = float(hourMinuteSecondMillisecondReference[2]) \
                                + float(hourMinuteSecondMillisecondReference[1]) * 60 \
                                + float(hourMinuteSecondMillisecondReference[0]) * 60 * 60
        return totalSecondsReference

    def isWithinTimestamp(self, timestamp):
        givenTime = getSeconds(timestamp)
        if givenTime >= self.startTime and givenTime <= self.endTime:
            return True
        else:
            return False

    def getMeanDistanceError(self):
        testPoint = (self.lat, self.lng)
        errorDistaceInMetres = 0
        for location in self.estimatedLocations:
            errorDistaceInMetres = errorDistaceInMetres + haversine(testPoint, location)
        try:
            return errorDistaceInMetres/len(self.estimatedLocations) * 1000 # in metres
        except:
            return -1

def path1_non_moving_experiment(estimatedLocations):
    experimentPoints = {
        0 : ExperimentPoints(0, 55.944478679160206,-3.1869960576295857, "2018-04-20 20:42:48.858", "2018-04-20 20:43:22.354"),
        1 : ExperimentPoints(1, 55.9444916341351,-3.186918273568153, "2018-04-20 20:44:41.462", "2018-04-20 20:45:52.854"),
        2 : ExperimentPoints(2, 55.944435683632705,-3.1869886815547948, "2018-04-20 20:46:49.137", "2018-04-20 20:47:20.291"),
        3 : ExperimentPoints(3, 55.944454834484915,-3.1868780404329295, "2018-04-20 20:48:22.563", "2018-04-20 20:48:53.792"),
        4 : ExperimentPoints(4, 55.9444709812745,-3.186771087348461, "2018-04-20 20:49:59.386",  "2018-04-20 20:50:32.264"),
        5 : ExperimentPoints(5, 55.94440113697342,-3.186951801180839,  "2018-04-20 20:51:29.559", "2018-04-20 20:52:50.815"),
        6 : ExperimentPoints(6, 55.94441427972785,-3.1868740171194077, "2018-04-20 20:53:47.910", "2018-04-20 20:54:17.534"),
        7 : ExperimentPoints(7, 55.94442836124552,-3.186793215572834, "2018-04-20 20:55:17.741", "2018-04-20 20:55:56.786"),
        8 : ExperimentPoints(8, 55.94450477685883,-3.1868331134319305,  "2018-04-20 20:57:51.264",  "2018-04-20 20:58:30.693"),
        9 : ExperimentPoints(9, 55.94451791957813,-3.186751641333103, "2018-04-20 21:00:28.571", "2018-04-20 21:01:00.317"),
        10 : ExperimentPoints(10, 55.94453106229293,-3.186670504510403,  "2018-04-20 21:02:05.731", "2018-04-20 21:02:42.224"),
        11 : ExperimentPoints(11, 55.94448074444634,-3.186710067093372, "2018-04-20 21:03:56.303", "2018-04-20 21:04:31.457"),
        12 : ExperimentPoints(12, 55.94449294840768,-3.1866389885544772, "2018-04-20 21:05:27.696","2018-04-20 21:05:59.176"),
        13 : ExperimentPoints(13, 55.94444075297686,-3.1867134198546414, "2018-04-20 21:07:28.819",  "2018-04-20 21:08:01.388"),
        14 : ExperimentPoints(14, 55.94445464673151,-3.186629600822926, "2018-04-20 21:08:51.265", "2018-04-20 21:09:22.805")
    }

    i = 0
    for location in estimatedLocations:
        content = location.split(",")
        timestamp = content[0]
        lat = float(content[1])
        lon = float(content[2])
        if experimentPoints[i].isWithinTimestamp(timestamp):
            experimentPoints[i].estimatedLocations.append((lat, lon))
        else:
            #next experiment point as time is after the end of the timestamp for that testpoint
            i += 1
    overallMeanDistanceError = 0
    for testPointID in experimentPoints:
        testPointDistanceError = experimentPoints[testPointID].getMeanDistanceError()
        overallMeanDistanceError += testPointDistanceError
        print("Test Point: " + str(testPointID)
              + "     Number of Estimated Locations: " + str(len(experimentPoints[testPointID].estimatedLocations))
              + "     Mean Distance Error: " + str(testPointDistanceError))

    print("Overall Mean Distance Error: " + str(overallMeanDistanceError/len(experimentPoints)))


if __name__ == "__main__":
    # Found the rssi at 1 metres but still requires calibration. Did it manually with the help of my
    # Android app visualising the distance reached by beacons and my real position.
    beaconsMap = {
        "ED23C0D875CD": Beacon("ED23C0D875CD", 55.9444578385393, -3.1866151839494705, -93 + 6 +3),
        "E7311A8EB6D7": Beacon("E7311A8EB6D7", 55.94444244275808, -3.18672649562358860, -94 + 7 +7),
        "C7BC919B2D17": Beacon("C7BC919B2D17", 55.94452336441765, -3.1866540759801865, -61 + 4.5),
        "EC75A5ED8851": Beacon("EC75A5ED8851", 55.94452261340533, -3.1867526471614838, -88 + 5),
        "FE12DEF2C943": Beacon("FE12DEF2C943", 55.94448393625199, -3.1868280842900276, -87 + 2.5),
        "C03B5CFA00B8": Beacon("C03B5CFA00B8", 55.94449050761571, -3.1866483762860294, -50),
        "E0B83A2F802A": Beacon("E0B83A2F802A", 55.94443774892113, -3.1867992505431175, -96 + 10),
        "F15576CB0CF8": Beacon("F15576CB0CF8", 55.944432116316044, -3.186904862523079, -94 +5),
        "F17FB178EA3D": Beacon("F17FB178EA3D", 55.94444938963575, -3.1869836524128914, -85),
        "FD8185988862": Beacon("FD8185988862", 55.94449107087541, -3.186941407620907, -90 +5)
    }

    estimatedLocations = list()  # Keeps track of the successfully estimated locations
    discoveredBeacons = dict()  # a map of discovered Beacon objects
    timeWindow = 4.5  # Only take into account the RSSI of the past x seconds
    timeWindowForAlgorithm = 3   # run algorithm for every x seconds interval
    ### NOTE THAT timeWindowForAlgorithm must be smaller than timeWindow

    # Authorisation header for GET and POST request
    myheaders = {"Authorization": "Bearer 57:3996aa851ea17f9dd462969c686314ed878c0cf7"}
    readingsUrl = 'http://glenlivet.inf.ed.ac.uk:8080/api/v1/svc/apps/data/docs/path1_non_moving'
    estimatedPositionUrl = 'http://glenlivet.inf.ed.ac.uk:8080/api/v1/svc/apps/data/docs/batchlocations'
    # reset container
    requests.delete(estimatedPositionUrl, headers=myheaders)
    readingsResponse = requests.get(readingsUrl, headers=myheaders)

    # ALL CONTENT OF THE PRINT STATEMENT HAVE BEEN FORMATTED IN THE FOLLOWING WAY
    # LINE 1 CONTAINS THE ESTIMATED POSITION OR ERROR MESSAGES
    # ALL OTHER LIENS CONTAINS THE BEACON'S DEVICE_MAC AND THE DISTANCE TO BEACON
    # NOTE WHEN THERE ARE NO ENOUGH BEACONS FOR TRILATERATION, THE LAST KNOWN POSITION WILL BE USED
    # TO INTERPOLATE THE NEW POSITION. IN THIS CASE THE LAST KNOWN POSITION IS TREATED AS A BEACON
    # AND ITS DISTANCE TO LAST KNOWN POSITION IS ALSO PRINTED AS A BEACON
    # THE PURPOSE OF THIS IS SO THAT IT CAN BE VISUALISED ON THE ANDROID APP
    if len(readingsResponse.json()) > 0:
        json = readingsResponse.json()
        # This is used as a reference timestamp to get all RSSI readings in the past x seconds
        lastTimestamp = json[0]["timestamp"]  # Get first timestamp
        timeReference = getSeconds(lastTimestamp)

        # Start iteration from the oldest item (oldest beacon info)
        # Read all readings from the past timeWindow seconds and compute estimated location

        i = 0
        j = 0  # saves which index is when the timeWindowForAlgorithm seconds reached
        timeWindowForAlgorithmReached = False

        while (i < len(json)):
            item = json[i]
            timestamp = item["timestamp"]
            deviceMac = item["device_mac"]
            rssi = int(item["rssi"])
            # only considers values in the past 3 seconds
            timeDif = timeDifference(timeReference, getSeconds(timestamp))
            if timeDif > timeWindowForAlgorithm and not timeWindowForAlgorithmReached:
                j = i
                timeWindowForAlgorithmReached = True
                # Update time reference for the next iteration
                tempTimeReference = getSeconds(timestamp)
                tempLastTimestamp = timestamp

            if timeDif <= timeWindow:
                #print("i: " + str(i) + " j:" + str(j) + " threeSecondReached: " + str(timeWindowForAlgorithmReached) + " timeDif: " + str(timeDif) + " | " + timestamp + " | " + deviceMac + " | " + str(rssi))
                if not deviceMac in discoveredBeacons:
                    # convert metres to kilometres for the trilateration algorithm later
                    discoveredBeacons[deviceMac] = beaconsMap[deviceMac]
                # record seen rssi value in the past timeWindow seconds to beacons
                beaconsMap[deviceMac].pastRssi.append(rssi)
                i += 1
            else:
                i = j
                try:
                    computeResult(discoveredBeacons)
                    # Reset for next computation
                    for deviceMac in beaconsMap:
                        beaconsMap[deviceMac].resetPastRssi()
                    discoveredBeacons = dict()
                    # Get ready for the next iteration

                    timeWindowForAlgorithmReached = False
                    timeReference = tempTimeReference
                    lastTimestamp = tempLastTimestamp
                except:
                    pass

    # printTraces(estimatedLocations)
    print("Time Window: " + str(timeWindow))
    print("Time Window for Algorithm: " + str(timeWindowForAlgorithm))
    print("Number of estimated location: " + str(len(estimatedLocations)))
    writeCVS(estimatedLocations)
    path1_non_moving_experiment(estimatedLocations)