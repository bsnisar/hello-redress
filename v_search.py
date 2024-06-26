import requests
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

AUTH_TOKEN = st.secrets["AUTH_TOKEN"]


def v_search(image_url, product_description):
    headers = {
        'X-API-KEY-HEWI': AUTH_TOKEN,
        'Content-Type': 'application/json'
    }
    payload = {
      "topK": 10,
      "categories": [],
      "image_url": image_url,
      "product_description": product_description
    }
    response = requests.post('http://44.223.215.76:8005/hewi/v1/similar_images', json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()

    # Example usage
    image_urls = [
        doc['imageCutOutUrl']
        for doc in data
    ]
    image_names = [
        doc['name']
        for doc in data
    ]

    return image_urls, image_names 


num_columns = 3

ss_input = st.text_input('Url Search')
product_description = st.text_input('Product description')

if ss_input:
    urls, labels = v_search(ss_input, product_description)

    url_chunks = [urls[i:i + num_columns] for i in range(0, len(urls), num_columns)]
    url_labels = [labels[i:i + num_columns] for i in range(0, len(labels), num_columns)]

    # Render the grid of images
    for chunk_url, chunk_lable in zip(url_chunks, url_labels):
        cols = st.columns(num_columns)
        for col, image_url, label in zip(cols, chunk_url, chunk_lable):
            col.image(image_url, caption=label, use_column_width=True)
