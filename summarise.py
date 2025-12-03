from groq import Groq
import os
import render

key = os.environ.get("GroqApi")
client = Groq(api_key=key)
model = "meta-llama/llama-4-scout-17b-16e-instruct"

def pagesummarise(doc,page,conts):
    imgcont = imgText(doc,page)
    prompt = ("Summarise the following PDF page.\n\n"
    "TEXT CONTENT:\n" + conts + "\n\n"
     + "\n\n"
    +"Image description:\n" + imgcont + "\n\n"+"Give a compact,detailed, easy to understand summary with definitions.")

    resp = client.chat.completions.create(
    model = model,
    messages =[{'role':'user','content':prompt}]
    )
    response = resp.choices[0].message.content
    return response

def imgText(doc,page):
    img = render.exportImg(doc,page)
    prompt = "provide detailed description of the given page"
    resp = client.chat.completions.create(
        model=model,
        messages=[{
            "role":"user",
            "content": [
                {"type": "text",
                 "text":prompt},{
                "type":"image_url",
                "image_url":{"url":f"data:image/png;base64,{img}"},
                 },
            ],
        }]

    )
    response = resp.choices[0].message.content
    return response

