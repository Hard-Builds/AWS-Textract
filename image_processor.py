import base64
import io

from PIL import Image


class ImageProcessor:

    @staticmethod
    def convert_image_to_bw_base64(base64_string):
        try:
            if base64_string.startswith("data:image"):
                base64_string = base64_string.split(",")[1]

            image_data = base64.b64decode(base64_string)

            with Image.open(io.BytesIO(image_data)) as image:
                bw_image = image.convert("L")

                buffered = io.BytesIO()
                bw_image.save(buffered, format="PNG")

                bw_base64_string = buffered.getvalue()

            return bw_base64_string

        except Exception as e:
            print(f"Error converting image to black and white: {e}")
            return None
