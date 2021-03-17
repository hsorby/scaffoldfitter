"""
Fit step for configuring subsequent behaviour, e.g. data projection settings.
"""

from scaffoldfitter.fitterstep import FitterStep


class FitterStepConfig(FitterStep):

    _jsonTypeId = "_FitterStepConfig"

    def __init__(self):
        super(FitterStepConfig, self).__init__()
        # Example json serialisation within config step. Include only groups and options in-use
        # Note that these are model group names; data group names differing by
        # case or whitespace are set by Fitter to matching model names.
        #"groupSettings": {
        #    "GROUPNAME1" : {
        #        "dataProportion" : 0.1
        #        }
        #    "GROUPNAME2" : {
        #        "dataProportion" : null
        #        }
        #    }
        # unlisted groups or groups without dataProportion inherit from earlier config step
        # or back to initial global setting (1.0 in this case = include all points).
        # null value cancels inherited dataProportion = go back to global setting.
        self._groupSettings = {}
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
        self._groupSettings = dct["groupSettings"]
        self._projectionCentreGroups = dct["projectionCentreGroups"]

    def encodeSettingsJSONDict(self) -> dict:
        """
        Encode definition of step in dict.
        :return: Settings in a dict ready for passing to json.dump.
        """
        return {
            self._jsonTypeId : True,
            "groupSettings" : self._groupSettings,
            "projectionCentreGroups" : self._projectionCentreGroups
            }

    def getGroupSettingsNames(self):
        """
        :return:  List of names of groups settings are held for.
        """
        return list(self._groupSettings.keys())

    def clearGroupSettings(self, groupName):
        """
        Clear all local settings for group so fall back to last config
        settings or global defaults.
        :param groupName:  Exact model group name.
        """
        groupSettings = self._groupSettings.pop(groupName, None)

    def clearGroupDataProportion(self, groupName):
        """
        Clear local group data proportion so fall back to last config or global default.
        :param groupName:  Exact model group name.
        """
        groupSettings = self._groupSettings.get(groupName)
        if groupSettings:
            groupSettings.pop("dataProportion", None)
            if len(groupSettings) == 0:
                self._groupSettings.pop(groupName)

    def getGroupDataProportion(self, groupName):
        """
        Get proportion of group data points to include in fit, or None to
        use global default.
        :param groupName:  Exact model group name.
        :return:  Proportion, isLocallySet. Proportion is either a value from
        0.0 to 1.0, where 0.1 = 10%, or None if using global value (1.0).
        The second return value is True if the value is set locally.
        """
        groupSettings = self._groupSettings.get(groupName)
        if groupSettings:
            proportion = groupSettings.get("dataProportion", "INHERIT")
            if proportion != "INHERIT":
                return proportion, True
        inheritConfigStep = self.getFitter().getInheritFitterStepConfig(self)
        proportion = inheritConfigStep.getGroupDataProportion(groupName)[0] if inheritConfigStep else None
        return proportion, False

    def setGroupDataProportion(self, groupName, proportion):
        """
        Set proportion of group data points to include in fit, or force
        return to global default.
        :param groupName:  Exact model group name.
        :param proportion:  Float valued proportion from 0.0 (0%) to 1.0 (100%),
        or None to force used of global default. Asserts value is valid.
        """
        assert (proportion is None) or (isinstance(proportion, float) and (0.0 <= proportion <= 1.0)), "FitterStepConfig: Invalid group data proportion"
        groupSettings = self._groupSettings.get(groupName)
        if not groupSettings:
            groupSettings = self._groupSettings[groupName] = {}
        groupSettings["dataProportion"] = proportion

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
