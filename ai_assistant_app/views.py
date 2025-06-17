# ai_assistant_app/views.py の完全なコード

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
import google.generativeai as genai
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib import messages
from .models import AICharacter, AIChatHistory
import traceback
from django.utils.html import json_script
import requests
import os
import uuid

# ✨ pytz をインポートして、タイムゾーンの魔法を使えるようにする！
import pytz

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    print("警告: GEMINI_API_KEYが設定されていません。")

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

        AIChatHistory.objects.create(
            user=request.user, 
            ai_character=ai_character, 
            message_text=user_message_text, 
            sender_type=AIChatHistory.SENDER_USER
        )
        
        db_chat_history = AIChatHistory.objects.filter(user=request.user, ai_character=ai_character).order_by('-timestamp')[:5]
        history_for_ai_list = [f"{'AI' if h.sender_type == 'ai' else 'User'}: {h.message_text.split('<!--')[0].strip()}" for h in reversed(db_chat_history)]
        history_for_ai = "\n".join(history_for_ai_list)
        
        # --- ✨✨ ここが最終・確定の修正ポイント！ ✨✨ ---
        # 1. UTC（世界の基準時間）で、今の時間を取得
        utc_now = timezone.now()
        # 2. 日本のタイムゾーン情報を取得
        jst = pytz.timezone('Asia/Tokyo')
        # 3. UTCの時間を、日本の時間に変換！
        jst_now = utc_now.astimezone(jst)
        # 4. AIに教えるために、日本の時間を文字列に変換
        now_str_for_ai = jst_now.strftime('%Y-%m-%d %H:%M')

        # ユーザーからのメッセージの直前に、正しい日本の現在時刻の情報を叩き込む！
        final_prompt_for_ai = (
            f"過去の会話履歴:\n---\n{history_for_ai}\n---\n"
            f"【最重要指示】現在の日時は {now_str_for_ai} です。これを厳密な基準として、ユーザーの次の発言を解釈してください。\n"
            f"ユーザーの最新の発言:「{user_message_text}」"
        )

        model = genai.GenerativeModel('gemini-1.5-pro-latest', system_instruction=ai_character.prompt_template)
        # --- ✨✨ 改良ポイントはここまで！ ✨✨ ---

        generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
        response = model.generate_content(final_prompt_for_ai, generation_config=generation_config)
        
        ai_json_response = json.loads(response.text)
        speech_text = ai_json_response.get('speech_text', '')
        text_for_speech = speech_text.replace('///', '…')

        audio_url = None
        if settings.NIJIVOICE_API_KEY and settings.NIJIVOICE_VOICE_ACTOR_ID and text_for_speech:
            try:
                url_for_getting_dl_url = f"https://api.nijivoice.com/api/platform/v1/voice-actors/{settings.NIJIVOICE_VOICE_ACTOR_ID}/generate-voice"
                headers = {"accept": "application/json", "Content-Type": "application/json", "x-api-key": settings.NIJIVOICE_API_KEY}
                payload = {"script": text_for_speech, "speed": "1.0", "format": "mp3"}
                response_for_url = requests.post(url_for_getting_dl_url, headers=headers, data=json.dumps(payload))
                response_for_url.raise_for_status()
                response_json = response_for_url.json()
                download_url = response_json.get('generatedVoice', {}).get('audioFileDownloadUrl')
                if not download_url:
                    raise Exception("JSONレスポンスにダウンロードURLが含まれていません。")
                response_audio_content = requests.get(download_url)
                response_audio_content.raise_for_status()
                audio_folder = os.path.join(settings.MEDIA_ROOT, 'audio')
                os.makedirs(audio_folder, exist_ok=True)
                filename = f"{uuid.uuid4()}.mp3"
                filepath = os.path.join(audio_folder, filename)
                with open(filepath, "wb") as out:
                    out.write(response_audio_content.content)
                audio_url = os.path.join(settings.MEDIA_URL, 'audio', filename).replace('\\', '/')
            except Exception as e:
                print(f"--- にじボイスAPI処理中にエラー発生！ ---")
                print(f"エラー内容: {e}")

        text_to_save_and_send = f"{speech_text}<!-- SCHEDULE_PROPOSAL_DATA_START -->{json.dumps(ai_json_response)}<!-- SCHEDULE_PROPOSAL_DATA_END -->"

        AIChatHistory.objects.create(
            user=request.user, ai_character=ai_character, 
            message_text=text_to_save_and_send,
            sender_type=AIChatHistory.SENDER_AI
        )

        final_audio_url = request.build_absolute_uri(audio_url) if audio_url else None
        
        return JsonResponse({
            'reply': text_to_save_and_send,
            'audio_url': final_audio_url
        })

    except Exception as e:
        traceback.print_exc()
        user_error_message = 'ごめんね！AIとの会話中に予期せぬエラーが発生しちゃったみたい…。'
        return JsonResponse({'error': user_error_message}, status=500)


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