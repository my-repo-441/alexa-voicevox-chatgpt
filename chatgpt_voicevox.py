
import requests, json
import io
import wave
import time
from pathlib import Path
import boto3
import tempfile
import subprocess

class Voicevox:
    # hostにはVOICEVOXを起動しているEC2のプライベートアドレスを入れる。
    def __init__(self,host="100.24.0.11",port=50021):
        self.host = host
        self.port = port

    def speak(self,text=None,speaker=47, speed=1.4): 

        params = (
            ("text", text),
            ("speaker", speaker)  # 音声の種類をInt型で指定
        )

        init_q = requests.post(
            f"http://{self.host}:{self.port}/audio_query",
            params=params
        )

        res = requests.post(
            f"http://{self.host}:{self.port}/synthesis",
            headers={"Content-Type": "application/json"},
            params=params,
            data=json.dumps(init_q.json())
        )
        
        # Create temporary files for processing
        temp_input_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_input_file.write(res.content)
        temp_input_file.close()
    
        temp_output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")

        # Run ffmpeg to change bitrate
        #subprocess.call(['ffmpeg', '-y','-i', temp_input_file.name, '-b:a', '48k', temp_output_file.name])
        subprocess.call(['ffmpeg', '-y', '-i', temp_input_file.name, '-b:a', '48k', '-ar', '16000', temp_output_file.name])

        # Open the new file and load into BytesIO
        with open(temp_output_file.name, 'rb') as f:
          audio = io.BytesIO(f.read())

        # メモリ上で展開
        #audio = io.BytesIO(res.content)

        s3 = boto3.client('s3', region_name='us-east-1')
        
        bucket_name = 'bucket-voicevox'
        object_name = 'voice_output.mp3'
        s3.upload_fileobj(audio, bucket_name, object_name)


        response = s3.generate_presigned_url('get_object',
                Params={'Bucket': bucket_name,'Key': object_name},
                ExpiresIn=3600)
                    
        return response

def main():
    vv = Voicevox()
    vv.speak(text='こんにちは')


if __name__ == "__main__":
    main()

