from typing import Any, Union

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

import json
import re


# according to https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file

# https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#embedding-yt-dlp

import os
import subprocess

def Subprocess_with_line_callback(command, line_callback):

    # Start the process
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Read the output stream incrementally
    while True:
        output_line = process.stdout.readline()
        if not output_line:
            break  # Break the loop if no more output
        yield output_line  # Yield the output line instead of printing

    # Wait for the process to terminate and get the exit code
    exit_code = process.wait()
    if exit_code != 0:
        raise Exception(f"Process exited with code {exit_code}")


YTDLP_path = 'yt-dlp'

def YTDLP_do(video_ids, command='download', dst_path='../videos/', options_str="-o '%(title)s.%(ext)s'"):

    # check if dst_path exists
    os.makedirs(dst_path, exist_ok=True)

    log = []
    results = []
    def line_callback(line) -> None:
        log.append(line)
        if line.startswith('[download]'):
            results.append(line)

    max_height = 480
## ex: 
# yt-dlp --download-archive /YTD-archive.txt -i --max-downloads 51 --playlist-end 52 -r 10M --write-info-json --write-description --write-thumbnail 
#     -f 'bestvideo[height<=480]+bestaudio/best[height<=480]/18/http-360p/http-360p/http-240p/http-280p/http-280-0/93/92/94/95/bestvideo[height<=540]+bestaudio/best[height<=540]/bestvideo[height<=720]+bestaudio/best[height<=720]/mp4/replay-600/3+4/2+4/1+4'
#     -o '/home/user/TMP/%(uploader)s/%(upload_date)s %(title)s !!%(duration)ssec!-%(id)s.%(ext)s' -- 'https://www.youtube.com/watch?v=3JWTaaS7LdU'



    if command!='download':
        meta = {
            'success': False,
            'error': 'command not supported',
            'results_nbr': 0,
        }
        return results, meta
    
    if command=='download':
        args = []
        args += ['-i', '--max-downloads', '51', '--playlist-end', '52', '-r', '10M', '--write-info-json', '--write-description', '--write-thumbnail']
        if not max_height or max_height==480:
            args += ['-f', 'bestvideo[height<=480]+bestaudio/best[height<=480]/18/http-360p/http-360p/http-240p/http-280p/http-280-0/93/92/94/95/bestvideo[height<=540]+bestaudio/best[height<=540]/bestvideo[height<=720]+bestaudio/best[height<=720]/mp4/replay-600/3+4/2+4/1+4']
        elif max_height==720:
            args += ['-f', 'bestvideo[height<=720]+bestaudio/best[height<=720]/mp4/replay-600/3+4/2+4/1+4']
        else:
            args += ['-f', 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/mp4/replay-600/3+4/2+4/1+4']
        args += ['-o', f'{dst_path}/%(channel_id)s/%(upload_date)s %(title)s !!%(duration)ssec H%(height)s #%(id)s.%(ext)s']
        command = [YTDLP_path] + args + video_ids
    
    print(f"Command: {command}")

    # Start the process
    try:
        Subprocess_with_line_callback(command, line_callback)
        exit_code = 0
    except Exception as e:
        print(f"Error: {e}")
        exit_code = -1
    print(f"Process exited with code {exit_code}")

    meta = {
        'success': exit_code==0,
        'log': log,
        'results_nbr': len(results),
    }



class VideoDownloader():

    def ExtractInformation(self):
        infos = []
        print(json.dumps(infos))
        return infos
    
    @staticmethod
    def DownloadVideos(self, subpath, video_ids, options={}):
        options_str = " ".join([ f"--{key} {value}" for key, value in options.items() ])
        results, meta = YTDLP_do(video_ids, command='download', dst_path='../videos'/subpath, options_str=options_str)
        return results, meta

def Youtube_parse_video_ids(iris, with_info=False):
    iris_lst = iris.replace(' ','|').replace('||','|').split('|')
    videos=[]
    for iri in iris_lst:
        m = re.search(r"(http[s])://www.youtube.com/watch?v=(\w+)", iri)
        if not m:
            m = re.search(r"(http[s])://youtu.be/(\w+)", iri)
        # if not /^https?:\/\/(?:www\.)?youtube.com\/(?:watch\?v=|embed\/|v\/|shorts\/|channel\/|user\/)[a-zA-Z0-9_-]{11}$/
        #     m = re.search(r"(\w+)", iri)
        if m:
            if with_info:
                video = {
                    'video_source' : 'youtube',
                    'protocol' : m.group(1),
                    'video_id' : m.group(2),
                    'video_iri' : iri,
                }
                videos.append(video)
            else:
                videos.append(m.group(2))
    return videos

class VideoDownloader_BrainzTools(BuiltinTool):

    def get_params(self, tool_parameters: dict[str, Any]) -> dict[str, Any]:
        # source=[youtube, odysee, ...]
        # find regex like 'https://www.youtube.com/watch?v=BaW_jenozKc'
        params = { 'params': tool_parameters}
        iris = tool_parameters.get('video_iris') or 'https://www.youtube.com/watch?v=BaW_jenozKc'
        params['videos'] = Youtube_parse_video_ids(iris, with_info=True)
        return params

    def results(self, params: dict) -> dict:
        subPath = params('user_id') or 'default'
        video_ids = [ video['video_id'] for video in params['videos'] ]
        results, meta = VideoDownloader.DownloadVideos(self, subPath, video_ids, options={})
        results = [ self.create_json_message(obj) for obj in results ]
        params['success'] = meta['success']
        params['log'] = meta['log']
        params['results_nbr'] = len(results)
        params['lg_index'] = { lg: i for i, lg in enumerate(video_ids)}
        return results, params

    def _invoke(self,
                user_id: str,
                tool_parameters: dict[str, Any],
        ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:

        try:
            params = self.get_params(tool_parameters)
            params['user_id'] = user_id
            results, meta = self.results(params)
        except Exception as e:
            msg = f'System Error in calling tool "{__class__}"\n\t{e}'
            results = []
            meta = {
                'success': False,
                'error': msg,
                'results_nbr': 0,
            }
        return results, meta


## =======================================
## === [ Using yt-dlp python package ] ===
## =======================================

# import yt_dlp

# class VideoDownloader_lib():

#     def ExtractInformation(self):
        
#         with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
#             info_ = ydl.extract_info(self.URL, download=False)

#         # ydl.sanitize_info makes the info json-serializable
#         # -> See help(yt_dlp.YoutubeDL) for a list of available options and public functions
#         info = ydl.sanitize_info(info_)
#         print(json.dumps(info))
#         return info
    
#     @classmethod
#     def Download_from_infoJson(json_text):
#         INFO_FILE = 'path/to/video.info.json'

#         with yt_dlp.YoutubeDL() as ydl:
#             error_code = ydl.download_with_info_file(INFO_FILE)

#         print('Some videos failed to download' if error_code
#             else 'All videos successfully downloaded')
        
#     def ExtractAudio(self):
#         URLS = ['https://www.youtube.com/watch?v=BaW_jenozKc']

#         ydl_opts = {
#             'format': 'm4a/bestaudio/best',
#             # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
#             'postprocessors': [{  # Extract audio using ffmpeg
#                 'key': 'FFmpegExtractAudio',
#                 'preferredcodec': 'm4a',
#             }]
#         }

#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             error_code = ydl.download(URLS)

#     def DownloadVideo(self):
#         URLS = ['https://www.youtube.com/watch?v=BaW_jenozKc']

#         class MyLogger:
#             def debug(self, msg):
#                 # For compatibility with youtube-dl, both debug and info are passed into debug
#                 # You can distinguish them by the prefix '[debug] '
#                 if not msg.startswith('[debug] '):
#                     self.info(msg)
#                     return
#                 # trace the debug messages here
#                 print(msg)
#                 pass

#             def info(self, msg):
#                 print(msg)
#                 pass

#             def warning(self, msg):
#                 print(msg)
#                 pass

#             def error(self, msg):
#                 print(msg)


#         # ℹ️ See "progress_hooks" in help(yt_dlp.YoutubeDL)
#         def my_hook(d):
#             if d['status'] == 'finished':
#                 print('Done downloading, now post-processing ...')


#         ydl_opts = {
#             'logger': MyLogger(),
#             'progress_hooks': [my_hook],
#         }

#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.download(URLS)


    
