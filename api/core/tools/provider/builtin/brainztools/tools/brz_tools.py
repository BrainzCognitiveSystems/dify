import json

## Cache
PUBLIC_USER_ID = 'public'
import os
from pathlib import Path
CACHE_path='../_cache_/'
cache_path_obj = Path(CACHE_path)

def Cache_get_path(user_id: str, segment_subpath: str, filename: str=None):
    dst_path = cache_path_obj / user_id / segment_subpath
    os.makedirs(dst_path, exist_ok=True)
    if filename:
        dst_path = dst_path / filename
    return dst_path

def Cache_Store(user_id: str, segment_subpath: str, blob, filename: str):
    thePath = Cache_get_path(user_id, segment_subpath, filename)
    if isinstance(blob, str):
        blob = blob.encode('utf-8')
    with open(thePath, 'wb') as f:
        f.write(blob)
    print(f'Cache_Store: (OK, size={len(blob)}) "{thePath}"')

def Cache_Retrieve(user_id: str, segment_subpath: str, filename: str, test_only=False, fmt:str='json'):
    try:
        thePath = Cache_get_path(user_id, segment_subpath, filename)
        if test_only:
            return os.path.exists(thePath)
        with open(thePath, 'rb') as f:
            data = f.read()
        if fmt == 'json':
            data = json.loads(data)    
        return data
    except Exception as e:
        print(f'Cache_Retrieve: (ERROR) "{thePath}" {e}')
        return None
    
def Cache_Delete(user_id: str, segment_subpath: str, filename: str):
    thePath = Cache_get_path(user_id, segment_subpath, filename)
    try:
        os.remove(thePath)
        print(f'Cache_Delete: (OK) "{thePath}"')
    except Exception as e:
        print(f'Cache_Delete: (ERROR) "{thePath}" {e}')

def Cache_DeleteAll(user_id: str, segment_subpath: str):
    thePath = Cache_get_path(user_id, segment_subpath)
    try:
        for f in os.listdir(thePath):
            os.remove(thePath / f)
        print(f'Cache_DeleteAll: (OK) "{thePath}"')
    except Exception as e:
        print(f'Cache_DeleteAll: (ERROR) "{thePath}" {e}')

def Cache_DeleteUser(user_id: str):
    thePath = cache_path_obj / user_id
    try:
        for f in os.listdir(thePath):
            os.remove(thePath / f)
        os.rmdir(thePath)
        print(f'Cache_DeleteUser: (OK) "{thePath}"')
    except Exception as e:
        print(f'Cache_DeleteUser: (ERROR) "{thePath}" {e}')

def Cache_DeleteAllUsers():
    try:
        for f in os.listdir(cache_path_obj):
            os.remove(cache_path_obj / f)
        print(f'Cache_DeleteAllUsers: (OK) "{cache_path_obj}"')
    except Exception as e:
        print(f'Cache_DeleteAllUsers: (ERROR) "{cache_path_obj}" {e}')
        
def Cache_DeleteAllCache():
    try:
        for f in os.listdir(cache_path_obj):
            os.remove(cache_path_obj / f)
        os.rmdir(cache_path_obj)
        print(f'Cache_DeleteAllCache: (OK) "{cache_path_obj}"')
    except Exception as e:
        print(f'Cache_DeleteAllCache: (ERROR) "{cache_path_obj}" {e}')
        
## =================================================================================================

def url_detect_file_type(url):
    print(f'!!url_detect_file_type: url={url}')
    properties = {}
    try:
        # find regex like "https://www.youtube.com/watch?v=xxxxx"
        m = re.search(r"http[s]://www.youtube.com/watch\?v=([\-\w]+)", url)

        if not m:
            # find regex like "https://youtu.be/hKa3EZqofNo"
            m = re.search(r"http[s]://youtu.be/([\-\w]+)", url)

        print(f'!!m={m}')

        if m:
            properties["url_type"] = "video"
            properties["url_source"] = "youtube"
            properties["doc_id"] = m.group(1)

        if not m:
            # find regex like https://www.youtube.com/channel/UCF9IOB2TExg3QIBupFtBDxg
            m = re.search(r"http[s]://www.youtube.com/channel/(\w+)", url)
            if m:
                properties["url_type"] = "channel"
                properties["url_source"] = "youtube"
                properties["doc_id"] = m.group(1)

        if not m:
            # find regex like "https://odysee.com/@LaUneTV2:c/LeDebatdeNatacha(30)_JIM_BLET:d"
            # https://odysee.com/@QuadrillageTraduction:1/trim.A98CCED0-E8A4-40CB-89C5-BC19ABADB6D4:4
            m = re.search(r"http[s]://odysee.com/@(\w+:\w)/(\w+:\w)", url)
            if m:
                properties["url_type"] = "video"
                properties["url_source"] = "odysee"
                properties["url_channel"] = m.group(1)
                properties["doc_id"] = m.group(2)

        if not m:
            # find regex like https://odysee.com/@QuadrillageTraduction:1
            m = re.search(r"http[s]://odysee.com/@(\w+:\w)", url)
            if m:
                properties["url_type"] = "channel"
                properties["url_source"] = "odysee"
                properties["url_channel"] = m.group(1)
        
        if not m:
            tgt = "http://dx.doi.org/https://doi.org/1"
            if url.startswith(tgt):
                properties['url'] = url.replace(tgt, "https://doi.org/")
    except: pass
    print('')
    return properties

## =================================================================================================