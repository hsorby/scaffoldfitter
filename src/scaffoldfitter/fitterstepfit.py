"""
Fit step for gross alignment and scale.
"""

from opencmiss.utils.zinc.field import assignFieldParameters, createFieldsDisplacementGradients
from opencmiss.utils.zinc.general import ChangeManager
from opencmiss.zinc.field import Field, FieldFindMeshLocation
from opencmiss.zinc.optimisation import Optimisation
from opencmiss.zinc.result import RESULT_OK
from scaffoldfitter.fitterstep import FitterStep

class FitterStepFit(FitterStep):

    _jsonTypeId = "_FitterStepFit"

    def __init__(self):
        super(FitterStepFit, self).__init__()
        self._lineWeight = 10.0
        self._markerWeight = 1.0
        self._strainPenaltyWeight = 0.0
        self._curvaturePenaltyWeight = 0.0
        self._edgeDiscontinuityPenaltyWeight = 0.0
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
        assert self._jsonTypeId in dctIn
        # ensure all new options are in dct
        dct = self.encodeSettingsJSONDict()
        dct.update(dctIn)
        self._lineWeight = dct["lineWeight"]
        self._markerWeight = dct["markerWeight"]
        self._strainPenaltyWeight = dct["strainPenaltyWeight"]
        self._curvaturePenaltyWeight = dct["curvaturePenaltyWeight"]
        self._edgeDiscontinuityPenaltyWeight = dct["edgeDiscontinuityPenaltyWeight"]
        self._numberOfIterations = dct["numberOfIterations"]
        self._maximumSubIterations = dct["maximumSubIterations"]
        self._updateReferenceState = dct["updateReferenceState"]

    def encodeSettingsJSONDict(self) -> dict:
        """
        Encode definition of step in dict.
        :return: Settings in a dict ready for passing to json.dump.
        """
        return {
            self._jsonTypeId : True,
            "lineWeight" : self._lineWeight,
            "markerWeight" : self._markerWeight,
            "strainPenaltyWeight" : self._strainPenaltyWeight,
            "curvaturePenaltyWeight" : self._curvaturePenaltyWeight,
            "edgeDiscontinuityPenaltyWeight" : self._edgeDiscontinuityPenaltyWeight,
            "numberOfIterations" : self._numberOfIterations,
            "maximumSubIterations" : self._maximumSubIterations,
            "updateReferenceState" : self._updateReferenceState
            }

    def getLineWeight(self):
        return self._lineWeight

    def setLineWeight(self, weight):
        assert weight >= 0.0
        if weight != self._lineWeight:
            self._lineWeight = weight
            return True
        return False

    def getMarkerWeight(self):
        return self._markerWeight

    def setMarkerWeight(self, weight):
        assert weight >= 0.0
        if weight != self._markerWeight:
            self._markerWeight = weight
            return True
        return False

    def getStrainPenaltyWeight(self):
        return self._strainPenaltyWeight

    def setStrainPenaltyWeight(self, weight):
        assert weight >= 0.0
        if weight != self._strainPenaltyWeight:
            self._strainPenaltyWeight = weight
            return True
        return False

    def getCurvaturePenaltyWeight(self):
        return self._curvaturePenaltyWeight

    def setCurvaturePenaltyWeight(self, weight):
        assert weight >= 0.0
        if weight != self._curvaturePenaltyWeight:
            self._curvaturePenaltyWeight = weight
            return True
        return False

    def getEdgeDiscontinuityPenaltyWeight(self):
        return self._edgeDiscontinuityPenaltyWeight

    def setEdgeDiscontinuityPenaltyWeight(self, weight):
        assert weight >= 0.0
        if weight != self._edgeDiscontinuityPenaltyWeight:
            self._edgeDiscontinuityPenaltyWeight = weight
            return True
        return False

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
        fieldmodule = self._fitter._region.getFieldmodule()
        optimisation = fieldmodule.createOptimisation()
        optimisation.setMethod(Optimisation.METHOD_LEAST_SQUARES_QUASI_NEWTON)
        optimisation.addIndependentField(self._fitter.getModelCoordinatesField())
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

        dataProjectionObjective = [ None, None ]
        dataProjectionObjectiveComponentsCount = [ 0, 0 ]
        markerObjectiveField = None
        deformationPenaltyObjective = None
        edgeDiscontinuityPenaltyObjective = None
        with ChangeManager(fieldmodule):
            for dimension in range(1, 3):
                if self._fitter.getDataProjectionNodesetGroup(dimension).getSize() > 0:
                    dataProjectionObjective[dimension - 1] = self.createDataProjectionObjectiveField(dimension, self._lineWeight if (dimension == 1) else 1.0)
                    dataProjectionObjectiveComponentsCount[dimension - 1] = dataProjectionObjective[dimension - 1].getNumberOfComponents()
                    result = optimisation.addObjectiveField(dataProjectionObjective[dimension - 1])
                    assert result == RESULT_OK, "Fit Geometry:  Could not add data projection objective field for dimension " + str(dimension)
            if self._fitter.getMarkerGroup() and self._fitter.getMarkerDataLocationNodesetGroup() and \
                    (self._fitter.getMarkerDataLocationNodesetGroup().getSize() > 0) and (self._markerWeight > 0.0):
                markerObjectiveField = self.createMarkerObjectiveField(self._markerWeight)
                result = optimisation.addObjectiveField(markerObjectiveField)
                assert result == RESULT_OK, "Fit Geometry:  Could not add marker objective field"
            if (self._strainPenaltyWeight > 0.0) or (self._curvaturePenaltyWeight > 0.0):
                deformationPenaltyObjective = self.createDeformationPenaltyObjectiveField()
                result = optimisation.addObjectiveField(deformationPenaltyObjective)
                assert result == RESULT_OK, "Fit Geometry:  Could not add strain/curvature penalty objective field"
            if self._edgeDiscontinuityPenaltyWeight > 0.0:
                edgeDiscontinuityPenaltyObjective = self.createEdgeDiscontinuityPenaltyObjectiveField()
                result = optimisation.addObjectiveField(edgeDiscontinuityPenaltyObjective)
                assert result == RESULT_OK, "Fit Geometry:  Could not add edge discontinuity penalty objective field"

        fieldcache = fieldmodule.createFieldcache()
        for iter in range(self._numberOfIterations):
            if self.getDiagnosticLevel() > 0:
                print("-------- Iteration", iter + 1)
            if self.getDiagnosticLevel() > 0:
                for d in range(2):
                    if dataProjectionObjective[d]:
                        result, objective = dataProjectionObjective[d].evaluateReal(fieldcache, dataProjectionObjectiveComponentsCount[d])
                        print("    " + str(d + 1) + "-D data projection objective", objective)
                if markerObjectiveField:
                    result, objective = markerObjectiveField.evaluateReal(fieldcache, markerObjectiveField.getNumberOfComponents())
                    print("    marker objective", objective)
                if deformationPenaltyObjective:
                    result, objective = deformationPenaltyObjective.evaluateReal(fieldcache, deformationPenaltyObjective.getNumberOfComponents())
                    print("    deformation penalty objective", objective)
            result = optimisation.optimise()
            if self.getDiagnosticLevel() > 1:
                solutionReport = optimisation.getSolutionReport()
                print(solutionReport)
            assert result == RESULT_OK, "Fit Geometry:  Optimisation failed with result " + str(result)
            self._fitter.calculateDataProjections(self)
            if modelFileNameStem:
                self._fitter.writeModel(modelFileNameStem + "_fit" + str(iter + 1) + ".exf")
        if self.getDiagnosticLevel() > 0:
            print("--------")

        if self.getDiagnosticLevel() > 0:
            for d in range(2):
                if dataProjectionObjective[d]:
                    result, objective = dataProjectionObjective[d].evaluateReal(fieldcache, dataProjectionObjectiveComponentsCount[d])
                    print("END " + str(d + 1) + "-D data projection objective", objective)
            if markerObjectiveField:
                result, objective = markerObjectiveField.evaluateReal(fieldcache, markerObjectiveField.getNumberOfComponents())
                print("END marker objective", objective)
            if deformationPenaltyObjective:
                result, objective = deformationPenaltyObjective.evaluateReal(fieldcache, deformationPenaltyObjective.getNumberOfComponents())
                print("END deformation penalty objective", objective)

        if self._updateReferenceState:
            self._fitter.updateModelReferenceCoordinates()

        self.setHasRun(True)

    def createDataProjectionObjectiveField(self, dimension, weight):
        """
        Get FieldNodesetSumSquares objective for data projected onto mesh of dimension.
        Minimises length in projection direction, allowing sliding fit.
        Only call if self._fitter.getDataProjectionNodesetGroup().getSize() > 0
        Assumes ChangeManager(fieldmodule) is in effect.
        :param dimension: Mesh dimension 1 or 2.
        :param weight: Real weight to multiply objective terms by.
        :return: Zinc FieldNodesetSumSquares.
        """
        fieldmodule = self._fitter.getFieldmodule()
        dataScale = self._fitter.getDataScale()
        dataProjectionDelta = self._fitter.getDataProjectionDeltaField(dimension)
        #dataProjectionInDirection = fieldmodule.createFieldDotProduct(dataProjectionDelta, self._fitter.getDataProjectionDirectionField())
        #dataProjectionInDirection = fieldmodule.createFieldMagnitude(dataProjectionDelta)
        #dataProjectionInDirection = dataProjectionDelta
        dataProjectionInDirection = fieldmodule.createFieldConstant([ weight/dataScale ]*dataProjectionDelta.getNumberOfComponents()) * dataProjectionDelta
        dataProjectionObjective = fieldmodule.createFieldNodesetSumSquares(dataProjectionInDirection, self._fitter.getDataProjectionNodesetGroup(dimension))
        return dataProjectionObjective

    def createMarkerObjectiveField(self, weight):
        """
        Only call if self._fitter.getMarkerGroup() and (self._fitter.getMarkerDataLocationNodesetGroup().getSize() > 0) and (self._markerWeight > 0.0)
        For marker datapoints with locations in model, creates a FieldNodesetSumSquares
        of coordinate projections to those locations.
        Assumes ChangeManager(fieldmodule) is in effect.
        :return: Zinc FieldNodesetSumSquares.
        """
        fieldmodule = self._fitter.getFieldmodule()
        dataScale = self._fitter.getDataScale()
        markerDataLocation, markerDataLocationCoordinates, markerDataDelta = self._fitter.getMarkerDataLocationFields()
        markerDataWeightedDelta = markerDataDelta*fieldmodule.createFieldConstant([ weight/dataScale ]*markerDataDelta.getNumberOfComponents())
        markerDataObjective = fieldmodule.createFieldNodesetSumSquares(markerDataWeightedDelta, self._fitter.getMarkerDataLocationNodesetGroup())
        return markerDataObjective

    def createDeformationPenaltyObjectiveField(self):
        """
        Only call if (self._strainPenaltyWeight > 0.0) or (self._curvaturePenaltyWeight > 0.0)
        :return: Zinc FieldMeshIntegralSquares, or None if not weighted.
        Assumes ChangeManager(fieldmodule) is in effect.
        """
        numberOfGaussPoints = 3
        fieldmodule = self._fitter.getFieldmodule()
        mesh = self._fitter.getHighestDimensionMesh()
        dataScale = self._fitter.getDataScale()
        displacementGradient1, displacementGradient2 = createFieldsDisplacementGradients(self._fitter.getModelCoordinatesField(), self._fitter.getModelReferenceCoordinatesField(), mesh)
        if self._strainPenaltyWeight > 0.0:
            weightedDisplacementGradient1 = displacementGradient1*fieldmodule.createFieldConstant([ self._strainPenaltyWeight ]*displacementGradient1.getNumberOfComponents())
        else:
            weightedDisplacementGradient1 = None
        if self._curvaturePenaltyWeight > 0.0:
            weightedDisplacementGradient2 = displacementGradient2*fieldmodule.createFieldConstant([ self._curvaturePenaltyWeight ]*displacementGradient2.getNumberOfComponents())
        else:
            weightedDisplacementGradient2 = None

        if weightedDisplacementGradient1:
            if weightedDisplacementGradient2:
                deformationField = fieldmodule.createFieldConcatenate([ weightedDisplacementGradient1, weightedDisplacementGradient2 ])
            else:
                deformationField = weightedDisplacementGradient1
        elif weightedDisplacementGradient2:
            deformationField = weightedDisplacementGradient2
        else:
            return None

        scaledModelReferenceCoordinatesField = self._fitter.getModelReferenceCoordinatesField()*fieldmodule.createFieldConstant([ 1.0/dataScale ]*3)
        deformationPenaltyObjective = fieldmodule.createFieldMeshIntegralSquares(deformationField, scaledModelReferenceCoordinatesField, mesh)
        deformationPenaltyObjective.setNumbersOfPoints(numberOfGaussPoints)
        return deformationPenaltyObjective

    def createEdgeDiscontinuityPenaltyObjectiveField(self):
        """
        Only call if self._edgeDiscontinuityPenaltyWeight > 0.0
        Assumes ChangeManager(fieldmodule) is in effect.
        :return: Zinc FieldMeshIntegralSquares, or None if not weighted.
        """
        numberOfGaussPoints = 3
        fieldmodule = self._fitter.getFieldmodule()
        lineMesh = fieldmodule.findMeshByDimension(1)
        edgeDiscontinuity = fieldmodule.createFieldEdgeDiscontinuity(self._fitter.getModelCoordinatesField())
        dataScale = self._fitter.getDataScale()
        weightedEdgeDiscontinuity = edgeDiscontinuity*fieldmodule.createFieldConstant(self._edgeDiscontinuityPenaltyWeight/dataScale)
        edgeDiscontinuityPenaltyObjective = fieldmodule.createFieldMeshIntegralSquares(weightedEdgeDiscontinuity, self._fitter.getModelReferenceCoordinatesField(), lineMesh)
        edgeDiscontinuityPenaltyObjective.setNumbersOfPoints(numberOfGaussPoints)
        return edgeDiscontinuityPenaltyObjective
