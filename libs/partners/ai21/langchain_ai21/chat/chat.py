from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Union, cast

from ai21.models import ChatMessage as J2ChatMessage
from ai21.models import RoleType
from ai21.models.chat import ChatMessage
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

_ChatMessageType = Union[ChatMessage, J2ChatMessage]


class Chat(ABC):
    def convert_messages(self, messages: List[BaseMessage]) -> Tuple[str, List[_ChatMessageType]]:
        system_message = None
        converted_messages: List[_ChatMessageType] = []

        for i, message in enumerate(messages):
            if message.type == "system":
                if i != 0:
                    raise ValueError("System message must be at "
                                     "beginning of message list.")
                else:
                    system_message = self._get_system_message_from_message(message)
            else:
                converted_message = self._convert_message_to_ai21_message(message)
                converted_messages.append(converted_message)

        return system_message, converted_messages

    def _convert_message_to_ai21_message(
            self,
            message: BaseMessage,
    ) -> ChatMessage:
        content = cast(str, message.content)

        role = None

        if isinstance(message, HumanMessage):
            role = RoleType.USER
        elif isinstance(message, AIMessage):
            role = RoleType.ASSISTANT

        if not role:
            raise ValueError(
                f"Could not resolve role type from message {message}. "
                f"Only support {HumanMessage.__name__} and {AIMessage.__name__}."
            )

        return self._chat_message(role=role, content=content)

    @abstractmethod
    def _chat_message(
            self,
            role: RoleType,
            content: str,
    ) -> ChatMessage | J2ChatMessage:
        pass

    @abstractmethod
    def call(self, client: Any, **params: Any) -> BaseMessage:
        pass

    def _get_system_message_from_message(self, message: BaseMessage) -> str:
        if not isinstance(message.content, str):
            raise ValueError(
                f"System Message must be of type str. Got {type(message.content)}"
            )

        return message.content


class J2Chat(Chat):

    def _chat_message(
            self,
            role: RoleType,
            content: str,
    ) -> J2ChatMessage:
        return J2ChatMessage(role=role, text=content)

    def call(self, client: Any, **params: Any) -> BaseMessage:
        response = client.chat.create(**params)
        outputs = response.outputs
        return AIMessage(content=outputs[0].text)


class JambaChatCompletions(Chat):

    def _chat_message(
            self,
            role: RoleType,
            content: str,
    ) -> ChatMessage:
        return ChatMessage(role=role, content=content)

    def call(self, client: Any, **params: Any) -> BaseMessage:
        response = client.chat.completions.create(**params)
        choices = response.choices
        return AIMessage(content=choices[0].message.content)