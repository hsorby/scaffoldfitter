import math
import os
import unittest
from opencmiss.utils.zinc.field import createFieldMeshIntegral
from opencmiss.zinc.result import RESULT_OK
from scaffoldfitter.fitter import Fitter
from scaffoldfitter.fitterstepfit import FitterStepFit

here = os.path.abspath(os.path.dirname(__file__))


class Fit2dTestCase(unittest.TestCase):

    def test_fit_breast2d(self):
        """
        Test 2D fit with curvature penalty requiring fibre field to be set.
        """
        zinc_model_file = os.path.join(here, "resources", "breast_plate.exf")
        zinc_data_file = os.path.join(here, "resources", "breast_data.exf")
        fitter = Fitter(zinc_model_file, zinc_data_file)
        fitter.setDiagnosticLevel(1)
        fitter.load()

        fit1 = FitterStepFit()
        fitter.addFitterStep(fit1)
        self.assertEqual(2, len(fitter.getFitterSteps()))
        fit1.setGroupCurvaturePenalty(None, [100.0])
        # can't use a curvature penalty without a fibre field
        with self.assertRaises(AssertionError) as cm:
            fit1.run()
        self.assertEqual(str(cm.exception),
                         "Must supply a fibre field to use strain/curvature penalties "
                         "with mesh dimension < coordinate components.")

        # set the in-built zero fibres field
        fieldmodule = fitter.getFieldmodule()
        zeroFibreField = fieldmodule.findFieldByName("zero fibres")
        self.assertTrue(zeroFibreField.isValid())
        fitter.setFibreField(zeroFibreField)
        fitter.load()

        # check these now as different after re-load
        fieldmodule = fitter.getFieldmodule()
        coordinates = fitter.getModelCoordinatesField()
        self.assertEqual(coordinates.getName(), "coordinates")
        self.assertEqual(fitter.getDataCoordinatesField().getName(), "data_coordinates")

        fit1.run()

        # check surface area of fitted coordinates
        # Note name is only prefixes with "fitted " when written with Fitter.writeModel
        surfaceAreaField = createFieldMeshIntegral(coordinates, fitter.getMesh(2), number_of_points=4)
        valid = surfaceAreaField.isValid()
        self.assertTrue(surfaceAreaField.isValid())
        fieldcache = fieldmodule.createFieldcache()
        result, surfaceArea = surfaceAreaField.evaluateReal(fieldcache, 1)
        self.assertEqual(result, RESULT_OK)
        self.assertAlmostEqual(surfaceArea, 104501.36293993103, delta=1.0E-1)


if __name__ == "__main__":
    unittest.main()
