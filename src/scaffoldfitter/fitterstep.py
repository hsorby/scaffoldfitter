"""
Base class for fitter steps.
"""


class FitterStep:
    """
    Base class for fitter steps.
    """

    def __init__(self):
        """
        Construct and add to Fitter.
        """
        self._fitter = None  # set by subsequent client call to Fitter.addFitterStep()
        self._hasRun = False

    def getFitter(self):
        return self._fitter

    def _setFitter(self, fitter):
        '''
        Should only be called by Fitter when adding or removing from it.
        '''
        self._fitter = fitter

    def hasRun(self):
        return self._hasRun

    def setHasRun(self, hasRun):
        self._hasRun = hasRun

    def getDiagnosticLevel(self):
        return self._fitter.getDiagnosticLevel()

    def run(self):
        """
        Override to perform action of derived FitStep
        """
        pass
