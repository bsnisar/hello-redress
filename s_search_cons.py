import requests
import base64
import json
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import textwrap
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage

AUTH_TOKEN = st.secrets["AUTH_TOKEN"]
OPENAPI_API_KEY = st.secrets["OPENAPI_API_KEY"]



def image_to_data_url(uploaded_file):
    encoded_string = base64.b64encode(uploaded_file.read()).decode('utf-8')    
    file_extension = uploaded_file.name.split('.')[-1].lower()
    mime_type = f"image/{file_extension}"    
    data_url = f"data:{mime_type};base64,{encoded_string}"
    
    return data_url


def s_search(text, top_n=10):
    headers = {
        'X-API-KEY-HEWI': AUTH_TOKEN,
        'Content-Type': 'application/json'
    }
    payload = {
      "topK": top_n,
      "query": text,
      "classify_category": False
    } 
    response = requests.post('http://44.223.215.76:8005/hewi/semantic_search', json=payload, headers=headers)
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
    return zip(image_urls, image_names)


def web_search(context, image):
    llm = ChatOpenAI(
        temperature=0, 
        model="gpt-4o", 
        api_key=OPENAPI_API_KEY)

    basicWebSearchResponsePrompt = textwrap.dedent("""
    You are REDRESS, an AI model who is expert at analyzing images and tailoring follow-up questions to better understand and meet the user's needs.
    Your task is to analyze the provided image of clothes and generate follow-up questions that can help make the user's request more specific and tailored. If no follow-up questions are needed, simply return empty json object.
    Generate follow-up questions that are informative and relevant to the user's context. Use an unbiased and journalistic tone in your responses. Do not repeat the text.
    Your questions should aim to gather more details about the user's preferences, requirements, and the context of their query. Provide options for each question to make it easier for the user to respond. Make sure the questions are clear and specific to the user's needs.
    Return the questions as a JSON array with each question containing text and options, like this:
    ```json
    [
        {{
            "question": "Could you specify the occasion for which you need this outfit?",
            "options": ["Casual", "Formal", "Party", "Work", "Other"]
        }},
        {{
            "question": "Are there any particular colors or styles you prefer or dislike?",
            "options": ["Yes, specify colors/styles", "ANY"]
        }},
        {{
            "question": "Do you have a preference for any specific material or fabric?",
            "options": ["Cotton", "Wool", "Silk", "Synthetic", "ANY"]
        }},
        {{
            "question": "Would you like suggestions for accessories to match this outfit?",
            "options": ["Yes", "No"]
        }}
    ]
    ```

    Anything inside the following `context` HTML block provided below is for your knowledge and not shared by the user. You have to generate questions on the basis of this context but you do not have to talk about the context in your response.

    <context>
    {context}
    </context>

    If you think no follow-up questions are needed based on the image, you can simply return empty JSON object "{{}}".
    """)

    prompt = ChatPromptTemplate.from_messages(    [
        (
            "user",
            [
                {
                    "text": basicWebSearchResponsePrompt,
                },
                {
                    "image_url": {
                        "url": "{imageURL}",
                        "detail": "high",
                    }
                },
            ],
        ),
    ])
    
    chain = prompt | llm | SimpleJsonOutputParser()

    result = chain.invoke({
        "context": context,
        "imageURL": image
    })

    return result




def mk_requests(context):
    llm = ChatOpenAI(
        temperature=0, 
        model="gpt-3.5-turbo", 
        api_key=OPENAPI_API_KEY)

    basicWebSearchResponsePrompt = textwrap.dedent("""
    You are Redress, an AI model specialized in generating precise search queries for marketplaces to help users find specific items based on their needs and preferences.

    Your task is to create detailed and relevant search queries that can be used on various marketplaces to find items based on the user's context. The context represents answers to follow-up questions regarding their preferences and requirements for the items they are looking for.
    Generate search queries that are specific and tailored to the user's context. Use an unbiased and journalistic tone in your responses. Do not repeat the text.
    Ensure that the search queries include relevant keywords, attributes, and specifications based on the user's input. Make sure the search queries are clear and specific to the user's needs.

    Return the search queries as a JSON array, where each query is a string.
    Anything inside the following `context` HTML block provided below is for your knowledge and not shared by the user. You have to generate search queries based on this context.

    <context>
    {context}
    </context>

    If you think there's not enough information to generate a relevant search query, you can return 'None'.

    Example:
    ```json
    [
        "red floral dress size M",
        "men's black leather jacket XL",
        "women's running shoes size 8"
    ]
    ```
    """)

    prompt = ChatPromptTemplate.from_messages(    [
        (
            "user",
            [
                {
                    "text": basicWebSearchResponsePrompt,
                },
            ],
        ),
    ])
    
    chain = prompt | llm | SimpleJsonOutputParser()

    result = chain.invoke({
        "context": context
    })

    return result

num_columns = 3
def render(pairs):
    pairs_list = list(set(pairs))
    pairs_chunks = [pairs_list[i:i + num_columns] for i in range(0, len(pairs_list), num_columns)]

    for chunk in pairs_chunks:
        cols = st.columns(num_columns)
        for col, item in zip(cols, chunk):

            image_url = item[0]
            label = item[1]

            col.image(image_url, caption=label, use_column_width=True)



ss_q_input = st.text_input("Query", key="q")
ss_media_file = st.file_uploader("Choose a file", key="img")


if ss_media_file and ss_q_input:

    if 'web_search' not in st.session_state:
        response = web_search(ss_q_input, image_to_data_url(ss_media_file))
        st.session_state['web_search'] = response
    else :
        response = st.session_state['web_search']

    if response:
        st.subheader('Follow up questions')
        for opts in response:
            key = opts['question']
            val = opts['options']
            key_opt = st.radio(str(key), list(val), key=f"ss__{key}")

    if st.button("Find"):
        keys = set(st.session_state)
        context = {}
        for k in keys:
            if str(k).startswith('ss__'):
                context[str(k)[len('ss__'):]] = st.session_state[k]
                del st.session_state[k]

        queries_list = mk_requests(context)
        queries_response = []
        for q in queries_list:
            items = s_search(q, top_n=10)
            queries_response.extend(items)

        render(queries_response)

