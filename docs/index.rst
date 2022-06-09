*scaffoldfitter library*
========================

The *scaffoldfitter library* performs iterative geometric field fitting, optimising the field to fit annotated point data projected onto matching annotated regions of the scaffold. Through its API the client sets up a sequence of config, align and fit steps, each with highly configurable smoothing and other parameters, which progressively move the scaffold geometric field closer to the data, with data reprojected each step. Model representation and fitting is performed with the underlying *OpenCMISS-Zinc library*.

Most users will use this from the ABI Mapping Tools' **Geometry Fitter** user interface for this library. Its documentation of the fitting steps and parameters also applies to this back-end library.

Examples of direct usage are in the tests folder of the library's `github repository <https://github.com/ABI-Software/scaffoldfitter>`_.
