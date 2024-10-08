import streamlit as st
import pandas as pd
import math
from pathlib import Path
import os
import pdfplumber
import re
import zipfile
from io import BytesIO

import os
import streamlit as st
import pdfplumber
import re
import zipfile
from io import BytesIO
from PIL import Image

# 提取发票号码的函数
def extract_invoice_number(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()

        # 使用正则表达式匹配发票号码
        match = re.search(r'发票号码[:：]\s*(\d+)', text)
        if match:
            return match.group(1)  # 返回发票号码
        else:
            return None

# 从上传的 ZIP 文件中提取 PDF 文件和图片，并生成文件名
# def extract_files_from_zip(zip_file):
#     pdf_files = []
#     image_files = []
#     pdf_file_names = []
#     image_file_names = []

#     with zipfile.ZipFile(zip_file) as z:
#         for file_name in z.namelist():
#             # 处理 PDF 文件
#             if file_name.endswith('.pdf'):
#                 pdf_files.append(BytesIO(z.read(file_name)))
#                 pdf_file_names.append(file_name)  # 保留文件名
#             # 处理图片文件
#             elif file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
#                 image_files.append(BytesIO(z.read(file_name)))
#                 image_file_names.append(file_name)  # 保留文件名
#     return pdf_files, image_files, pdf_file_names, image_file_names

def extract_files_from_zip(zip_file):
    pdf_files = []
    image_files = []
    pdf_file_names = []
    image_file_names = []

    with zipfile.ZipFile(zip_file) as z:
        for file_info in z.infolist():
            file_name = file_info.filename
            try:
                # 尝试使用 UTF-8 解码
                file_name = file_name.encode('utf-8').decode('utf-8')
            except UnicodeDecodeError:
                try:
                    # 如果 UTF-8 失败，尝试 GBK
                    file_name = file_name.encode('utf-8').decode('gbk')
                except UnicodeDecodeError:
                    # 如果都失败，保留原始文件名
                    file_name = file_info.filename

            # 处理 PDF 文件
            if file_name.endswith('.pdf'):
                pdf_files.append(BytesIO(z.read(file_info.filename)))
                pdf_file_names.append(file_name)  # 保留文件名
            # 处理图片文件
            elif file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(BytesIO(z.read(file_info.filename)))
                image_file_names.append(file_name)  # 保留文件名

    return pdf_files, image_files, pdf_file_names, image_file_names

# 检查并删除重复发票的函数
def remove_duplicate_pdfs(uploaded_files, file_names):
    st.write("Processing uploaded files...")
    seen_invoice_numbers = set()
    unique_files = []
    duplicate_files = []
    unique_file_names = []
    duplicate_file_names = []

    for file, file_name in zip(uploaded_files, file_names):
        invoice_number = extract_invoice_number(file)

        if invoice_number:
            if invoice_number in seen_invoice_numbers:
                duplicate_files.append(file)  # 重复文件
                duplicate_file_names.append(file_name)
            else:
                seen_invoice_numbers.add(invoice_number)
                unique_files.append(file)  # 唯一文件
                unique_file_names.append(file_name)
        else:
            st.write(f"未找到发票号码: {file_name}")

    return unique_files, duplicate_files, unique_file_names, duplicate_file_names

# 将处理过的唯一文件打包成ZIP
def create_zip_from_files(unique_pdfs, unique_images, pdf_file_names, image_file_names):
    # 创建一个内存中的 BytesIO 对象，用于临时存储压缩文件
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file, file_name in zip(unique_pdfs, pdf_file_names):
            zip_file.writestr(file_name, file.getvalue())  # 保存PDF文件

        for img, img_name in zip(unique_images, image_file_names):
            zip_file.writestr(img_name, img.getvalue())  # 保存图片文件

    # 返回 ZIP 文件的字节数据
    zip_buffer.seek(0)
    return zip_buffer

# Streamlit 应用
st.title("文件夹处理工具 (支持PDF、图片、压缩包)")

# 上传包含 PDF 文件、图片、压缩包 的 ZIP 文件
uploaded_files = st.file_uploader("上传PDF文件或压缩包", type=["pdf", "zip"], accept_multiple_files=True)

# 检查是否有上传的文件
if uploaded_files:
    st.write("Uploaded files:", uploaded_files)  # 检查上传的文件是否成功

    # 存储所有上传的PDF文件和图片文件
    pdf_files = []
    image_files = []
    pdf_file_names = []
    image_file_names = []

    # 处理上传的文件
    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith(".pdf"):
            pdf_files.append(uploaded_file)  # 直接添加 PDF 文件
            pdf_file_names.append(uploaded_file.name)  # 保留 PDF 文件名
        elif uploaded_file.name.endswith(".zip"):
            extracted_pdfs, extracted_images, extracted_pdf_names, extracted_image_names = extract_files_from_zip(uploaded_file)  # 解压 ZIP 中的 PDF 和图片
            pdf_files.extend(extracted_pdfs)  # 将解压的 PDF 文件加入列表
            image_files.extend(extracted_images)  # 将解压的图片文件加入列表
            pdf_file_names.extend(extracted_pdf_names)  # 保留解压的 PDF 文件名
            image_file_names.extend(extracted_image_names)  # 保留解压的图片文件名

    # 按钮触发去重操作
    if st.button('处理文件'):
        if pdf_files or image_files:
            # 去重处理 PDF 文件
            unique_pdfs, duplicate_pdfs, unique_pdf_names, duplicate_pdf_names = remove_duplicate_pdfs(pdf_files, pdf_file_names)

            # 显示处理结果
            if unique_pdfs:
                st.write("处理完成，以下为唯一的 PDF 文件:")
                for file_name in unique_pdf_names:
                    st.write(file_name)

            if duplicate_pdfs:
                st.write("以下为重复的 PDF 文件（已删除）:")
                for file_name in duplicate_pdf_names:
                    st.write(file_name)

            if image_files:
                st.write(f"提取到 {len(image_files)} 张图片文件")

            # 将处理好的文件打包成 ZIP 并提供下载
            zip_file = create_zip_from_files(unique_pdfs, image_files, unique_pdf_names, image_file_names)
            st.download_button(
                label="下载处理后的 ZIP 文件",
                data=zip_file,
                file_name="processed_files.zip",
                mime="application/zip"
            )
        else:
            st.write("没有找到任何 PDF 或图片文件。")
