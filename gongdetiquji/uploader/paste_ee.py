import asyncio
import logging
import os
import typing

from aiohttp import ClientSession

from .base import UploaderBase, UploadResult

class PasteEEUploader(UploaderBase):
    
    def __init__(self, token: str='', **kwargs):
        self.http_client=ClientSession(headers={ 'X-Auth-Token': token or os.environ['PASTE_EE_TOKEN'] })

    async def upload(self, original_fname: str, files_to_upload: typing.List[typing.Tuple[str, str]]) -> UploadResult:
        payload={
            'description': '由功德提取机 Bot 自动转存',
            'sections': []
        }
        for fname, content in files_to_upload:
            # We have encountered cases where fname exceeds the maximum allowed by paste.ee.
            # Thus we trunctuate it to first 60 characters, following with a ellipsis.
            if len(fname) > 64:
                fname=fname[:60] + '...'
            # We have encountered cases where file content contains NUL character (embedded zero).
            # Thus we remove them before uploading, to avoid issue.
            content=content.translate({ 0: None })
            payload['sections'].append({
                'name': fname,
                'syntax': 'text',
                'contents': content
            })
        async with self.http_client.post('https://api.paste.ee/v1/pastes', json=payload) as resp:
            if resp.ok:
                body=await resp.json()
                if 'link' in body:
                    paste_url=body['link']
                    return UploadResult(True, { fname: paste_url for fname, _ in files_to_upload })
                else:
                    logging.error(f'Uploading {fname} encounters unexpected result! Server response: {str(body)}')
                    raise Exception('paste.ee did not return paste link in response')
            else:
                logging.error(f'paste.ee server returns status code {resp.status} which does not sounds good.')
                raise Exception('paste.ee server is probably down!')

    async def close(self):
        await self.http_client.close()