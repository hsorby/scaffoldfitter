"""
Fit step for configuring subsequent behaviour, e.g. data projection settings.
"""

from scaffoldfitter.fitterstep import FitterStep


class FitterStepConfig(FitterStep):

    _jsonTypeId = "_FitterStepConfig"

    def __init__(self):
        super(FitterStepConfig, self).__init__()
        # Example json serialisation within config step. Include only groups and options in-use
        # Note that these are model group names -- data group names differing by
        # case or whitespace are set by Fitter to matching model names.
        #"groupSettings": {
        #    "GROUPNAME1" : {
        #        "dataProportion" : 0.1
        #        }
        #    "GROUPNAME2" : {
        #        "dataProportion" : null,
        #        "dataWeight" : 5.0
        #        }
        #    }
        # The first group GROUPNAME1 uses only 0.1 = 10% of the data points.
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

    def _clearGroupSetting(self, groupName : str, settingName : str):
        """
        Clear setting for group, removing group settings dict if empty.
        :param groupName:  Exact model group name.
        :param settingName: Exact name of real setting.
        """
        groupSettings = self._groupSettings.get(groupName)
        if groupSettings:
            groupSettings.pop(settingName, None)
            if len(groupSettings) == 0:
                self._groupSettings.pop(groupName)

    def _getGroupSetting(self, groupName : str, settingName : str, defaultValue):
        """
        Get group setting of supplied name, with reset & inherit ability.
        :param groupName:  Exact model group name.
        :param settingName: Exact name of real setting.
        :param defaultValue: Value to use if setting not found for group.
        :return:  value, setLocally, inheritable.
        Value falls back to defaultValue if not set.
        The second return value is True if the value is set locally to a value
        or None if reset locally.
        The third return value is True if a previous config has set the value.
        """
        value = None
        setLocally = False
        inheritable = False
        groupSettings = self._groupSettings.get(groupName)
        if groupSettings:
            if settingName in groupSettings:
                value = groupSettings[settingName]
                setLocally = None if (value is None) else True
        inheritConfigStep = self.getFitter().getInheritFitterStepConfig(self)
        if inheritConfigStep:
            inheritedValue = inheritConfigStep._getGroupSetting(groupName, settingName, None)[0]
            if inheritedValue is not None:
                if not (setLocally or (setLocally is None)):
                    value = inheritedValue
                inheritable = True
        if value is None:
            value = defaultValue
        return value, setLocally, inheritable

    def _setGroupSetting(self, groupName : str, settingName : str, value):
        """
        Set value of setting or None to reset to global default.
        :param groupName:  Exact model group name.
        :param settingName: Exact name of real setting.
        :param value: Value to assign, or None to reset. If the value is not
        inherited, None will clear the setting. Caller must check valid value.
        """
        groupSettings = self._groupSettings.get(groupName)
        if not groupSettings:
            groupSettings = self._groupSettings[groupName] = {}
        groupSettings[settingName] = value
        if value is None:
            inheritConfigStep = self.getFitter().getInheritFitterStepConfig(self)
            if (not inheritConfigStep) or \
                (inheritConfigStep._getGroupSetting(groupName, settingName, None)[0] is None):
                self._clearGroupSetting(groupName, settingName)

    def clearGroupDataProportion(self, groupName):
        """
        Clear local group data proportion so fall back to last config or global default.
        :param groupName:  Exact model group name.
        """
        self._clearGroupSetting(groupName, "dataProportion")

    def getGroupDataProportion(self, groupName):
        """
        Get proportion of group data points to include in fit, from 0.0 (0%) to
        1.0 (100%), plus flags indicating where it has been set.
        :param groupName:  Exact model group name.
        :return:  Proportion, setLocally, inheritable.
        Proportion of points used for group from 0.0 to 1.0.
        The second return value is True if the value is set locally to a value
        or None if reset locally.
        The third return value is True if a previous config has set the value.
        """
        return self._getGroupSetting(groupName, "dataProportion", 1.0)

    def setGroupDataProportion(self, groupName, proportion):
        """
        Set proportion of group data points to include in fit, or reset to
        global default.
        :param groupName:  Exact model group name.
        :param proportion:  Float valued proportion from 0.0 (0%) to 1.0 (100%),
        or None to reset to global default. Function ensures value is valid.
        """
        if proportion is not None:
            if not isinstance(proportion, float):
                proportion = self.getGroupDataProportion(groupName)[0]
            elif proportion < 0.0:
                proportion = 0.0
            elif proportion > 1.0:
                proportion = 1.0
        self._setGroupSetting(groupName, "dataProportion", proportion)

    def clearGroupDataWeight(self, groupName):
        """
        Clear local group data weight so fall back to last config or global default.
        :param groupName:  Exact model group name.
        """
        self._clearGroupSetting(groupName, "dataWeight")

    def getGroupDataWeight(self, groupName, defaultDataWeight=1.0):
        """
        Get weighting of group data points to apply in fit >= 0.0, plus flags
        indicating where it has been set.
        :param groupName:  Exact model group name.
        :param defaultDataWeight:  Value to use if not set for the group.
        :return:  Weight, setLocally, inheritable.
        Weight is a real value >= 0.0.
        The second return value is True if the value is set locally to a value
        or None if reset locally.
        The third return value is True if a previous config has set the value.
        """
        return self._getGroupSetting(groupName, "dataWeight", defaultDataWeight)

    def setGroupDataWeight(self, groupName, weight):
        """
        Set weighting of group data points to apply in fit, or reset to
        global default.
        :param groupName:  Exact model group name.
        :param weight:  Float valued weight >= 0.0, or None to reset to global
        default. Function ensures value is valid.
        """
        if weight is not None:
            if not isinstance(weight, float):
                weight = self.getGroupDataWeight(groupName)[0]
            elif weight < 0.0:
                weight = 0.0
        self._setGroupSetting(groupName, "dataWeight", weight)

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
