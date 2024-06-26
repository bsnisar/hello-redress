import requests
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

AUTH_TOKEN = st.secrets["AUTH_TOKEN"]


def v_search(prod_txt, negative_txt, image_url, top_n=10):
    headers = {
        'X-API-KEY-HEWI': AUTH_TOKEN,
        'Content-Type': 'application/json'
    }
    payload = {
      "topK": top_n,
      "categories": [],
      "image_url": image_url,
      "product_description": prod_txt,
      "negative_description": negative_txt
    }    
    response = requests.post('http://44.223.215.76:8005/hewi/v1/similar_images_consumer', json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    image_urls = [
        doc['imageCutOutUrl']
        for doc in data
    ]
    image_names = [
        doc['name']
        for doc in data
    ]
    return  image_urls, image_names 


num_columns = 3

ss_input = st.text_input('Url Search')
if ss_input:
    urls, labels = v_search(ss_input)

    url_chunks = [urls[i:i + num_columns] for i in range(0, len(urls), num_columns)]
    url_labels = [labels[i:i + num_columns] for i in range(0, len(labels), num_columns)]

    # Render the grid of images
    for chunk_url, chunk_lable in zip(url_chunks, url_labels):
        cols = st.columns(num_columns)
        for col, image_url, label in zip(cols, chunk_url, chunk_lable):
            col.image(image_url, caption=label, use_column_width=True)
