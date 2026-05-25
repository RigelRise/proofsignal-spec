class CoreError(RuntimeError):
    """Base error for ProofSignal Core adapter failures."""


class CoreMissingError(CoreError):
    """ProofSignal Core executable was not found."""


class CoreIncompatibleError(CoreError):
    """ProofSignal Core public contract is incompatible with ProofSignal Spec."""


class CoreExecutionError(CoreError):
    """ProofSignal Core command failed."""


class CoreValidationError(CoreError):
    """ProofSignal Core validation returned blockers."""


class CoreReportError(CoreError):
    """ProofSignal Core report inspection failed."""


class RuntimeInputError(CoreError):
    """A required runtime input is missing."""
