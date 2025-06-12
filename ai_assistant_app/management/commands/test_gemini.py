from django.core.management.base import BaseCommand
from django.conf import settings # settings.py からAPIキーを読み込むため
import google.generativeai as genai # インストールしたライブラリ！

class Command(BaseCommand):
    help = 'Gemini APIとの簡単な疎通確認テストを行います。'

    def handle(self, *args, **options):
        self.stdout.write("Gemini APIとの接続テストを開始します...")

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            self.stderr.write(self.style.ERROR("エラー: GEMINI_API_KEYが設定されていません。"))
            return

        try:
            # APIキーを設定
            genai.configure(api_key=api_key)

            # 使用するモデルを選択 (gemini-pro はテキスト生成が得意なモデルだよ！)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')

            # 簡単なプロンプト（お願い）を送信
            prompt = "こんにちは！あけおめ！"
            self.stdout.write(f"Geminiに送信するプロンプト: '{prompt}'")
            
            response = model.generate_content(prompt)

            # 応答を表示
            self.stdout.write(self.style.SUCCESS("Geminiからの応答:"))
            # response.text で、AIが生成したテキストが取れるよ！
            self.stdout.write(response.text) 
            
            self.stdout.write(self.style.SUCCESS("テストが正常に完了しました！"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"テスト中にエラーが発生しました: {e}"))
