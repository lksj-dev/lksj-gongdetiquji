from typing import Mapping, Sequence

from .base import UploaderBase
from .chained import ChainedUploader
from .dpaste import DPatseUploader
from .mclogs import MCLogsUploader
from .paste_ee import PasteEEUploader
from .paste_gg import PasteGGUploader
from .pastebin_com import PastebinDotComUploader

_factories={
    'ascclemens/paste': PasteGGUploader,
    'aternos': MCLogsUploader,
    'dpaste': DPatseUploader,
    'mclo.gs': MCLogsUploader,
    'mclogs': MCLogsUploader,
    'paste.ee': PasteEEUploader,
    'paste.gg': PasteGGUploader,
    'pastebin.com': PastebinDotComUploader
}

def create_uploader(config) -> UploaderBase:
    if isinstance(config, Mapping):
        if config['type'] in _factories:
            return _factories[config['type']](**config)
    elif isinstance(config, Sequence):
        children=[]
        for sub_config in config:
            children.append(create_uploader(sub_config))
        return ChainedUploader(children)
    else:
        raise Exception(f"We do not know how to create uploader from config type {type(config)}")