

from COMPONENT import *
from COMPONENT.VRF import VRF

class ComputingSystem(object):
    instance = None
    printOriginalSchedulingList = False
    printOptimizedSchedulingList = False
    init_flag = False

    processors = []

    applications = []

    VRFs = []
    processors1 = []

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, processors=None, applications=None):
        if ComputingSystem.init_flag:
            return
        self.processors = processors
        self.applications = applications
        ComputingSystem.init_flag = True

    @classmethod
    def init(cls, processor_number):
        ComputingSystem.init_processors(processor_number)

    @classmethod
    def init_processors(cls, processor_number):
        for i in range(processor_number):
            ecu = processor.Processor((i + 1), "P%d" % (i + 1))
            cls.processors.append(ecu)

    @classmethod
    def clear_processors(cls):
        for p in cls.processors:
            p.resident_tasks.clear()

    @classmethod
    def clear_applications(cls):
        cls.applications.clear()

    @classmethod
    def reset_processors(cls):
        cls.clear_processors()

    @classmethod
    def reset_tasks(cls, app):
        for t in app.tasks:
            t.is_executed = False
            t.is_assigned = False
            t.assignment = None

    @classmethod
    def reset(cls, app):
        cls.reset_processors()
        cls.reset_tasks(app)

    @classmethod
    def initiateVRFs(cls, vrfs):
        for i in range(len(vrfs)):
            Vrf = []
            vrf = vrfs[i]
            for j in range(len(vrf)):
                v = VRF(vrf[j][0], vrf[j][1])
                Vrf.append(v)
            cls.VRFs.append(Vrf)

    @classmethod
    def initiateProcessors(cls, vrfs, processorNumber):
        for i in range(processorNumber):
            p = processor.Processor((i), "p%d" % (i))
            p.setVrfs(cls.VRFs[i % len(cls.VRFs)])
            cls.processors1.append(p)

    @classmethod
    def initiate(cls, vrfs, processorNumber):
        cls.initiateVRFs(vrfs)
        cls.initiateProcessors(vrfs, processorNumber)