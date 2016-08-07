
class Station():
    """
    Station represents the interface for a station
    """
    def __init__(self):
        self.master = False
        self.on = False
        self.ignore_rain = False
        self.rain_detected = False


    def Reset(self):
        pass


    def Update(self):
        """
        Apply station update logic
        """
        pass


    def SetAsMaster(self):
        """
        Set the station as master station
        """
        self.master = True


    def SetAsStandard(self):
        """
        Remove master designation from station
        """
        self.master = False


    def IsMaster(self):
        """
        Is the current station designated as master
        """
        return self.master


    def TurnOn(self):
        """
        Turn the station on
        """
        self.on = True


    def TurnOff(self):
        """
        Turn the station off
        """
        self.on = False


    def IsOn(self):
        """
        Is the station on?
        """
        return self.on


    def EnableIgnoreRain(self):
        """
        Set the station to ignore rain
        """
        self.ignore_rain = True


    def DisableIgnoreRain(self):
        """
        Set the station to account for rain
        """
        self.ignore_rain = False


    def IgnoringRain(self):
        """
        Return if the station is ignoring rain
        """
        return self.ignore_rain


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


    def ClearRainDetected(self):
        """
        Unset the flag for rain detected
        """
        self.rain_detected = False
