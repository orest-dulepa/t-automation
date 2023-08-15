class MissingClient(Exception):
    """
    Client in Invoice but NOT in CR
    """

    pass


class DuplicatedClient(Exception):
    """
    Client with same fullname in CR but different Client ID
    """

    pass


class NoCRResults(Exception):
    """
    Filter returns 'No search results'
    """

    pass


class NoBulkApply(Exception):
    """
    Bulk Apply button didnt appear. Happens when no rows selected
    """

    pass


class EmptyGDrive(Exception):
    """
    Empty GDrive files result. Folder could be empty or incorrect name
    """

    pass
