# ai_assistant_app/views.py の完全な書き換え版！

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from django.utils import timezone
from datetime import timedelta, datetime
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import AICharacter, AIChatHistory
import traceback
from django.utils.html import json_script
import requests
import os
import uuid

# --- Gemini AIの設定 ---
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    print("警告: GEMINI_API_KEYが設定されていません。AIアシスタント機能は動作しません。")

# --- ai_chat_view (変更なし) ---
@login_required
@require_GET
def ai_chat_view(request, character_id):
    ai_character = get_object_or_404(AICharacter, id=character_id)
    if request.user.selected_ai_character_id != character_id:
        request.user.selected_ai_character_id = character_id
        request.user.save(update_fields=['selected_ai_character_id'])
    
    chat_history_queryset = AIChatHistory.objects.filter(
        user=request.user,
        ai_character=ai_character
    ).order_by('timestamp')
    
    chat_history_list = [
        {
            'sender_type': h.sender_type,
            'message_text': h.message_text,
            'timestamp': h.timestamp.isoformat()
        } for h in chat_history_queryset
    ]

    context = {
        'ai_character': ai_character,
        'chat_history_json': json_script(chat_history_list, "chat-history-data"),
        'page_title': f'{ai_character.character_name} とおしゃべり'
    }
    return render(request, 'ai_assistant_app/chat_interface.html', context)

# --- ✨ send_message_to_ai_view を【ボタンで確認バージョン】に！ ---
@login_required
@require_POST
def send_message_to_ai_view(request, character_id):
    if not settings.GEMINI_API_KEY:
        return JsonResponse({'error': 'AI機能が現在利用できません。(APIキー未設定)'}, status=503)

    try:
        data = json.loads(request.body)
        user_message_text = data.get('message', '').strip()
        if not user_message_text:
            return JsonResponse({'error': 'メッセージが空です。'}, status=400)

        ai_character = get_object_or_404(AICharacter, id=character_id)

        # ユーザーのメッセージを履歴に保存
        AIChatHistory.objects.create(
            user=request.user, 
            ai_character=ai_character, 
            message_text=user_message_text, 
            sender_type=AIChatHistory.SENDER_USER
        )
        
        # 直近の会話履歴を文脈としてAIに渡す
        db_chat_history = AIChatHistory.objects.filter(user=request.user, ai_character=ai_character).order_by('-timestamp')[:5]
        history_for_ai_list = [f"{'AI' if h.sender_type == 'ai' else 'User'}: {h.message_text.split('<!--')[0].strip()}" for h in reversed(db_chat_history)]
        history_for_ai = "\n".join(history_for_ai_list)
        
        final_prompt_for_ai = (
            f"これはユーザーとの過去の会話履歴です:\n---\n{history_for_ai}\n---\n"
            f"この会話の文脈を踏まえて、ユーザーの最新の発言「{user_message_text}」に最も適切に応答するJSONを生成してください。"
        )

        model = genai.GenerativeModel(
            'gemini-1.5-pro-latest',
            system_instruction=ai_character.prompt_template
        )
        
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        
        response = model.generate_content(final_prompt_for_ai, generation_config=generation_config)
        
        ai_json_response = json.loads(response.text)
        
        speech_text = ai_json_response.get('speech_text', '')

        # 音声合成の前に「///」を自然な「間」に置き換える
        text_for_speech = speech_text.replace('///', '…')

        # ✨ 自動作成処理はここには書かない！✨

        # CoeFont APIによる音声合成
        audio_url = None
        if settings.COEFONT_API_KEY and settings.COEFONT_ID_AYA and text_for_speech:
            try:
                url = "https://api.coefont.cloud/v2/text2speech"
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {settings.COEFONT_API_KEY}"}
                payload = {"coefont": settings.COEFONT_ID_AYA, "text": text_for_speech}
                response_audio = requests.post(url, headers=headers, data=json.dumps(payload))
                response_audio.raise_for_status()
                
                audio_folder = os.path.join(settings.MEDIA_ROOT, 'audio')
                os.makedirs(audio_folder, exist_ok=True)
                filename = f"{uuid.uuid4()}.wav"
                filepath = os.path.join(audio_folder, filename)
                with open(filepath, "wb") as out:
                    out.write(response_audio.content)
                audio_url = os.path.join(settings.MEDIA_URL, 'audio', filename).replace('\\', '/')
            except Exception as e:
                print(f"CoeFont APIでの音声合成中にエラーが発生しました: {e}")
        
        # フロントには、AIが作ったJSONをそのまま埋め込んで返す！
        text_to_save_and_send = f"{speech_text}<!-- SCHEDULE_PROPOSAL_DATA_START -->{json.dumps(ai_json_response)}<!-- SCHEDULE_PROPOSAL_DATA_END -->"

        # AIの応答を履歴に保存
        AIChatHistory.objects.create(
            user=request.user, ai_character=ai_character, 
            message_text=text_to_save_and_send,
            sender_type=AIChatHistory.SENDER_AI
        )

        # フロントエンドに返すデータ
        return JsonResponse({
            'reply': text_to_save_and_send,
            'audio_url': audio_url
        })

    except Exception as e:
        traceback.print_exc()
        user_error_message = 'ごめんね！AIとの会話中に予期せぬエラーが発生しちゃったみたい…。'
        return JsonResponse({'error': user_error_message}, status=500)

# --- (reset_chat_history_view, get_ai_character_list_view は変更なし) ---
@login_required
@require_POST
def reset_chat_history_view(request, character_id):
    ai_character = get_object_or_404(AICharacter, id=character_id)
    AIChatHistory.objects.filter(user=request.user, ai_character=ai_character).delete()
    messages.success(request, f'{ai_character.character_name}との会話履歴がリセットされました。')
    return redirect(reverse_lazy('ai_assistant_app:ai_chat', args=[character_id]))

@login_required 
@require_GET
def get_ai_character_list_view(request):
    characters = AICharacter.objects.all().values('id', 'character_name', 'icon_url', 'description')
    user_selected_char_id = request.user.selected_ai_character_id
    return JsonResponse({'characters': list(characters), 'user_selected_char_id': user_selected_char_id})