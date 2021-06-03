"""
Fit step for gross alignment and scale.
"""

from opencmiss.utils.zinc.field import assignFieldParameters, createFieldsDisplacementGradients
from opencmiss.utils.zinc.general import ChangeManager
from opencmiss.zinc.field import Field, FieldFindMeshLocation
from opencmiss.zinc.optimisation import Optimisation
from opencmiss.zinc.result import RESULT_OK
from scaffoldfitter.fitterstep import FitterStep
import sys

class FitterStepFit(FitterStep):

    _jsonTypeId = "_FitterStepFit"
    _dataWeightToken = "dataWeight"
    _strainPenaltyToken = "strainPenalty"
    _curvaturePenaltyToken = "curvaturePenalty"

    def __init__(self):
        super(FitterStepFit, self).__init__()
        self._numberOfIterations = 1
        self._maximumSubIterations = 1
        self._updateReferenceState = False

    @classmethod
    def getJsonTypeId(cls):
        return cls._jsonTypeId

    def decodeSettingsJSONDict(self, dctIn : dict):
        """
        Decode definition of step from JSON dict.
        """
        super().decodeSettingsJSONDict(dctIn)  # to decode group settings
        # ensure all new options are in dct
        dct = self.encodeSettingsJSONDict()
        dct.update(dctIn)
        print("decodeSettingsJSONDict fitter", self._fitter)
        self._numberOfIterations = dct["numberOfIterations"]
        self._maximumSubIterations = dct["maximumSubIterations"]
        self._updateReferenceState = dct["updateReferenceState"]
        # migrate legacy settings
        lineWeight = dct.get("lineWeight")
        if lineWeight is not None:
            self.setLineWeight(lineWeight)
        markerWeight = dct.get("markerWeight")
        if markerWeight is not None:
            self.setMarkerWeight(markerWeight)
        # convert legacy single-valued strain and curvature penalty weights to list:
        strainPenaltyWeight = dct.get("strainPenaltyWeight")
        if strainPenaltyWeight is not None:
            self.setGroupStrainPenalty(None, strainPenaltyWeight)
        curvaturePenaltyWeight = dct.get("curvaturePenaltyWeight")
        if curvaturePenaltyWeight is not None:
            self.setGroupCurvaturePenalty(None, curvaturePenaltyWeight)

    def encodeSettingsJSONDict(self) -> dict:
        """
        Encode definition of step in dict.
        :return: Settings in a dict ready for passing to json.dump.
        """
        dct = super().encodeSettingsJSONDict()
        dct.update({
            "numberOfIterations" : self._numberOfIterations,
            "maximumSubIterations" : self._maximumSubIterations,
            "updateReferenceState" : self._updateReferenceState
            })
        return dct

    def clearGroupDataWeight(self, groupName: str):
        """
        Clear group data weight so fall back to last fit or global default.
        :param groupName:  Exact model group name, or None for default group.
        """
        self.clearGroupSetting(groupName, self._dataWeightToken)

    def getGroupDataWeight(self, groupName: str):
        """
        Get group data weight to apply in fit, and associated flags.
        If not set or inherited, gets value from default group.
        :param groupName:  Exact model group name, or None for default group.
        :return: Weight, setLocally, inheritable.
        Weight is a real value >= 0.0. Default value 1.0 if not set.
        The second return value is True if the value is set locally to a value
        or None if reset locally.
        The third return value is True if a previous config has set the value.
        """
        return self.getGroupSetting(groupName, self._dataWeightToken, 1.0)

    def setGroupDataWeight(self, groupName: str, weight):
        """
        Set group data weight to apply in fit, or reset to use default.
        :param groupName:  Exact model group name, or default group name.
        :param weight:  Float valued weight >= 0.0, or None to reset to global
        default. Function ensures value is valid.
        """
        if weight is not None:
            if not isinstance(weight, float):
                weight = self.getGroupDataWeight(groupName)[0]
            elif weight < 0.0:
                weight = 0.0
        self.setGroupSetting(groupName, self._dataWeightToken, weight)

    def getLineWeight(self):
        """
        :deprecated: Use getGroupDataWeight().
        """
        print("Fit getLineWeight is deprecated", file=sys.stderr)
        groupNames = self._fitter.getDataProjectionGroupNames()
        fieldmodule = self._fitter.getFieldmodule()
        for groupName in groupNames:
            group = fieldmodule.findFieldByName(groupName).castGroup()
            meshGroup = self.getGroupDataProjectionMeshGroup(group)
            dimension = meshGroup.getDimension()
            if dimension == 1:
                return self.getGroupDataWeight(groupName, lineWeight)[0]
        return 0.0

    def setLineWeight(self, lineWeight):
        """
        :deprecated: Use setGroupDataWeight().
        """
        print("Fit setLineWeight is deprecated", file=sys.stderr)
        groupNames = self._fitter.getDataProjectionGroupNames()
        fieldmodule = self._fitter.getFieldmodule()
        for groupName in groupNames:
            group = fieldmodule.findFieldByName(groupName).castGroup()
            meshGroup = self.getGroupDataProjectionMeshGroup(group)
            dimension = meshGroup.getDimension()
            if dimension == 1:
                self.setGroupDataWeight(groupName, lineWeight)

    def getMarkerWeight(self):
        """
        :deprecated: Use getGroupDataWeight().
        """
        print("Fit getMarkerWeight is deprecated", file=sys.stderr)
        markerGroupName = self._fitter.getMarkerGroup().getName()
        if markerGroupName:
            return self.getGroupDataWeight(markerGroupName, markerWeight)[0]
        return 0.0

    def setMarkerWeight(self, markerWeight):
        """
        :deprecated: Use setGroupDataWeight().
        """
        print("Fit setMarkerWeight is deprecated", file=sys.stderr)
        markerGroupName = self._fitter.getMarkerGroup().getName()
        if markerGroupName:
            self.setGroupDataWeight(markerGroupName, markerWeight)

    def clearGroupStrainPenalty(self, groupName: str):
        """
        Clear local group strain penalty so fall back to last fit or global default.
        :param groupName:  Exact model group name, or None for default group.
        """
        self.clearGroupSetting(groupName, self._strainPenaltyToken)

    def getGroupStrainPenalty(self, groupName: str, count=None):
        """
        Get list of strain penalty factors used to scale first deformation
        gradient components in group. Up to 9 components possible in 3-D.
        :param groupName:  Exact model group name, or default group name.
        :param count: Optional number of factors to limit or enlarge list to.
        If enlarging, values are padded with the last stored value. If None,
        the number stored is requested.
        If not set or inherited, gets value from default group.
        :return: list(float), setLocally, inheritable.
        First return value is a list of float strain penalty factors, length > 0.
        If length is 1 and value is 0.0, no penalty will be applied.
        The second return value is True if the value is set locally to a value
        or None if reset locally.
        The third return value is True if a previous config has set the value.
        """
        strainPenalty, setLocally, inheritable = self.getGroupSetting(groupName, self._strainPenaltyToken, [0.0])
        if count:
            count = min(count, 9)
            storedCount = len(strainPenalty)
            if count <= storedCount:
                strainPenalty = strainPenalty[:count]
            else:
                lastFactor = strainPenalty[-1]
                strainPenalty = strainPenalty + [lastFactor]*(count - storedCount)
        else:
            strainPenalty = strainPenalty[:]  # shallow copy
        return strainPenalty, setLocally, inheritable

    def setGroupStrainPenalty(self, groupName: str, strainPenalty):
        """
        :param groupName:  Exact model group name, or default group name.
        :param factors: List of 1-9 float-value strain penalty factors to scale
        first deformation gradient components, or None to reset to inherited or
        default value. If fewer than 9 values are supplied in the list, the
        last value is used for all remaining components.
        """
        if strainPenalty is not None:
            assert isinstance(strainPenalty, list), "FitterStepFit: setGroupStrainPenalty requires a list of float"
            strainPenalty = strainPenalty[:9]  # shallow copy, limiting size
            count = len(strainPenalty)
            assert len > 0, "FitterStepFit: setGroupStrainPenalty requires a list of at least 1 float"
            for i in range(count):
                assert isinstance(strainPenalty[i], float), "FitterStepFit: setGroupStrainPenalty requires a list of float"
                if strainPenalty[i] < 0.0:
                    strainPenalty[i] = 0.0
        self.setGroupSetting(groupName, self._strainPenaltyToken, strainPenalty)

    def getStrainPenaltyWeight(self) -> float:
        """
        :deprecated: use getGroupStrainPenalty[default group name]
        :return: Single strain penalty weight.
        """
        print("Fit getStrainPenaltyWeight is deprecated", file=sys.stderr)
        strainPenalty = self.getGroupStrainPenalty(None)[0]
        if len(strainPenalty) > 1:
            print("Warning: Calling deprecated getStrainPenaltyWeight while multiple factors", file=sys.stderr)
        return strainPenalty[0]

    def setStrainPenaltyWeight(self, weight : float):
        """
        :deprecated: use setGroupStrainPenalty.
        :param weight: penalty factor to apply to all first deformation gradient components.
        """
        print("Fit setStrainPenaltyWeight is deprecated", file=sys.stderr)
        self.setGroupStrainPenalty(None, [weight])

    def clearGroupCurvaturePenalty(self, groupName: str):
        """
        Clear local group curvature penalty so fall back to last fit or global default.
        :param groupName:  Exact model group name, or None for default group.
        """
        self.clearGroupSetting(groupName, self._curvaturePenaltyToken)

    def getGroupCurvaturePenalty(self, groupName: str, count=None):
        """
        Get list of curvature penalty factors used to scale second deformation
        gradient components in group. Up to 27 components possible in 3-D.
        :param groupName:  Exact model group name, or default group name.
        :param count: Optional number of factors to limit or enlarge list to.
        If enlarging, values are padded with the last stored value. If None,
        the number stored is requested.
        If not set or inherited, gets value from default group.
        :return: list(float), setLocally, inheritable.
        First return value is a list of float curvature penalty factors.
        If length is 1 and value is 0.0, no penalty will be applied.
        The second return value is True if the value is set locally to a value
        or None if reset locally.
        The third return value is True if a previous config has set the value.
        """
        curvaturePenalty, setLocally, inheritable = self.getGroupSetting(groupName, self._curvaturePenaltyToken, [0.0])
        if count:
            storedCount = len(curvaturePenalty)
            if count <= storedCount:
                curvaturePenalty = curvaturePenalty[:count]
            else:
                lastFactor = curvaturePenalty[-1]
                curvaturePenalty = curvaturePenalty + [lastFactor]*(count - storedCount)
        else:
            curvaturePenalty = curvaturePenalty[:]  # shallow copy
        return curvaturePenalty, setLocally, inheritable

    def setGroupCurvaturePenalty(self, groupName: str, curvaturePenalty):
        """
        :param groupName:  Exact model group name, or default group name.
        :param curvaturePenalty: List of 1-27 float-value curvature penalty
        factors to scale first deformation gradient components, or None to
        reset to inherited or default value. If fewer than 27 values are
        supplied in the list, the last value is used for all remaining
        components.
        """
        if curvaturePenalty is not None:
            assert isinstance(curvaturePenalty, list), "FitterStepFit: setGroupCurvaturePenalty requires a list of float"
            curvaturePenalty = curvaturePenalty[:27]  # shallow copy, limiting size
            count = len(curvaturePenalty)
            assert count > 0, "FitterStepFit: setGroupCurvaturePenalty requires a list of at least 1 float"
            for i in range(count):
                assert isinstance(curvaturePenalty[i], float), "FitterStepFit: setGroupCurvaturePenalty requires a list of float"
                if curvaturePenalty[i] < 0.0:
                    curvaturePenalty[i] = 0.0
        self.setGroupSetting(groupName, self._curvaturePenaltyToken, curvaturePenalty)

    def getCurvaturePenaltyWeight(self) -> float:
        """
        :deprecated: use getGroupCurvaturePenalty[default group name]
        :return: Single curvature penalty weight.
        """
        print("Fit getCurvaturePenaltyWeight is deprecated", file=sys.stderr)
        curvaturePenalty = self.getGroupCurvaturePenalty(None)[0]
        if len(curvaturePenalty) > 1:
            print("Warning: Calling deprecated getCurvaturePenaltyWeight while multiple factors", file=sys.stderr)
        return curvaturePenalty[0]

    def setCurvaturePenaltyWeight(self, weight : float):
        """
        :deprecated: use setCurvaturePenaltyFactors.
        :param weight: penalty factor to apply to all first deformation gradient components.
        """
        print("Fit setCurvaturePenaltyWeight is deprecated", file=sys.stderr)
        self.setGroupCurvaturePenalty(None, [weight])

    def getEdgeDiscontinuityPenaltyWeight(self):
        print("Fit getEdgeDiscontinuityPenaltyWeight: feature removed", file=sys.stderr)
        return 0.0

    def setEdgeDiscontinuityPenaltyWeight(self, weight):
        print("Fit setEdgeDiscontinuityPenaltyWeight: feature removed", file=sys.stderr)

    def getNumberOfIterations(self):
        return self._numberOfIterations

    def setNumberOfIterations(self, numberOfIterations):
        assert numberOfIterations > 0
        if numberOfIterations != self._numberOfIterations:
            self._numberOfIterations = numberOfIterations
            return True
        return False

    def getMaximumSubIterations(self):
        return self._maximumSubIterations

    def setMaximumSubIterations(self, maximumSubIterations):
        assert maximumSubIterations > 0
        if maximumSubIterations != self._maximumSubIterations:
            self._maximumSubIterations = maximumSubIterations
            return True
        return False

    def isUpdateReferenceState(self):
        return self._updateReferenceState

    def setUpdateReferenceState(self, updateReferenceState):
        if updateReferenceState != self._updateReferenceState:
            self._updateReferenceState = updateReferenceState
            return True
        return False

    def run(self, modelFileNameStem=None):
        """
        Fit model geometry parameters to data.
        :param modelFileNameStem: Optional name stem of intermediate output file to write.
        """
        self._fitter.assignDataWeights(self);

        fieldmodule = self._fitter._region.getFieldmodule()
        optimisation = fieldmodule.createOptimisation()
        optimisation.setMethod(Optimisation.METHOD_NEWTON)
        optimisation.addDependentField(self._fitter.getModelCoordinatesField())
        optimisation.setAttributeInteger(Optimisation.ATTRIBUTE_MAXIMUM_ITERATIONS, self._maximumSubIterations)

        #FunctionTolerance = optimisation.getAttributeReal(Optimisation.ATTRIBUTE_FUNCTION_TOLERANCE)
        #GradientTolerance = optimisation.getAttributeReal(Optimisation.ATTRIBUTE_GRADIENT_TOLERANCE)
        #StepTolerance = optimisation.getAttributeReal(Optimisation.ATTRIBUTE_STEP_TOLERANCE)
        MaximumStep = optimisation.getAttributeReal(Optimisation.ATTRIBUTE_MAXIMUM_STEP)
        MinimumStep = optimisation.getAttributeReal(Optimisation.ATTRIBUTE_MINIMUM_STEP)
        #LinesearchTolerance = optimisation.getAttributeReal(Optimisation.ATTRIBUTE_LINESEARCH_TOLERANCE)
        #TrustRegionSize = optimisation.getAttributeReal(Optimisation.ATTRIBUTE_TRUST_REGION_SIZE)

        dataScale = self._fitter.getDataScale()
        #tol_scale = dataScale  # *dataScale
        #FunctionTolerance *= tol_scale
        #optimisation.setAttributeReal(Optimisation.ATTRIBUTE_FUNCTION_TOLERANCE, FunctionTolerance)
        #GradientTolerance /= tol_scale
        #optimisation.setAttributeReal(Optimisation.ATTRIBUTE_GRADIENT_TOLERANCE, GradientTolerance)
        #StepTolerance *= tol_scale
        #optimisation.setAttributeReal(Optimisation.ATTRIBUTE_STEP_TOLERANCE, StepTolerance)
        MaximumStep *= dataScale
        optimisation.setAttributeReal(Optimisation.ATTRIBUTE_MAXIMUM_STEP, MaximumStep)
        MinimumStep *= dataScale
        optimisation.setAttributeReal(Optimisation.ATTRIBUTE_MINIMUM_STEP, MinimumStep)
        #LinesearchTolerance *= dataScale
        #optimisation.setAttributeReal(Optimisation.ATTRIBUTE_LINESEARCH_TOLERANCE, LinesearchTolerance)
        #TrustRegionSize *= dataScale
        #optimisation.setAttributeReal(Optimisation.ATTRIBUTE_TRUST_REGION_SIZE, TrustRegionSize)

        #if self.getDiagnosticLevel() > 0:
        #    print("Function Tolerance", FunctionTolerance)
        #    print("Gradient Tolerance", GradientTolerance)
        #    print("Step Tolerance", StepTolerance)
        #    print("Maximum Step", MaximumStep)
        #    print("Minimum Step", MinimumStep)
        #    print("Linesearch Tolerance", LinesearchTolerance)
        #    print("Trust Region Size", TrustRegionSize)

        dataObjective = None
        deformationPenaltyObjective = None
        edgeDiscontinuityPenaltyObjective = None
        with ChangeManager(fieldmodule):
            dataObjective = self.createDataObjectiveField()
            result = optimisation.addObjectiveField(dataObjective)
            assert result == RESULT_OK, "Fit Geometry:  Could not add data objective field"
            # temporary check until per-group, multi-component penalties implemented:
            if (self.getStrainPenaltyWeight() > 0.0) or (self.getCurvaturePenaltyWeight() > 0.0):
                deformationPenaltyObjective = self.createDeformationPenaltyObjectiveField()
                result = optimisation.addObjectiveField(deformationPenaltyObjective)
                assert result == RESULT_OK, "Fit Geometry:  Could not add strain/curvature penalty objective field"
            #if self._edgeDiscontinuityPenaltyWeight > 0.0:
            #    print("WARNING! Edge discontinuity penalty is not supported by NEWTON solver - skipping")
            #    #edgeDiscontinuityPenaltyObjective = self.createEdgeDiscontinuityPenaltyObjectiveField()
            #    #result = optimisation.addObjectiveField(edgeDiscontinuityPenaltyObjective)
            #    #assert result == RESULT_OK, "Fit Geometry:  Could not add edge discontinuity penalty objective field"

        fieldcache = fieldmodule.createFieldcache()
        objectiveFormat = "{:12e}"
        for iter in range(self._numberOfIterations):
            iterName = str(iter + 1)
            if self.getDiagnosticLevel() > 0:
                print("-------- Iteration " + iterName)
            if self.getDiagnosticLevel() > 0:
                result, objective = dataObjective.evaluateReal(fieldcache, 1)
                print("    Data objective", objectiveFormat.format(objective))
                if deformationPenaltyObjective:
                    result, objective = deformationPenaltyObjective.evaluateReal(fieldcache, deformationPenaltyObjective.getNumberOfComponents())
                    print("    Deformation penalty objective", objectiveFormat.format(objective))
            result = optimisation.optimise()
            if self.getDiagnosticLevel() > 1:
                solutionReport = optimisation.getSolutionReport()
                print(solutionReport)
            assert result == RESULT_OK, "Fit Geometry:  Optimisation failed with result " + str(result)
            if modelFileNameStem:
                self._fitter.writeModel(modelFileNameStem + "_fit" + iterName + ".exf")
            self._fitter.calculateDataProjections(self)

        if self.getDiagnosticLevel() > 0:
            print("--------")
            result, objective = dataObjective.evaluateReal(fieldcache, 1)
            print("    END Data objective", objectiveFormat.format(objective))
            if deformationPenaltyObjective:
                result, objective = deformationPenaltyObjective.evaluateReal(fieldcache, deformationPenaltyObjective.getNumberOfComponents())
                print("    END Deformation penalty objective", objectiveFormat.format(objective))

        if self._updateReferenceState:
            self._fitter.updateModelReferenceCoordinates()

        self.setHasRun(True)

    def createDataObjectiveField(self):
        """
        Get FieldNodesetSum objective for data projected onto mesh, including markers with fixed locations.
        Assumes ChangeManager(fieldmodule) is in effect.
        :return: Zinc FieldNodesetSum.
        """
        fieldmodule = self._fitter.getFieldmodule()
        delta = self._fitter.getDataDeltaField()
        weight = self._fitter.getDataWeightField()
        deltaSq = fieldmodule.createFieldDotProduct(delta, delta)
        #dataProjectionInDirection = fieldmodule.createFieldDotProduct(dataProjectionDelta, self._fitter.getDataProjectionDirectionField())
        #dataProjectionInDirection = fieldmodule.createFieldMagnitude(dataProjectionDelta)
        #dataProjectionInDirection = dataProjectionDelta
        #dataProjectionInDirection = fieldmodule.createFieldConstant([ weight/dataScale ]*dataProjectionDelta.getNumberOfComponents()) * dataProjectionDelta
        dataProjectionObjective = fieldmodule.createFieldNodesetSum(weight*deltaSq, self._fitter.getActiveDataNodesetGroup())
        dataProjectionObjective.setElementMapField(self._fitter.getDataHostLocationField())
        return dataProjectionObjective

    def createDeformationPenaltyObjectiveField(self):
        """
        Only call for non-zero strain or curvature penalty values.
        :return: Zinc field, or None if not weighted.
        Assumes ChangeManager(fieldmodule) is in effect.
        """
        numberOfGaussPoints = 3
        fieldmodule = self._fitter.getFieldmodule()
        mesh = self._fitter.getHighestDimensionMesh()
        dataScale = 1.0
        dimension = mesh.getDimension()
        # future: eliminate effect of model scale
        #linearDataScale = self._fitter.getDataScale()
        #for d in range(dimension):
        #    dataScale /= linearDataScale

        displacementGradient1, displacementGradient2 = createFieldsDisplacementGradients(self._fitter.getModelCoordinatesField(), self._fitter.getModelReferenceCoordinatesField(), mesh)
        deformationTerm = None
        strainPenaltyWeight = self.getStrainPenaltyWeight()
        curvaturePenaltyWeight = self.getCurvaturePenaltyWeight()
        if strainPenaltyWeight > 0.0:
            # future: allow variable alpha components
            alpha = fieldmodule.createFieldConstant([ strainPenaltyWeight*dataScale ]*displacementGradient1.getNumberOfComponents())
            wtSqDeformationGradient1 = fieldmodule.createFieldDotProduct(alpha, displacementGradient1*displacementGradient1)
            assert wtSqDeformationGradient1.isValid()
            deformationTerm = wtSqDeformationGradient1
        if curvaturePenaltyWeight > 0.0:
            # future: allow variable beta components
            beta = fieldmodule.createFieldConstant([ curvaturePenaltyWeight*dataScale ]*displacementGradient2.getNumberOfComponents())
            wtSqDeformationGradient2 = fieldmodule.createFieldDotProduct(beta, displacementGradient2*displacementGradient2)
            assert wtSqDeformationGradient2.isValid()
            deformationTerm = (deformationTerm + wtSqDeformationGradient2) if deformationTerm else wtSqDeformationGradient2

        deformationPenaltyObjective = fieldmodule.createFieldMeshIntegral(deformationTerm, self._fitter.getModelReferenceCoordinatesField(), mesh);
        deformationPenaltyObjective.setNumbersOfPoints(numberOfGaussPoints)
        return deformationPenaltyObjective

    #def createEdgeDiscontinuityPenaltyObjectiveField(self):
    #    """
    #    Only call if self._edgeDiscontinuityPenaltyWeight > 0.0
    #    Assumes ChangeManager(fieldmodule) is in effect.
    #    :return: Zinc FieldMeshIntegralSquares, or None if not weighted.
    #    """
    #    numberOfGaussPoints = 3
    #    fieldmodule = self._fitter.getFieldmodule()
    #    lineMesh = fieldmodule.findMeshByDimension(1)
    #    edgeDiscontinuity = fieldmodule.createFieldEdgeDiscontinuity(self._fitter.getModelCoordinatesField())
    #    dataScale = self._fitter.getDataScale()
    #    weightedEdgeDiscontinuity = edgeDiscontinuity*fieldmodule.createFieldConstant(self._edgeDiscontinuityPenaltyWeight/dataScale)
    #    edgeDiscontinuityPenaltyObjective = fieldmodule.createFieldMeshIntegralSquares(weightedEdgeDiscontinuity, self._fitter.getModelReferenceCoordinatesField(), lineMesh)
    #    edgeDiscontinuityPenaltyObjective.setNumbersOfPoints(numberOfGaussPoints)
    #    return edgeDiscontinuityPenaltyObjective
