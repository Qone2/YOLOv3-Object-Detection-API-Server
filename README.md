# real-matzip-backend-detection-api-server
리얼맛집 프로젝트에서 detection api 서버 기능을 담당하는 프로젝트.  
사진을 올리면 디텍션 결과를 json형태로 반환.  
YOLOv3와 Flask로 구성되어 있습니다.

## 1. Install
### Conda
가급적이면 conda환경을 구성해서 하는걸 추천합니다.
```shell
# Tensorflow CPU
conda env create -f conda-cpu.yml
conda activate yolov3-cpu

# Tensorflow GPU
conda env create -f conda-gpu.yml
conda activate yolov3-gpu
```

### Weights
가중치 파일은 일단은 coco dataset 으로 미리 학습된 모델을 받습니다.  
나중에 커스텀 모델도 올릴 예정입니다.  
```shell
wget https://pjreddie.com/media/files/yolov3.weights -O weights/yolov3.weights
```

### Convert
가중치 파일을 텐서플로 모델로 변환하여 저장합니다.
```shell
python load_weights.py
```

### Run
flask 서버 실행.
```shell
python app.py
```

## 2. Usage
### Detections by url list (POST http://localhost:5000/detections/by-url-list)
이미지 url 리스트를 json 형태로 body 에 담아 요청하면 detection 결과를 json 형태로 반환합니다.

요청 예시:
```json
{
    "images" : [
        "https://scontent-ssn1-1.cdninstagram.com/v/t51.2885-15/e35/219194203_4048726531863394_2564241120347390836_n.jpg?_nc_ht=scontent-ssn1-1.cdninstagram.com&_nc_cat=110&_nc_ohc=ozDT8pvlE1QAX9G0pPH&edm=AP_V10EBAAAA&ccb=7-4&oh=b6b5d2c2a7649896c7576e3a82ed5930&oe=60FE346B&_nc_sid=4f375e",
        "https://scontent-ssn1-1.cdninstagram.com/v/t51.2885-15/e35/s1080x1080/219798075_800281433987925_562346442929147322_n.jpg?_nc_ht=scontent-ssn1-1.cdninstagram.com&_nc_cat=1&_nc_ohc=zV6m3407S4UAX-D0Q0N&edm=AP_V10EBAAAA&ccb=7-4&oh=4aa5f11088554cbb058eeb1778510415&oe=60FD7652&_nc_sid=4f375e"
        ]
}
```

응답 예시:
```json
{
    "response": [
        {
            "detections": [
                {
                    "class": "dog",
                    "confidence": 99.93
                },
                {
                    "class": "teddy bear",
                    "confidence": 99.78
                },
                {
                    "class": "laptop",
                    "confidence": 96.11
                },
                {
                    "class": "chair",
                    "confidence": 87.97
                },
                {
                    "class": "cup",
                    "confidence": 59.49
                }
            ],
            "image": "Image1"
        },
        {
            "detections": [
                {
                    "class": "teddy bear",
                    "confidence": 97.35
                }
            ],
            "image": "Image2"
        }
    ]
}
```
url 의 image 포맷이 jpg나 png 이어야 합니다. 

<br/>

### Detections by image files (POST http://localhost:5000/detections/by-image-files)
1개 이상의 이미지 파일을 multipart/form-data 형식으로 body에 담아서 보내야 합니다.  
key 값은 "images"로 주어야 합니다.

postman 서비스를 이용하면 요청을 테스트 하기도 쉽고, 각 언어에 맞는 코드로 알려주기도 합니다.

요청 예시 (python.requests):
```python
import requests

url = "http://127.0.0.1:5000/detections"

payload={}
files=[
  ('images',('dog.jpg',open('/C:/Users/Qone/real-matzip-backend-detection-api-server/data/images/dog.jpg','rb'),'image/jpeg')),
  ('images',('meme.jpg',open('/C:/Users/Qone/real-matzip-backend-detection-api-server/data/images/meme.jpg','rb'),'image/jpeg'))
]
headers = {}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
```
응답 예시:
```json
{
    "response": [
        {
            "detections": [
                {
                    "class": "dog",
                    "confidence": 99.77
                },
                {
                    "class": "bicycle",
                    "confidence": 99.02
                },
                {
                    "class": "truck",
                    "confidence": 93.78
                }
            ],
            "image": "dog.jpg"
        },
        {
            "detections": [
                {
                    "class": "cup",
                    "confidence": 99.81
                },
                {
                    "class": "person",
                    "confidence": 99.77
                },
                {
                    "class": "laptop",
                    "confidence": 98.46
                },
                {
                    "class": "apple",
                    "confidence": 90.83
                },
                {
                    "class": "chair",
                    "confidence": 77.85
                },
                {
                    "class": "cell phone",
                    "confidence": 73.47
                },
                {
                    "class": "clock",
                    "confidence": 67.04
                }
            ],
            "image": "meme.jpg"
        }
    ]
}
```
<br/>

### Image by image file (POST http://localhost:5000/image/by-image-file)
1개의 이미지파일을 multipart/form-data 형식으로 body에 담아서 보내야합니다.  
key 값은 "images"로 주어야 합니다.

postman 서비스를 이용하면 요청을 테스트 하기도 쉽고, 각 언어에 맞는 코드로 알려주기도 합니다.

요청 예시(node.js axios):
```javascript
var axios = require('axios');
var FormData = require('form-data');
var fs = require('fs');
var data = new FormData();
data.append('images', fs.createReadStream('/C:/Users/Qone/Downloads/real-matzip-backend-detection-api-server/data/images/dog.jpg'));

var config = {
  method: 'post',
  url: 'http://localhost:5000/image',
  headers: { 
    ...data.getHeaders()
  },
  data : data
};

axios(config)
.then(function (response) {
  console.log(JSON.stringify(response.data));
})
.catch(function (error) {
  console.log(error);
});
```

응답 예시:
![response](detections/detection.jpg)

<br/>

## Reference
이곳에서 영향을 많이 받았고, 필요에 맞게 수정하였습니다.
* https://github.com/theAIGuysCode/Object-Detection-API
