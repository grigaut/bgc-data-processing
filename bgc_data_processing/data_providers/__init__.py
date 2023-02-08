from typing import TYPE_CHECKING

from bgc_data_processing.data_providers import (
    argo,
    clivar,
    glodap,
    glodap_2019,
    glodap_2022,
    ices,
    imr,
    nmdc,
)

if TYPE_CHECKING:
    from bgc_data_processing.base import BaseLoader

LOADERS: dict[str, "BaseLoader"] = {
    argo.loader.provider: argo.loader,
    clivar.loader.provider: clivar.loader,
    glodap.loader.provider: glodap.loader,
    glodap_2019.loader.provider: glodap_2019.loader,
    glodap_2022.loader.provider: glodap_2022.loader,
    ices.loader.provider: ices.loader,
    imr.loader.provider: imr.loader,
    nmdc.loader.provider: nmdc.loader,
}

__all__ = [
    LOADERS,
]
