import sys
import os
import threading
from flask import Flask, render_template, request, jsonify
import webview
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# --- 1. 资源路径处理 (为了打包exe准备) ---
def resource_path(relative_path):
    """ 获取资源的绝对路径，适配 PyInstaller 打包后的路径 """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- 2. 初始化 Flask，指定模板和静态文件夹路径 ---
app = Flask(__name__, 
            template_folder=resource_path('templates'), 
            static_folder=resource_path('static'))

client = genai.Client()
TRANSLATION_PROMPT = (
    """
你是一位专业的、细致入微的翻译官。你的任务是根据用户提供的【源语言文本】进行高精度翻译。

请严格遵守以下指令和步骤：

### **1. 翻译核心要求**

* **准确性 (Accuracy):** 确保翻译忠实于源文本的**语义、语境和事实信息**。不得增加、删除或扭曲任何核心信息。
* **流畅性 (Fluency):** 翻译结果必须符合目标语言的**自然表达习惯**，行文流畅、地道，仿佛由目标语言母语者写成。
* **风格与语气 (Style & Tone):** 保持源文本的**正式程度、专业领域和情感色彩**。如果源文本是技术文档，翻译就应保持严谨和专业；如果是非正式对话，翻译就应轻松自然。
* **格式保留 (Formatting):** 严格保留源文本中的所有**Markdown格式**（如粗体 `**`、斜体 `*`、列表 `* `、代码块 `` ` `` 或 ``` `), HTML标签，以及任何特殊标点符号和结构。
* **专有名词处理 (Proper Nouns):** 对于人名、地名、组织名、品牌名、专业术语等，如果源语言中有通用的或官方的译法，请采用该译法；如果没有，请进行合理的**音译或保留原文**（并在必要时提供注释）。

### **2. 翻译步骤**

1.  **分析上下文:** 首先分析源文本的**类型**（如商务邮件、文学作品、技术说明、日常对话等）和**隐含语境**。
2.  **执行翻译:** 逐句、逐段进行翻译，确保译文在整体上保持连贯和统一。
3.  **最终审校:** 检查译文是否满足“准确性”、“流畅性”和“格式保留”等所有核心要求。

### **3. 待处理任务**

* **源语言文本 (Source Text):** [此处会插入用户待翻译的文本]
* **要求：如果输入文本是中文，就将其翻译成英文；如果输入文本是英文或其他语言，就将其翻译成中文

### **4. 输出格式**

请直接输出**最终的、唯一的翻译结果**，不要添加任何解释、评论、标题或额外的说明文字。
    """
)


# --- 这是你的翻译函数 ---
def translate_logic(text):
    # 组合用户请求和系统指令
    user_prompt = f"请翻译这段文字：\n {text}"
    
    config = types.GenerateContentConfig(
        # 在这里设置你的全局翻译指引
        system_instruction=TRANSLATION_PROMPT,
        # 可以添加其他配置，例如温度 (temperature)
        temperature=0.7
    )

    response = client.models.generate_content(
        model='gemini-2.5-flash',  # 选择合适的模型
        contents=[user_prompt],
        config=config,
    )
    
    return response.text




# --- 4. 路由设置 ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/translate', methods=['POST'])
def get_translation():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'result': ''})

    result_text = translate_logic(text)
    return jsonify({'result': result_text})

# --- 5. 启动服务 ---
def start_server():
    app.run(host='127.0.0.1', port=54321, threaded=True)

if __name__ == '__main__':
    # 启动 Flask 线程
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    # 启动桌面窗口
    webview.create_window(
        title="Markdown Translator Pro", 
        url="http://127.0.0.1:54321",
        width=1100,
        height=800,
        resizable=True,
        min_size=(900, 600),
        text_select=True,
        frameless=False
    )
    
    webview.start()
