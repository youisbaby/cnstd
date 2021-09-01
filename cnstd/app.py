# coding: utf-8
# Copyright (C) 2021, [Breezedeus](https://github.com/breezedeus).
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from collections import OrderedDict

import numpy as np
from PIL import Image
import streamlit as st

from cnstd import CnStd
from cnstd.utils import plot_for_debugging, pil_to_numpy

try:
    from cnocr import CnOcr
    from cnocr.consts import AVAILABLE_MODELS
    cnocr_avalable = True
except ModuleNotFoundError:
    cnocr_avalable = False


@st.cache(allow_output_mutation=True)
def get_ocr_model(ocr_model_name):
    if not cnocr_avalable:
        return None
    return CnOcr(ocr_model_name)


@st.cache(allow_output_mutation=True)
def get_std_model(std_model_name):
    return CnStd(
        std_model_name,
    )


def visualize_std(img, std_out, box_score_thresh):
    img = pil_to_numpy(img).transpose((1, 2, 0)).astype(np.uint8)

    plot_for_debugging(
        img, std_out['detected_texts'], box_score_thresh, './streamlit-app'
    )
    st.subheader('STD Result')
    st.image('./streamlit-app-result.png')
    # st.image('./streamlit-app-crops.png')


def visualize_ocr(ocr, std_out):
    st.empty()
    st.subheader('OCR Result')
    ocr_res = OrderedDict({'文本': []})
    ocr_res['概率值'] = []
    for box_info in std_out['detected_texts']:
        cropped_img = box_info['cropped_img']  # 检测出的文本框
        ocr_out = ocr.ocr_for_single_line(cropped_img)
        ocr_res['概率值'].append(ocr_out[1])
        ocr_res['文本'].append(''.join(ocr_out[0]))
    st.table(ocr_res)


def main():
    st.sidebar.header('CnStd 设置')
    std_model_name = st.sidebar.selectbox('模型名称', ('db_resnet18', 'db_resnet34'))
    st.sidebar.subheader('resize 后图片大小')
    height = st.sidebar.select_slider('height', options=[384, 512, 768, 896, 1024], value=768)
    width = st.sidebar.select_slider('width', options=[384, 512, 768, 896, 1024], value=768)
    preserve_aspect_ratio = st.sidebar.checkbox('resize 时是否等比例缩放', value=True)
    st.sidebar.subheader('检测分数阈值')
    box_score_thresh = st.sidebar.slider('（低于阈值的结果会被过滤掉）', min_value=0.05, max_value=0.95, value=0.3)
    std = get_std_model(std_model_name)

    if cnocr_avalable:
        st.sidebar.markdown("""---""")
        st.sidebar.header('CnOcr 设置')
        ocr_model_name = st.sidebar.selectbox('模型名称', ('densenet-s-fc', 'densenet-s-gru'))
        ocr = get_ocr_model(ocr_model_name)

    st.subheader('选择待检测图片')
    content_file = st.file_uploader('', type=["png", "jpg", "jpeg"])
    if content_file is None:
        st.stop()

    try:
        img = Image.open(content_file)

        std_out = std.detect(
            img,
            resized_shape=(height, width),
            preserve_aspect_ratio=preserve_aspect_ratio,
            box_score_thresh=box_score_thresh,
        )
        visualize_std(img, std_out, box_score_thresh)

        if cnocr_avalable:
            visualize_ocr(ocr, std_out)
    except Exception as e:
        st.error(e)


if __name__ == '__main__':
    main()
