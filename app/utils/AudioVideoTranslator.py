from pyAudioAnalysis import audioSegmentation as aS
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, concatenate_audioclips
import requests

import time
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set log level if needed

class AudioVideoTranslator:
    def __init__(self, video_path):
        self.video_path = video_path
       # self.audio_path = "../downloads/temp_audio.wav"
       # self.video = VideoFileClip(video_path)
       # self.video.audio.write_audiofile(self.audio_path)
        self.segments = []

    def count_speakers(self):
        try:
            # Assuming speaker_diarization requires only the file path and the number of speakers.
            # This is a placeholder; you may need to adjust arguments according to the actual API.
            segments, speaker_labels = aS.speaker_diarization(self.audio_path, numOfSpeakers=2)
            num_speakers = len(set(speaker_labels))
            logger.info(f"Estimated number of unique speakers: {num_speakers}")
            return num_speakers
        except Exception as e:
            logger.info(f"An error occurred during speaker diarization: {e}")


    def adjust_audio_duration_and_translate(self, target_language):
        for i, (start, end, _) in enumerate(self.segments):
            start_ms = start * 1000
            end_ms = end * 1000
            audio_chunk = AudioSegment.from_file(self.audio_path)[start_ms:end_ms]
            
            # Assuming you implement a function to handle speech-to-text, translation, and text-to-speech,
            # which outputs the translated audio file path.
            translated_audio_path = self.translate_audio_chunk(audio_chunk, target_language)
            
            # Update segment with translated audio path
            self.segments[i] = (start, end, translated_audio_path)

    def translate_audio_chunk(self, audio_chunk, target_language):
        # This method should implement speech-to-text, call translate_text_with_ollama for translation,
        # and then use text-to-speech to generate the translated audio, returning the path to the audio file.
        pass

 

    def combine_audio_with_video(self):
        audio_clips = []
        for start, end, path in self.segments:
            if path:  # Ensure there's a translated path
                audio_clip = AudioFileClip(path).set_start(start)
                audio_clips.append(audio_clip)
        final_audio = concatenate_audioclips(audio_clips)
        
        final_video = self.video.set_audio(final_audio)
        final_video.write_videofile("translated_video.mp4", codec="libx264", audio_codec="aac")

# Example usage
if __name__ == "__main__":
    translator = AudioVideoTranslator("../downloads/Истинный Смысл Матрицы. Наука, Религия и Философия в Матрице.mp4")
    # translate text remove it after testing:
    result = translator.translate_text_with_ollama("Лишь довольно малое количество людей знают о том, что огромное количество кинематографических проектов брало за основу смыслы, истории, повествования и пророчества из различных религиозных традиций или, ушедших в прошлое, древних мифов. Не каждый догадывается что история из первого 'Терминатора' это переработанная древнегреческая легенда о Минотавре. Или то что за основу кодекса чести рыцарей - джедаев взят реально существовавший кодекс чести японских самураев, следовавших духовной традиции синтоизма. И, в этой статье, я собираюсь Вам поведать о религиозных смыслах ставшего уже классическим замечательного фильма 'Матрица' от уже бывших братьев Вачовски с Киану Ривзом и Лоуренсом Фишберном в главных ролях."+

"Для начала, давайте разберёмся с понятием 'матрица', при чём здесь вообще религия и почему создатели фильма взяли в качестве наименования проекта именно это слово."+

"Матрица имеет много значений. Она есть в искусстве, астрономии, физике, математике, программировании и, даже, в экономике. В искусстве это образец, модель, штамп, то что взято за основу первого творческого порыва художника. В физике матрица это конденсированная среда, в которую помещаются изолированные активные частицы, с целью предотвращения взаимодействия между собой и окружающей средой. В математике это прямоугольная таблица элементов некоторого кольца или поля. В программировании - двумерный массив. В экономике, по аналогии с математикой, это, опять же, таблицы. Но что объединяет эти разные, по значению, матрицы? Искусственно созданный мир. Пространство, на которое художник изливает свои фантазии и видение мира, баланс между различными частицами, блуждающими внутри этого искусственного мира, или таблица, имитирующая то что происходит в реальном мире и объясняющая принципы действия всех материальных вещей вокруг нас. Эти все разные принципы существуют в нашей жизни, окружают нас, и всё это было названо словом мир. словом вселенная. Ведь всё это так же временно как и любая матрица, а значит имеет и другую сторону медали, реальную и живую, подобно двумерной матрице в программировании. "  +

"Пифия " + 
"И, даже, не смотря на то что прорицательница Пифия, в исполнении Глории Фостер, в середине фильма определила что Нео вовсе не избранный, то, всё равно достаточно веры и сосредоточения на свете, исходящем изнутри. Ведь одно утверждение в этом мире, может иметь иной смысл в истинной реальности.", "English")
    print(f"Translated : {result}")
    result = translator.count_speakers()
    print(f"Speakers counted : {result}")
    #translator.adjust_audio_duration_and_translate("French")
    #translator.combine_audio_with_video()