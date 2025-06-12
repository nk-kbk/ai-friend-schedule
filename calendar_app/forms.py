# calendar_app/forms.py
from django import forms
from .models import Schedule
from django.utils import timezone # timezone は使ってなければ不要かも

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        # fields に、ユーザーに入力してもらいたい項目を指定するよ！
        fields = [
            'title',
            'description',
            'start_datetime',
            'end_datetime',
            'location',
            # 'is_recurring', # 👈 これを削除！
            # 'recurrence_rule' # 👈 これも削除！
            # ✨ participants フィールドもフォームで扱いたいなら、ここに追加する！ ✨
            # 'participants', # (ウィジェットの指定も必要になるかも)
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            # 'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}), # 👈 削除！
        }
        labels = {
            'title': 'タイトル',
            'description': '詳細',
            'start_datetime': '開始日時',
            'end_datetime': '終了日時',
            'location': '場所',
            # 'is_recurring': '繰り返し予定ですか？', # 👈 削除！
            # 'recurrence_rule': '繰り返しルール (例:FREQ=WEEKLY;BYDAY=MO)', # 👈 削除！
            'participants': '参加者', # (もしparticipantsをフォームで扱うなら)
        }
        help_texts = {
            # 'recurrence_rule': 'iCalendar形式で入力。例: 毎週月曜なら「FREQ=WEEKLY;BYDAY=MO」', # 👈 削除！
        }

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get("start_datetime")
        end_datetime = cleaned_data.get("end_datetime")

        if start_datetime and end_datetime:
            if end_datetime < start_datetime:
                self.add_error('end_datetime', "終了日時は開始日時より後の日付を設定してください。")
        return cleaned_data

    # participants フィールドをフォームで扱う場合の追加処理 (例)
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if 'participants' in self.fields:
    #         # ログインユーザーを参加者から除外する (任意)
    #         # from accounts.models import User # Userモデルをインポート
    #         # self.fields['participants'].queryset = User.objects.exclude(id=self.request.user.id) # requestオブジェクトが必要
    #         # あるいは、友達だけを選択できるようにする、なども考えられる
    #         pass
