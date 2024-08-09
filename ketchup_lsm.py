import os
import json
import textwrap
import random
import streamlit as st
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

client = OpenAI(api_key="OPENAI_API")
base_dir = 'Character'
background_dir = 'background'
speech_bubble_dir = 'speechBubble'

with open('all_char.txt', 'r', encoding='utf-8') as f:
    data = json.loads(f.read())

ch_names = []
for category in data:
    for item in category:
        ch_names.append(item['ch_name'])

background_files = []
for filename in os.listdir(background_dir):
    if filename.endswith('.jpg') or filename.endswith('.png'):
        background_files.append(filename)

def find_most_similar_ch_name_and_background(prompt, ch_names, background_files, job, gender):
    wrapped_prompt = '\n'.join(textwrap.wrap(prompt, width=50))
    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
           {
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON."
            },
            {
                "role": "user",
                "content": (
                    f"Given the list of character names: {', '.join(ch_names)}, and background files: {', '.join(background_files)}, "
                    f"find the character name and background that would most likely match the phrase '{wrapped_prompt}'. The character is working as a {job}. "
                    "You must choose the character name and background from the provided lists only. "
                    "Please provide the result as a concise JSON object with the following format:\n"
                    "{\n"
                    "    \"ch_name\": \"character_name\",\n"
                    "    \"background\": \"background_file\"\n"
                    "}"
                )
            }
        ],
        temperature=0,
        max_tokens=100
    )
    result = chat_completion.choices[0].message.content.strip()
    
    # 디버깅을 위해 응답 내용을 출력
    print(f"OpenAI Response: {result}")
    
    try:
        result_json = json.loads(result)
        if gender == "female":
            result_json['ch_name'] = result_json['ch_name'].replace("(m)", "(w)")

    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON response: {e}")
        return None
    
    return result_json

def find_image_file(ch_name):
    file_name = f"{ch_name}.png"
    file_path = os.path.join(base_dir, file_name)
    
    # 파일 경로 디버깅 출력
    print(f"Looking for character image file: {file_path}")
    
    if os.path.exists(file_path):
        return file_path
    else:
        return None

def find_background_image_file(background_name):
    file_path = os.path.join(background_dir, background_name)
    
    # 파일 경로 디버깅 출력
    print(f"Looking for background image file: {file_path}")
    
    if os.path.exists(file_path):
        return file_path
    else:
        print("Background not found, selecting a random background")
        return os.path.join(background_dir, random.choice(background_files))

def get_random_speech_bubble_image():
    speech_bubble_files = [f for f in os.listdir(speech_bubble_dir) if os.path.isfile(os.path.join(speech_bubble_dir, f))]
    if speech_bubble_files:
        return os.path.join(speech_bubble_dir, random.choice(speech_bubble_files))
    else:
        return None

def add_text_to_speech_bubble(image, text):
    draw = ImageDraw.Draw(image)
    font_path = "C:/Windows/Fonts/malgun.ttf" 
    font = ImageFont.truetype(font_path, 20)
    wrapped_text = '\n'.join(textwrap.wrap(text, width=15))  # 텍스트 줄바꿈
    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bubble_width, bubble_height = image.size
    text_x = (bubble_width - text_width) / 2
    text_y = (bubble_height - text_height) / 2
    draw.text((text_x, text_y), wrapped_text, fill="black", font=font)
    return image

st.set_page_config(page_title="Character Image Finder", page_icon="🔍")
st.title("🦜🔎 KetchUp")
st.write("대사에 맞는 캐릭터를 찾아보세요.")

st.sidebar.header("User Input")
job = st.sidebar.selectbox("직업 선택:", ["None", "adult", "child", "doctor", "jobless", "officeworker", "police", "senior", "singer", "student", "teacher"])
gender = st.sidebar.selectbox("성별 선택:", ["None", "male", "female"])

prompt = st.text_input("대사를 입력해주세요:")

if st.button("Find Character"):
    if prompt and job and gender:
        result_json = find_most_similar_ch_name_and_background(prompt, ch_names, background_files, job, gender)
        
        if result_json:
            most_similar_ch_name = result_json.get('ch_name')
            background_name = result_json.get('background')

            if most_similar_ch_name and background_name:
                st.write(f"Most similar character name: **{most_similar_ch_name}**")
                st.write(f"Background: **{background_name}**")

                image_file = find_image_file(most_similar_ch_name)
                background_image_file = find_background_image_file(background_name)
                speech_bubble_image_file = get_random_speech_bubble_image()

                if image_file and background_image_file and speech_bubble_image_file:
                    char_image = Image.open(image_file).convert("RGBA")
                    background_image = Image.open(background_image_file).convert("RGBA")
                    speech_bubble_image = Image.open(speech_bubble_image_file).convert("RGBA")
                    
                    # 배경 이미지를 고정 크기로 조정
                    bg_width, bg_height = 800, 600
                    background_image = background_image.resize((bg_width, bg_height))

                    # 캐릭터 이미지를 배경에 맞게 조정
                    char_width = bg_width // 4  # 캐릭터 이미지를 배경의 1/4 크기로 조정
                    char_height = int(char_image.height * (char_width / char_image.width))
                    char_image = char_image.resize((char_width, char_height))

                    # 말풍선 이미지를 캐릭터 위에 적절한 크기로 조정
                    bubble_width = char_width
                    bubble_height = int(speech_bubble_image.height * (bubble_width / speech_bubble_image.width))
                    speech_bubble_image = speech_bubble_image.resize((bubble_width, bubble_height))

                    # 말풍선에 텍스트 추가
                    speech_bubble_image = add_text_to_speech_bubble(speech_bubble_image, prompt)

                    # 배경 이미지에 캐릭터 이미지 결합
                    combined_image = background_image.copy()
                    char_x = (bg_width - char_width) // 2
                    char_y = bg_height - char_height - 20  # 바닥에서 20픽셀 위
                    combined_image.paste(char_image, (char_x, char_y), char_image)

                    # 말풍선을 캐릭터 이미지 위에 결합
                    bubble_x = char_x
                    bubble_y = char_y - bubble_height - 10  # 캐릭터 위에 10픽셀 위
                    combined_image.paste(speech_bubble_image, (bubble_x, bubble_y), speech_bubble_image)

                    st.image(combined_image, caption=f"{most_similar_ch_name} with background and speech bubble", use_column_width=True)
                elif image_file:
                    image = Image.open(image_file)
                    st.image(image, caption=os.path.basename(image_file), width=300)
                else:
                    st.write("No similar image file found.")
            else:
                st.write("Failed to retrieve valid response from OpenAI.")
        else:
            st.write("Failed to retrieve valid response from OpenAI.")
    else:
        st.write("Enter a description, select a job, and a gender to find a character image.")