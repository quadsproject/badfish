class BadfishException(Exception):
    pass


class ResourceNotFound(BadfishException):
    """Raised when a Redfish resource is not present on the host.

    Callers that treat "endpoint not present" as a graceful, degradable
    condition should catch this, while auth/transport/server errors (which also
    raise BadfishException) propagate and stay distinguishable.
    """
