class CoreError(RuntimeError):
    """Base error for VerifySignal Core adapter failures."""


class CoreMissingError(CoreError):
    """VerifySignal Core executable was not found."""


class CoreIncompatibleError(CoreError):
    """VerifySignal Core public contract is incompatible with VerifySignal Spec."""


class CoreExecutionError(CoreError):
    """VerifySignal Core command failed."""


class CoreValidationError(CoreError):
    """VerifySignal Core validation returned blockers."""


class CoreReportError(CoreError):
    """VerifySignal Core report inspection failed."""


class RuntimeInputError(CoreError):
    """A required runtime input is missing."""
