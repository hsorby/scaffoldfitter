"""
Fit step for configuring subsequent behaviour, e.g. data projection settings.
"""

from scaffoldfitter.fitterstep import FitterStep


class FitterStepConfig(FitterStep):

    _jsonTypeId = "_FitterStepConfig"

    def __init__(self):
        super(FitterStepConfig, self).__init__()
        self._projectionCentreGroups = False

    @classmethod
    def getJsonTypeId(cls):
        return cls._jsonTypeId

    def decodeSettingsJSONDict(self, dctIn : dict):
        """
        Decode definition of step from JSON dict.
        """
        assert self._jsonTypeId in dctIn
        # ensure all new options are in dct
        dct = self.encodeSettingsJSONDict()
        dct.update(dctIn)
        self._projectionCentreGroups = dct["projectionCentreGroups"]

    def encodeSettingsJSONDict(self) -> dict:
        """
        Encode definition of step in dict.
        :return: Settings in a dict ready for passing to json.dump.
        """
        return {
            self._jsonTypeId : True,
            "projectionCentreGroups" : self._projectionCentreGroups
            }

    def isProjectionCentreGroups(self):
        return self._projectionCentreGroups

    def setProjectionCentreGroups(self, projectionCentreGroups):
        """
        :param projectionCentreGroups: True to compute projections of group data
        translated so centre of data is at centre of target model geometry.
        Helps fit features with good initial orientation, but in the wrong place.
        :return: True if state changed, otherwise False.
        """
        if projectionCentreGroups != self._projectionCentreGroups:
            self._projectionCentreGroups = projectionCentreGroups
            return True
        return False

    def run(self, modelFileNameStem=None):
        """
        Calculate data projections with current settings.
        :param modelFileNameStem: Optional name stem of intermediate output file to write.
        """
        self._fitter.calculateDataProjections(self)
        if modelFileNameStem:
            self._fitter.writeModel(modelFileNameStem + "_config.exf")
        self.setHasRun(True)
