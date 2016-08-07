
class Controller(object):
    """
    Controller object represents a single raspberry PI controller with attached stations.
    """

    def __init__(self, enabled, rain_delay, manual_mode, logger, stations=[]):
        self.enabled = enabled
        self.stations = stations
        self.rain_delay = rain_delay
        self.manual_mode = manual_mode
        self.reboot = 0
        self.station_count = 0
        self.logging_enabled = False
        self.logger = logger
        self.busy = False
        self.rain_detected = False
        self.sequential = True
        self.rain_delay = None


    def ResetAllStations(self):
        """
        Reset all stations on this controller
        """
        for station in self.stations:
            station.Reset()


    def ResetStationByID(self, station_id):
        """
        Reset a station by ID
        """
        pass


    def Reboot(self):
        """
        Reboot the controller
        """
        pass


    def IsEnabled(self):
        """
        Return the enabled state of the controller (Boolean).
        """
        return self.enabled


    def Enable(self):
        """
        Enable the controller
        """
        self.enabled = True


    def Disable(self):
        """
        Disable the controller
        """
        self.enable = False


    def UpdateStations(self):
        """
        Update stations controlled by this controller
        """
        for station in self.stations:
            station.Update()


    def StationCount(self):
        """
        Get the number of stations governed by this controller
        """
        return len(self.stations)


    def SetBusy(self):
        """
        Set the controller as busy
        """
        self.busy = True


    def ClearBusy(self):
        """
        Set the controller as not busy
        """
        self.busy = False


    def IsBusy(self):
        """
        Return the busy condition of the controller
        """
        return self.busy


    def RainDetected(self):
        """
        Return the state of rain detection for the station
        """
        return self.rain_detected


    def SetRainDetected(self):
        """
        Set the station to know rain was detected
        """
        self.rain_detected = True
        for station in self.stations:
            station.SetRainDetected()


    def ClearRainDetected(self):
        """
        Unset the flag for rain detected
        """
        self.rain_detected = False
        for station in self.stations:
            station.ClearRainDetected()


    def SetSequentialMode(self):
        """
        Set the current mode to be sequential
        """
        self.sequential = True


    def SetConcurrentMode(self):
        """
        Set the current mode to be concurrent
        """
        self.sequential = False


    def IsSequentialMode(self):
        """
        Return if the current mode is sequential
        """
        return self.sequential


    def IsConcurrentMode(self):
        """
        Return if current mode is concurrent
        """
        return not self.sequential


    def CheckRain():
        """
        Check the rain sensor, set rain_detected and return if rain was detected
        """
        # Helpers.py check_rain()
        pass


    def SetRainDelayHours(self, delay):
        """
        Set the rain delay in hours
        """
        pass


    def ClearRainDelay(self):
        """
        Clear rain delay
        """
        self.rain_delay = 0


    def RainDelayEnabled(self):
        """
        Return if rain delay is enabled for this controller
        """
        return self.rain_delay > 0

