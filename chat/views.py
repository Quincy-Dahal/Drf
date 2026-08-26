"""
chat/views.py

The actual chat endpoint. The send_message action:
    1. Looks up an existing Conversation, or starts a new one
    2. Saves the visitor's message
    3. Sends the full conversation history to core.llm.chat()
    4. Saves the bot's reply
    5. Returns the reply plus the conversation_id to continue with

"""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.llm import LLMError
from core.llm import chat as llm_chat

from .models import Conversation, Message
from .serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
    ConversationSerializer,
)


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to conversations and their message history.
    """

    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer

    @extend_schema(
        request=ChatRequestSerializer,
        responses={200: ChatResponseSerializer},
        description=(
            "Send a message to the chatbot. Omit conversation_id to start "
            "a new conversation; include it to continue an existing one."
        ),
    )
    @action(detail=False, methods=["post"], url_path="send-message")
    def send_message(self, request):
        req = ChatRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        conversation_id = req.validated_data.get("conversation_id")
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = Conversation.objects.create()

        user_text = req.validated_data["message"]
        Message.objects.create(
            conversation=conversation, role=Message.Role.USER, content=user_text
        )

        history = [
            {"role": m.role, "content": m.content}
            for m in conversation.messages.all()
        ]

        try:
            reply_text = llm_chat(history)
        except LLMError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        Message.objects.create(
            conversation=conversation, role=Message.Role.ASSISTANT, content=reply_text
        )
        conversation.save()  # bumps updated_at

        response = ChatResponseSerializer(
            {"conversation_id": conversation.id, "reply": reply_text}
        )
        return Response(response.data, status=status.HTTP_200_OK)