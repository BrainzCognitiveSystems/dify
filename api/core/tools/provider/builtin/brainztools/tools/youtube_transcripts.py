from typing import Any, Union

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

# according to https://pypi.org/project/youtube-transcript-api/
def Youtube_get_transcripts(video_id, languages=["en", "fr"]):
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

    transcripts = { }
    print(f'!!transcripts (1) ={transcripts}')
    # return transcripts

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except Exception as e:
        print(f'!!transcript_list is missing ? (1a) {e}')
        return transcripts
    
    print(f'!!transcript_list (1b) {transcript_list}')

    transcripts_dict = {}
    # iterate over all available transcripts => transcript_list
    # you can also directly filter for the language you are
    # looking for, using the transcript list
    for transcript in transcript_list: # find_transcript(languages):
        print(f'!!transcript')
        print(f'!!  transcript {transcript}')
        print(f'!!  language_code = {transcript.language_code}')
        language_code = transcript.language_code
        transcripts_dict[language_code] = transcript

        if languages == "*" or language_code in languages:
            properties = Transcript_properties(transcript)
            tr = { 'properties':properties }
            tr['data'] = transcript.fetch() # ex: [{'text': 'imaginez ceci, une machine qui pourrait', 'start': 0.4, 'duration': 4.72}, ...]
            tr['data_size'] = len(tr['data'])
            tr['text'] = " ".join([x['text'] for x in tr['data']])
            tr['text_size'] = len(tr['text'])
            transcripts[language_code] = tr

        
    if False:
        # translating the transcript will return another
        # transcript object
        print(transcript.translate('en').fetch())


    for lg in languages:
        if transcript_list and lg not in transcripts:
            transcript = list(transcripts_dict.values())[0]
            # transcript_list.find_generated_transcript([lg])
            if transcript:
                print(f'!! translate transcript to "{lg}" from "{transcript.language_code}"')
                # translating the transcript will return another
                # transcript object
                tr2 = transcript.translate(lg)
                print(tr2)
                properties = Transcript_properties(tr2)
                properties['is_translated'] = True
                tr = { 'properties': properties }
                tr['data'] = tr2.fetch()
                tr['data_size'] = len(tr['data'])
                tr['text'] = " ".join([x['text'] for x in tr['data']])
                tr['text_size'] = len(tr['text'])
                transcripts[lg] = tr

                # or just filter for manually created transcripts
                # transcript = transcript_list.find_manually_created_transcript(['en'])

    return transcripts


class YoutubeTranscripts_BrainzTools(BuiltinTool):

    def get_params(self, video_id: str, language: str, **kwargs: Any) -> dict[str, str]:
        languages = language.split(',') if language else ["en"]
        return {
            "engine": "youtube_transcripts_brz",
            "video_id": video_id,
            "languages": languages,
            **{key: value for key, value in kwargs.items() if value not in [None, ""]},
        }

    def results(self, video_id: str, language: str, **kwargs: Any) -> dict:
        params = self.get_params(video_id, language, **kwargs)
        transcripts = Youtube_get_transcripts(video_id, languages=params['languages'])
        results = [ self.create_json_message(obj) for obj in transcripts.values() ]
        params['results_nbr'] = len(results)
        params['lg_index'] = { lg: i for i, lg in enumerate(transcripts.keys())}
        return results, params

    def _invoke(self,
                user_id: str,
                tool_parameters: dict[str, Any],
        ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:

        video_id = tool_parameters['video_id']
        language = tool_parameters.get('language', "en")

        results, meta = self.results(video_id, language)
        return results, meta
    
