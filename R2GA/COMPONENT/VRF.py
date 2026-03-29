
class VRF(object):

    def __init__(self, voltage=None, frequency=None):
        self.voltage = voltage
        self.frequency = frequency

    def getVoltage(self):
        return self.voltage

    def setVoltage(self, voltage):
        self.voltage = voltage

    def getFrequency(self):
        return self.frequency

    def setFrequency(self, frequency):
        self.frequency = frequency