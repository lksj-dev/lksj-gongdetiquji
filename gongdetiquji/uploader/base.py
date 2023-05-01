import abc
import typing

class UploadResult(typing.NamedTuple):
    success: bool
    links: typing.Mapping[str, str]

class UploaderBase(abc.ABC):

    @abc.abstractmethod
    async def upload(self, original_fname: str, files_to_upload: typing.List[typing.Tuple[str, str]]) -> UploadResult:
        ...

    @abc.abstractmethod
    async def close(self):
        ...