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
        self._fitter.assignDataWeights(self._lineWeight, self._markerWeight);

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
            if (self._strainPenaltyWeight > 0.0) or (self._curvaturePenaltyWeight > 0.0):
                deformationPenaltyObjective = self.createDeformationPenaltyObjectiveField()
                result = optimisation.addObjectiveField(deformationPenaltyObjective)
                assert result == RESULT_OK, "Fit Geometry:  Could not add strain/curvature penalty objective field"
            if self._edgeDiscontinuityPenaltyWeight > 0.0:
                print("WARNING! Edge discontinuity penalty is not supported by NEWTON solver - skipping")
                #edgeDiscontinuityPenaltyObjective = self.createEdgeDiscontinuityPenaltyObjectiveField()
                #result = optimisation.addObjectiveField(edgeDiscontinuityPenaltyObjective)
                #assert result == RESULT_OK, "Fit Geometry:  Could not add edge discontinuity penalty objective field"

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

        if self.getDiagnosticLevel() > 0:
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
        Only call if (self._strainPenaltyWeight > 0.0) or (self._curvaturePenaltyWeight > 0.0)
        :return: Zinc FieldMeshIntegral, or None if not weighted.
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
        if self._strainPenaltyWeight > 0.0:
            # future: allow variable alpha components
            alpha = fieldmodule.createFieldConstant([ self._strainPenaltyWeight*dataScale ]*displacementGradient1.getNumberOfComponents())
            wtSqDeformationGradient1 = fieldmodule.createFieldDotProduct(alpha, displacementGradient1*displacementGradient1)
            assert wtSqDeformationGradient1.isValid()
            deformationTerm = wtSqDeformationGradient1
        if self._curvaturePenaltyWeight > 0.0:
            # future: allow variable beta components
            beta = fieldmodule.createFieldConstant([ self._curvaturePenaltyWeight*dataScale ]*displacementGradient2.getNumberOfComponents())
            wtSqDeformationGradient2 = fieldmodule.createFieldDotProduct(beta, displacementGradient2*displacementGradient2)
            assert wtSqDeformationGradient2.isValid()
            deformationTerm = (deformationTerm + wtSqDeformationGradient2) if deformationTerm else wtSqDeformationGradient2

        deformationPenaltyObjective = fieldmodule.createFieldMeshIntegral(deformationTerm, self._fitter.getModelReferenceCoordinatesField(), mesh);
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
