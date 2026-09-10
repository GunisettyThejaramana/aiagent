import asyncio
import base64
import httpx

from app.config import settings


D_ID_API_URL = "https://api.d-id.com"


class AvatarService:

    def __init__(self):
        self.api_key = settings.D_ID_API_KEY
        self.source_url = settings.AVATAR_SOURCE_URL

    def _headers(self):
        if not self.api_key:
            raise RuntimeError(
                "D_ID_API_KEY is not configured."
            )

        encoded = base64.b64encode(
            self.api_key.encode("utf-8")
        ).decode("utf-8")

        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json"
        }

    async def create_talk(
        self,
        text: str,
        language: str = "en-US"
    ):

        if not self.api_key:
            raise RuntimeError(
                "D_ID_API_KEY is missing in .env"
            )

        if not self.source_url:
            raise RuntimeError(
                "AVATAR_SOURCE_URL is missing in .env"
            )

        voice_map = {
            "en-US": "en-US-JennyNeural",
            "hi-IN": "hi-IN-SwaraNeural",
            "ta-IN": "ta-IN-PallaviNeural"
        }

        voice_id = voice_map.get(
            language,
            "en-US-JennyNeural"
        )

        payload = {
            "source_url": self.source_url,

            "script": {
                "type": "text",
                "input": text,
                "provider": {
                    "type": "microsoft",
                    "voice_id": voice_id
                }
            },

            "config": {
                "fluent": True,
                "pad_audio": 0
            }
        }

        headers = self._headers()

        async with httpx.AsyncClient(
            timeout=60
        ) as client:

            response = await client.post(
                f"{D_ID_API_URL}/talks",
                headers=headers,
                json=payload
            )

            if response.status_code not in (
                200,
                201
            ):
                raise RuntimeError(
                    f"D-ID error: "
                    f"{response.status_code} "
                    f"{response.text}"
                )

            data = response.json()

            talk_id = data.get("id")

            if not talk_id:
                raise RuntimeError(
                    "D-ID did not return a talk ID."
                )

            # --------------------------------------------------
            # Wait for video generation
            # --------------------------------------------------

            for _ in range(60):

                await asyncio.sleep(2)

                status_response = await client.get(
                    f"{D_ID_API_URL}/talks/{talk_id}",
                    headers=headers
                )

                if status_response.status_code != 200:
                    continue

                status_data = (
                    status_response.json()
                )

                status = status_data.get(
                    "status"
                )

                if status == "done":

                    result_url = (
                        status_data.get(
                            "result_url"
                        )
                    )

                    if not result_url:
                        raise RuntimeError(
                            "D-ID completed the video "
                            "but no result URL was returned."
                        )

                    return {
                        "success": True,
                        "talk_id": talk_id,
                        "video_url": result_url
                    }

                if status in (
                    "error",
                    "failed"
                ):

                    raise RuntimeError(
                        f"D-ID avatar generation failed: "
                        f"{status_data}"
                    )

            raise RuntimeError(
                "D-ID avatar generation timed out."
            )


avatar_service = AvatarService()