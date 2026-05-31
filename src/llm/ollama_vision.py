import base64
import requests
from PIL import Image
from pathlib import Path


class OllamaVisionClient:

    def __init__(self, model="qwen2.5vl:7b"):
        self.model = model
        self.url = "http://localhost:11434/api/chat"

    def _resize_image(self, image_path):
        image_path = Path(image_path)

        output_path = image_path.with_name(
            image_path.stem + "_small.jpg"
        )

        image = Image.open(image_path).convert("RGB")

        image.thumbnail((768, 768))

        image.save(
            output_path,
            format="JPEG",
            quality=70,
            optimize=True
        )

        return str(output_path)

    def _image_to_base64(self, image_path):
        small_path = self._resize_image(image_path)

        with open(small_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def ask_image(self, image_path, prompt):
        image_base64 = self._image_to_base64(image_path)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_base64]
                }
            ],
            "stream": False,
            "options": {
                "num_predict": 500,
                "temperature": 0.1,
                "num_ctx": 2048
            }
        }

        response = requests.post(
            self.url,
            json=payload,
            timeout=180
        )

        response.raise_for_status()

        data = response.json()

        return data["message"]["content"]