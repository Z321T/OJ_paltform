import torch
import json
from sklearn.decomposition import PCA
from django.shortcuts import get_object_or_404
from transformers import AutoTokenizer, AutoModel
from torch.nn.functional import cosine_similarity

from BERT_app.models import (ProgrammingCodeFeature, ProgrammingReportFeature,
                             ReportStandardScore)
from administrator_app.models import ProgrammingExercise
from teacher_app.models import ReportScore, Class

# 加载 CodeBERT 模型和分词器
codebert_tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
codebert_model = AutoModel.from_pretrained("microsoft/codebert-base")
# 加载 Sentence-BERT 模型和分词器
sbert_tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
sbert_model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')

# 如果有GPU可用，移动模型到GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
codebert_model.to(device)
sbert_model.to(device)


# 分析程序设计题代码
def analyze_programming_code(student, code, question_id):
    # 代码分词
    tokenized_code = codebert_tokenizer.tokenize(code)
    features = []
    for i in range(0, len(tokenized_code), 512):
        inputs = codebert_tokenizer(tokenized_code[i:i+512], return_tensors="pt", padding=True, truncation=True, max_length=512)
        # 获取特征值
        with torch.no_grad():
            feature = codebert_model(**inputs).last_hidden_state.mean(dim=1)
            features.append(feature)
    # 连接所有特征值
    concatenated_features = torch.cat(features, dim=0)
    # 使用 PCA 进行维度减少
    pca = PCA(n_components=2)
    # 注意：PCA需要在CPU上的NumPy数组上运行
    reduced_features = pca.fit_transform(concatenated_features.cpu().numpy())
    # 将降维后的特征转换为JSON格式
    feature_as_json = json.dumps(reduced_features.tolist())

    question = ProgrammingExercise.objects.get(id=question_id)

    ProgrammingCodeFeature.objects.update_or_create(
        student=student,
        programming_question=question,
        defaults={'feature': feature_as_json}
    )


# 分析程序设计题报告
def analyze_programming_report(student, report, question_id):
    # 报告分词
    tokenized_report = sbert_tokenizer.tokenize(report)
    features = []
    for i in range(0, len(tokenized_report), 512):
        inputs = sbert_tokenizer(tokenized_report[i:i+512], return_tensors="pt", padding=True, truncation=True, max_length=512)
        # 获取特征值
        with torch.no_grad():
            feature = sbert_model(**inputs).last_hidden_state.mean(dim=1)
            features.append(feature)
    # 连接所有特征值
    concatenated_features = torch.cat(features, dim=0)
    # 使用 PCA 进行维度减少
    pca = PCA(n_components=2)
    # 注意：PCA需要在CPU上的NumPy数组上运行
    reduced_features = pca.fit_transform(concatenated_features.cpu().numpy())
    # 将降维后的特征转换为JSON格式
    feature_as_json = json.dumps(reduced_features.tolist())

    question = ProgrammingExercise.objects.get(id=question_id)

    ProgrammingReportFeature.objects.update_or_create(
        student=student,
        programming_question=question,
        defaults={'feature': feature_as_json}
    )


# 计算程序设计报告&代码的相似度
def compute_cosine_similarity(feature_json1, feature_json2):
    feature1 = torch.tensor(json.loads(feature_json1)).float()
    feature2 = torch.tensor(json.loads(feature_json2)).float()

    # 确定填充长度，使得两个张量的第一个维度长度相同。
    len_feature1 = feature1.size(0)
    len_feature2 = feature2.size(0)

    # 如果第一个张量比第二个短，那么添加零填充至第一个张量
    if len_feature1 < len_feature2:
        padding = len_feature2 - len_feature1
        feature1 = torch.cat((feature1, torch.zeros(padding, feature1.size(1))), dim=0)
    # 否则，在第二个张量上执行相同的操作
    elif len_feature1 > len_feature2:
        padding = len_feature1 - len_feature2
        feature2 = torch.cat((feature2, torch.zeros(padding, feature2.size(1))), dim=0)

    similarity_score = cosine_similarity(feature1, feature2).mean().item()

    return similarity_score


# 报告规范性评分
def score_report(student, document, programmingexercise_id):
    class_assigned = student.class_assigned
    teacher = get_object_or_404(Class, id=class_assigned.id).teacher
    report_score = ReportScore.objects.get(teacher=teacher)

    total_score = report_score.totalscore
    content_score = report_score.contents
    firstrow_score = report_score.firstrow
    fontsize_score = report_score.fontsize
    image_score = report_score.image
    pagenum_score = report_score.pagenum
    # 初始化标记为False，表示尚未扣除分数
    content_deducted = False
    firstrow_deducted = False
    fontsize_deducted = False
    image_deducted = False
    pagenum_deducted = False

    # 1. 检查文档是否含有目录
    has_table_of_contents = False
    for para in document.paragraphs:
        if "目录" in para.text:
            has_table_of_contents = True  # 找到目录标记为True并中断循环
            break

    if not has_table_of_contents and not content_deducted:
        total_score += content_score
        content_deducted = True  # 标记为已扣过分

    # 2. 检查每个段落的首行缩进
    for para in document.paragraphs:
        if not para.paragraph_format.first_line_indent or para.paragraph_format.first_line_indent.pt != 36:
            if not firstrow_deducted:
                total_score += firstrow_score
                firstrow_deducted = True  # 设置标志位
            break

    # 3. 检查段落中的文字字体大小是否为12
    for para in document.paragraphs:
        for run in para.runs:
            if run.font.size and abs(run.font.size.pt - 12) > 1:
                if not fontsize_deducted:
                    total_score += fontsize_score
                    fontsize_deducted = True  # 设置标志位
                break
        if fontsize_deducted:
            break

    # 4. 检查文档中的图像是否居中对齐
    for shape in document.inline_shapes:
        if shape.type == 3:
            if shape.text_frame.paragraph.alignment != 1:
                if not image_deducted:
                    total_score += image_score
                    image_deducted = True  # 设置标志位
                break

    # 5. 计算有页码的页面占比
    def score_page_numbers(doc):
        total_pages = len(doc.sections)
        for section in doc.sections:
            page_number_found = False
            for para in section.footer.paragraphs:
                if any(char.isdigit() for char in para.text):
                    page_number_found = True
                    break
            if not page_number_found:
                return True
        if total_pages == 0:
            return True
        return False

    if not score_page_numbers(document) and not pagenum_deducted:
        total_score += pagenum_score
        pagenum_deducted = True  # 设置标志位

    # 保存分数
    ReportStandardScore.objects.update_or_create(
        student=student,
        programming_question_id=programmingexercise_id,
        defaults={'standard_score': total_score}
    )

