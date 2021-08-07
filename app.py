import time
from absl import app, logging
import cv2
import numpy as np
import tensorflow as tf
from yolov3_tf2.models import (
    YoloV3, YoloV3Tiny
)
from yolov3_tf2.dataset import transform_images, load_tfrecord_dataset
from yolov3_tf2.utils import draw_outputs
from flask import Flask, request, Response, jsonify, send_from_directory, abort
import os
import requests
import json

# customize your API through the following parameters
classes_path = './data/labels/coco.names'
weights_path = './weights/yolov3.tf'
tiny = False                    # set to True if using a Yolov3 Tiny model
size = 416                      # size images are resized to for model
output_path = './detections/'   # path to output folder where images with detections are saved
num_classes = 80                # number of classes in model

# load in weights and classes
physical_devices = tf.config.experimental.list_physical_devices('GPU')
if len(physical_devices) > 0:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)

if tiny:
    yolo = YoloV3Tiny(classes=num_classes)
else:
    yolo = YoloV3(classes=num_classes)

yolo.load_weights(weights_path).expect_partial()
print('weights loaded')

class_names = [c.strip() for c in open(classes_path).readlines()]
print('classes loaded')

# Initialize Flask application
app = Flask(__name__)


# API that returns JSON with classes found in images
@app.route('/detections/by-image-files', methods=['POST'])
def get_detections_by_image_files():
    raw_images = []
    images = request.files.getlist("images")
    image_names = []
    for image in images:
        image_name = image.filename
        image_names.append(image_name)
        image.save(os.path.join(os.getcwd(), image_name))
        img_raw = None
        try:
            img_raw = tf.image.decode_image(
                open(image_name, 'rb').read(), channels=3)
        except tf.errors.InvalidArgumentError:
            abort(404, "it is not an image file or image file is an unsupported format. try jpg or png")
        except Exception as e:
            print(e.__class__)
            print(e)
            abort(500)
        raw_images.append(img_raw)
        
    num = 0
    
    # create list for final response
    response = []

    for j in range(len(raw_images)):
        # create list of responses for current image
        responses = []
        raw_img = raw_images[j]
        num += 1
        img = tf.expand_dims(raw_img, 0)
        img = transform_images(img, size)

        t1 = time.time()
        boxes, scores, classes, nums = yolo(img)
        t2 = time.time()
        print('time: {}'.format(t2 - t1))

        print('detections:')
        for i in range(nums[0]):
            print('\t{}, {}, {}'.format(class_names[int(classes[0][i])],
                                            np.array(scores[0][i]),
                                            np.array(boxes[0][i])))
            responses.append({
                "class": class_names[int(classes[0][i])],
                "confidence": float("{0:.2f}".format(np.array(scores[0][i])*100)),
                "box": np.array(boxes[0][i]).tolist()
            })
        response.append({
            "image": image_names[j],
            "detections": responses
        })
        img = cv2.cvtColor(raw_img.numpy(), cv2.COLOR_RGB2BGR)
        img = draw_outputs(img, (boxes, scores, classes, nums), class_names)
        cv2.imwrite(output_path + 'detection' + str(num) + '.jpg', img)
        print('output saved to: {}'.format(output_path + 'detection' + str(num) + '.jpg'))

    # remove temporary images
    for name in image_names:
        os.remove(name)
    try:
        return Response(response=json.dumps({"response": response}), mimetype="application/json")
    except FileNotFoundError:
        abort(404)


# API that returns image with detections on it
@app.route('/image/by-image-file', methods= ['POST'])
def get_image_by_image_file():
    image = request.files["images"]
    image_name = image.filename
    image.save(os.path.join(os.getcwd(), image_name))
    img_raw = None
    try:
        img_raw = tf.image.decode_image(
            open(image_name, 'rb').read(), channels=3)
    except tf.errors.InvalidArgumentError:
        abort(404, "it is not an image file or image file is an unsupported format. try jpg or png")
    except Exception as e:
        print(e.__class__)
        print(e)
        abort(500)
    img = tf.expand_dims(img_raw, 0)
    img = transform_images(img, size)

    t1 = time.time()
    boxes, scores, classes, nums = yolo(img)
    t2 = time.time()
    print('time: {}'.format(t2 - t1))

    print('detections:')
    for i in range(nums[0]):
        print('\t{}, {}, {}'.format(class_names[int(classes[0][i])],
                                        np.array(scores[0][i]),
                                        np.array(boxes[0][i])))
    img = cv2.cvtColor(img_raw.numpy(), cv2.COLOR_RGB2BGR)
    img = draw_outputs(img, (boxes, scores, classes, nums), class_names)
    cv2.imwrite(output_path + 'detection.jpg', img)
    print('output saved to: {}'.format(output_path + 'detection.jpg'))
    
    # prepare image for response
    _, img_encoded = cv2.imencode('.png', img)
    response = img_encoded.tostring()
    
    # remove temporary image
    os.remove(image_name)

    try:
        return Response(response=response, status=200, mimetype='image/png')
    except FileNotFoundError:
        abort(404)


# API that returns JSON with classes found in images from url list
@app.route('/detections/by-url-list', methods=['POST'])
def get_detections_by_url_list():
    raw_images = []
    image_urls = request.get_json()["images"]
    if not isinstance(image_urls, list):
        abort(400, "can't find image list")
    image_names = []
    custom_headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    }
    for i, image_url in enumerate(image_urls):
        image_name = "Image" + str(i + 1)
        image_names.append(image_name)
        img_raw = None
        try:
            img_raw = tf.image.decode_image(
                requests.get(image_url, headers=custom_headers).content, channels=3)
        except tf.errors.InvalidArgumentError:
            abort(404, "it is not image url or that image is an unsupported format. try jpg or png")
        except requests.exceptions.MissingSchema:
            abort(400, "it is not url form")
        except Exception as e:
            print(e.__class__)
            print(e)
            abort(500)
        raw_images.append(img_raw)

    num = 0
        
    # create list for final response
    response = []

    for j in range(len(raw_images)):
        # create list of responses for current image
        responses = []
        raw_img = raw_images[j]
        num += 1
        img = tf.expand_dims(raw_img, 0)
        img = transform_images(img, size)

        t1 = time.time()
        boxes, scores, classes, nums = yolo(img)
        t2 = time.time()
        print('time: {}'.format(t2 - t1))

        print('detections:')
        for i in range(nums[0]):
            print('\t{}, {}, {}'.format(class_names[int(classes[0][i])],
                                            np.array(scores[0][i]),
                                            np.array(boxes[0][i])))
            responses.append({
                "class": class_names[int(classes[0][i])],
                "confidence": float("{0:.2f}".format(np.array(scores[0][i])*100)),
                "box": np.array(boxes[0][i]).tolist()
            })
        response.append({
            "image": image_names[j],
            "detections": responses
        })
        img = cv2.cvtColor(raw_img.numpy(), cv2.COLOR_RGB2BGR)
        img = draw_outputs(img, (boxes, scores, classes, nums), class_names)
        cv2.imwrite(output_path + 'detection' + str(num) + '.jpg', img)
        print('output saved to: {}'.format(output_path + 'detection' + str(num) + '.jpg'))

    return Response(response=json.dumps({"response": response}), mimetype="application/json")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
