import abc

class UploaderBase(abc.ABC):

    @abc.abstractmethod
    async def upload(self, fname: str, content: bytes) -> str:
        ...

    @abc.abstractmethod
    async def close(self):
        ...