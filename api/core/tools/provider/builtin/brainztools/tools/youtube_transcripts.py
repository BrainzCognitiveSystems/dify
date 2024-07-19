from typing import Any, Union

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

from .brz_tools import *

# according to https://pypi.org/project/youtube-transcript-api/
def Youtube_get_transcripts(user_id: str, video_id, languages=["en", "fr"], keep_all_manual_transcripts=True, use_cache=True):
    from youtube_transcript_api import YouTubeTranscriptApi

    def Transcript_properties(transcript):
        # the Transcript object provides metadata properties
        properties = {
            "video_id": transcript.video_id,
            "language": transcript.language,
            "language_code": transcript.language_code,
        
            # whether it has been manually created or generated by YouTube
            "is_generated": transcript.is_generated,
            
            # whether this transcript can be translated or not
            "is_translatable": transcript.is_translatable,
            
            # a list of languages the transcript can be translated to
            "translation_languages_codes": [ dic['language_code'] for dic in transcript.translation_languages ],
        }
        print(properties)
        return properties

    def Transcript_fix_Text_and_stats(transcript):
        # The code `"\u00a0\n"` in a text string represents two characters:
        # `\u00a0`: This is a Unicode escape sequence representing a non-breaking space (NBSP).
        # So, the string `"\u00a0\n"` combines these two characters: a non-breaking space followed by a newline character.

        for rec in transcript.get('data') or []:
            try:
                text = rec['text'].replace("\u00a0"," ").replace("\n",' ')
                text = " ".join(text.split())
                rec['text'] = text
            except Exception as e:
                print(f'!!Transcript_fix_Text_and_stats: (ERROR) {e}')

        try:
            text = transcript['text']
            text = text.replace("\u00a0"," ").replace("\n",' ') # .replace('\r', ' ').replace('\t', ' ').replace('  ', ' ')
            text = " ".join(text.split()) # remove multiple spaces, tabs, newlines ; 6 times faster than re.sub(r'\s+', ' ', text)
        except Exception as e:
            print(f'!!Transcript_fix_Text_and_stats: (ERROR) {e}')
        transcript['text'] = text

        transcript['text_size'] = len(text)
        punctuation_nbr = len([c for c in text if c in '.,;:!?'])
        transcript['punctuation_nbr'] = punctuation_nbr
        transcript['punctuation_pct'] = round(100 * punctuation_nbr / len(text),2) if len(text) > 0 else 0


    transcripts = { }
    print(f'!!transcripts (1) ={transcripts}')
    # return transcripts

    if use_cache and languages != "*":
        for language_code in languages:
            dic = Cache_Retrieve(PUBLIC_USER_ID, 'transcripts', f'YT~{video_id}~{language_code}.json', fmt='json')
            if dic:
                transcripts[language_code] = dic
        if len(transcripts) == len(languages):
            # we already got what we need
            return transcripts


    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except Exception as e:
        print(f'!!transcript_list is missing ? (1a) {e}')
        return transcripts
    
    print(f'!!transcript_list (1b) {transcript_list}')
# (MANUALLY CREATED)  <= is_generated=False
#  - en-US ("English (United States)")[TRANSLATABLE]

# (GENERATED)
#  - en ("English (auto-generated)")[TRANSLATABLE]

# (TRANSLATION LANGUAGES)
#  - af ("Afrikaans")
#  - ak ("Akan")
#  - sq ("Albanian")
# ...

    transcripts_dict = {}
    # iterate over all available transcripts => transcript_list
    # you can also directly filter for the language you are
    # looking for, using the transcript list
    for transcript in transcript_list: # find_transcript(languages):
        print(f'!!transcript')
        print(f'!!  transcript {transcript}')
        print(f'!!  language_code = {transcript.language_code}')
        language_code = transcript.language_code.split('-')[0] # we don't consider the variant (en-US => en)
        while language_code in transcripts_dict:
            print(f'!!  language_code {language_code} already in transcripts_dict')
            language_code += "_" # to avoid duplicate keys
            continue
        transcripts_dict[language_code] = transcript

        if keep_all_manual_transcripts or language_code in languages:
            properties = Transcript_properties(transcript)
            properties['is_translated'] = False
            tr = { 'properties':properties }
            tr['data'] = transcript.fetch() # ex: [{'text': 'imaginez ceci, une machine qui pourrait', 'start': 0.4, 'duration': 4.72}, ...]
            tr['data_size'] = len(tr['data'])
            tr['text'] = " ".join([x['text'] for x in tr['data']])
            Transcript_fix_Text_and_stats(tr)
            transcripts[language_code] = tr          

        if use_cache:
            text = json.dumps(transcripts[language_code], indent=4)
            Cache_Store(PUBLIC_USER_ID, 'transcripts', text, f'YT~{video_id}~{language_code}.json')
    
    print(f'!!transcripts (2) ={transcripts}')
        
    if False:
        # translating the transcript will return another
        # transcript object
        print(transcript.translate('en').fetch())


    for language_code in languages:
        if transcript_list and language_code not in transcripts:
            transcript = list(transcripts_dict.values())[0] # we will translate the first transcript
            # transcript_list.find_generated_transcript([lg])
            if transcript:
                print(f'!! translate transcript to "{language_code}" from "{language_code}"')
                # translating the transcript will return another
                # transcript object
                tr2 = transcript.translate(language_code)
                print(tr2)
                properties = Transcript_properties(tr2)
                properties['is_translated'] = True
                tr = { 'properties': properties }
                tr['data'] = tr2.fetch()
                tr['data_size'] = len(tr['data'])
                tr['text'] = " ".join([x['text'] for x in tr['data']])
                Transcript_fix_Text_and_stats(tr)
                transcripts[language_code] = tr

                # or just filter for manually created transcripts
                # transcript = transcript_list.find_manually_created_transcript(['en'])

                if use_cache:
                    text = json.dumps(transcripts[language_code], indent=4)
                    Cache_Store(PUBLIC_USER_ID, 'transcripts', text, f'YT~{video_id}~{language_code}.json')

    return transcripts


class YoutubeTranscripts_BrainzTools(BuiltinTool):

    def get_params(self, user_id: str, video_ids: str, language: str, tool_parameters: dict) -> dict[str, str]:
        languages = language.replace(' ',',').replace(',,',',').split(',') if language else ["en"]
        language_xlate = { 'english':'en', 'french':'fr', 'spanish':'sp',}
        languages = [ language_xlate.get(lg.lower(), lg) for lg in languages]
        video_ids = Youtube_parse_video_ids(video_ids, with_info=False) or []
        return {
            "engine": "youtube_transcripts_brz",
            "video_id": video_ids[0] if video_ids else "",
            "languages": languages,
            "use_cache": tool_parameters.get('use_cache', True),
        }

    def results(self, user_id: str, video_ids: str, language: str, tool_parameters: dict) -> dict:
        params = self.get_params(user_id, video_ids, language, tool_parameters)

        video_id = params['video_id']
        transcripts = Youtube_get_transcripts(user_id, video_id, languages=params['languages'], use_cache=params['use_cache'])
        results = [ self.create_json_message(obj) for obj in transcripts.values() ]
        params['results_nbr'] = len(results)
        params['lg_index'] = { lg: i for i, lg in enumerate(transcripts.keys())}
        return results, params

    def _invoke(self,
                user_id: str,
                tool_parameters: dict[str, Any],
        ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:

        video_ids = tool_parameters['video_id']
        language = tool_parameters.get('language', "en")

        results, meta = self.results(user_id, video_ids, language, tool_parameters)
        return results, meta
    
