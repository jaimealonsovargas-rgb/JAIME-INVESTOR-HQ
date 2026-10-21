"""Local personal research is distinct from redistribution and valuation rights."""


def readable(rights, *, local_research=False):
    base = rights.access_allowed and rights.display_allowed and rights.storage_allowed
    return bool(base and (rights.redistribution_allowed or
        (local_research and rights.local_research_allowed and rights.scope == 'personal')))
