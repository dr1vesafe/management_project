from sqladmin import ModelView

from src.app.models.evaluation import Evaluation


class EvaluationAdmin(ModelView, model=Evaluation):
    name = 'Evaluation'
    name_plural = 'Evaluations'
    icon = 'fa-solid fa-thumbs-up'

    column_list = [
        Evaluation.id,
        Evaluation.manager_id,
        Evaluation.task_id,
        Evaluation.grade
    ]
    column_searchable_list = [Evaluation.task_id]
    column_sortable_list = [
        Evaluation.id,
        Evaluation.manager_id,
        Evaluation.task_id,
        Evaluation.grade
    ]

    form_columns = [
        Evaluation.grade,
        Evaluation.comment
    ]