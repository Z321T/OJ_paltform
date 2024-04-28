from django.db import models

from administrator_app.models import ProgrammingExercise
from student_app.models import Student
from teacher_app.models import ExerciseQuestion, ExamQuestion


# Create your models here.
# class CodeFeature(models.Model):
#     student = models.ForeignKey(Student, on_delete=models.SET_NULL, verbose_name="学生",
#                                 related_name='code_features', null=True)
#     exercise_question = models.ForeignKey(ExerciseQuestion, on_delete=models.CASCADE,
#                                           verbose_name="练习题", related_name='code_features', null=True, blank=True)
#     exam_question = models.ForeignKey(ExamQuestion, on_delete=models.CASCADE,
#                                       verbose_name="考试题", related_name='code_features', null=True, blank=True)
#     feature = models.TextField(verbose_name="特征值")
#
#     def __str__(self):
#         return (f"{self.student.name if self.student else '无关联学生'} - "
#                 f"{self.exercise_question or self.exam_question} - {self.feature}")


class ProgrammingCodeFeature(models.Model):
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, verbose_name="学生",
                                related_name='programming_code_features', null=True)
    programming_question = models.ForeignKey(ProgrammingExercise, on_delete=models.CASCADE, verbose_name="练习题",
                                             related_name='programming_code_features', null=True, blank=True)
    feature = models.TextField(verbose_name="特征值")
    cosine_similarity = models.FloatField(verbose_name="余弦相似度", null=True, blank=True)
    similar_student = models.ForeignKey(Student, on_delete=models.SET_NULL, verbose_name="相似的学生用户",
                                        related_name='similar_code_students', null=True, blank=True)

    def __str__(self):
        return (f"{self.student.name if self.student else '无关联学生'} - "
                f"{self.programming_question} - {self.feature}")


class ProgrammingReportFeature(models.Model):
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, verbose_name="学生",
                                related_name='programming_report_features', null=True)
    programming_question = models.ForeignKey(ProgrammingExercise, on_delete=models.CASCADE, verbose_name="练习题",
                                             related_name='programming_report_features', null=True, blank=True)
    feature = models.TextField(verbose_name="特征值")
    cosine_similarity = models.FloatField(verbose_name="余弦相似度", null=True, blank=True)
    similar_student = models.ForeignKey(Student, on_delete=models.SET_NULL, verbose_name="相似的学生用户",
                                        related_name='similar_report_students', null=True, blank=True)

    def __str__(self):
        return (f"{self.student.name if self.student else '无关联学生'} - "
                f"{self.programming_question} - {self.feature}")


class ReportStandardScore(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生",
                                related_name='report_standards')
    programming_question = models.ForeignKey(ProgrammingExercise, on_delete=models.CASCADE, verbose_name="练习题",
                                             related_name='report_standards')
    standard_score = models.IntegerField(verbose_name="报告规范性得分")


# class CodeStandardScore(models.Model):
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生",
#                                 related_name='code_standards')
#     programming_question = models.ForeignKey(ProgrammingExercise, on_delete=models.CASCADE, verbose_name="练习题",
#                                              related_name='code_standards')
#     standard_score = models.IntegerField(default=0, verbose_name="代码规范性得分")
#     添加代码文件路径字段在PyTorch中，可以使用torch.Tensor.view(*shape)方法来调整张量的大小，该方法返回具有相同数据但大小不同的新张量。这种方式常见于将多维张量展平为一维张量使用。
#     例如，如果我们有一个大小为[2, 3]的张量，我们可以使用view(-1)将它展平为一个一维张量，如下：
#     python
#     import torch
#
#     # 一个大小为[2, 3]的二维张量
#     x = torch.tensor([[1, 2, 3], [4, 5, 6]])
#
#     # 使用.view(-1)将其展平为一维张量
#     x_flat = x.view(-1)
#
#     print(x_flat)
#     # 输出: tensor([1, 2, 3, 4, 5, 6])
#     但请注意，重塑张量的前提是，新的形状必须能够与原始张量的元素数量相吻合。例如，如果原始张量的元素总数是12（例如，形状是[3, 4]），那么重塑后的张量的元素总数也必须是12（例如，形状可以是[2, 6]，也可以是[12]，但不能是[2, 5]）。
#     对于你的场景，你可能需要首先确认两个张量feature1和feature2是否应该有相同的大小，如果应该有相同的大小，那么需要查明为什么它们的大小不同，可能是在数据预处理阶段出现了某些错误。另外，如果它们的大小不需要完全一样，那么就需要找到一种方式来让这两个张量可以比较（例如，可能可以通过取平均，或者其他某种聚合函数对它们进行处理以得到相同大小的结果）。希望这个能帮你！
#     file_path = models.CharField(max_length=200, verbose_name="代码文件路径", null=True, blank=True)




