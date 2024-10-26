import base64
import re
from collections import defaultdict
from typing import Optional

import boto3

from image_processor import ImageProcessor


class OCRExtractor:
    def __init__(self):
        self.client = boto3.client('textract')
        self.results = {
            "amount": None,
            "transaction_id": None
        }

    def process_document(self, file_data):
        try:
            # Detect document text using AWS Textract
            result_json = self.client.detect_document_text(
                Document={'Bytes': file_data})
            text_blocks = result_json["Blocks"]
            print(f"result : {result_json['Blocks']}")

            self.__print_text_blocks(text_blocks)
            self.__check_confidence(text_blocks)

            return text_blocks
        except Exception as e:
            print(f"Error processing document: {e}")
            raise

    def __print_text_blocks(self, text_blocks):
        text_map = defaultdict(list)
        for block in text_blocks:
            if "Text" not in block:
                continue

            text = block["Text"]
            block_type = block["BlockType"]
            text_map[block_type].append(text)

        print(f"text_map : {text_map}")

    def __check_confidence(self, text_blocks):
        conf_map = defaultdict(list)
        for block in text_blocks:
            if "Text" not in block:
                continue
            conf = block["Confidence"]
            text = block.get("Text")
            if float(conf) > 95:
                conf_map["High"].append(text)
            elif float(conf) > 85:
                conf_map["Medium"].append(text)
            else:
                conf_map["Low"].append(text)
        print(f"conf_map : {conf_map}")

    def extract_results(self, file_data):

        print()
        print(f"File Name : {file_data.get('file_name')}")
        data = file_data.get("image")

        """Processing the image as is"""
        im_bytes = base64.b64decode(data)
        self.__extract_helper(im_bytes)

        if None in self.results.values():
            print("Else-2")
            """Converting image to black and white for better results"""
            im_bytes = ImageProcessor.convert_image_to_bw_base64(data)
            self.__extract_helper(im_bytes)

        return self.results
    
    def __extract_helper(self, im_bytes):
        text_blocks = self.process_document(im_bytes)

        """Iterating words to find required vals"""
        self.iterate_words_to_extract_fields(text_blocks)

        if self.results["amount"] is None:
            print("Else")
            self.results["amount"] = self.extract_amount(text_blocks)

        return self.results

    def iterate_words_to_extract_fields(self, text_blocks):
        for block in text_blocks:
            if block["BlockType"] != "WORD":
                continue

            text = block["Text"]
            cleaned_text = str(text).replace(" ", "")

            if "₹" in text:
                self.results["amount"] = self.extract_rupee(cleaned_text)
            else:
                transaction_id = self.extract_transaction_id(cleaned_text)
                if transaction_id:
                    self.results["transaction_id"] = transaction_id

    @staticmethod
    def extract_rupee(text: str) -> Optional[float]:
        try:
            amount_match = re.search(r'₹\s*([\d,]+(?:\.\d{2})?)', text)
            if amount_match:
                amount_str = amount_match.group(1).replace(",", "").replace(
                    " ", "")
                return float(amount_str)
            return None
        except Exception as exc:
            print(f"Error in extract_rupee: {exc}")
            return None

    @staticmethod
    def extract_transaction_id(text: str) -> Optional[str]:
        try:
            pattern = r'^\d{12}$'
            match = re.match(pattern, text)
            return match.group(0) if match else None
        except Exception as exc:
            print(f"Error in extract_transaction_id: {exc}")
            return None

    def extract_amount(self, text_blocks):
        for block in text_blocks:
            if block["BlockType"] not in ("WORD", "LINE"):
                continue

            try:
                text = block["Text"]
                text = str(text).lower()

                if "amount" in text:
                    amount = re.search(r'amount[\s:]*([\d,]+(?:\.\d{2})?)',
                                       text, re.IGNORECASE)
                    if amount:
                        return amount.group(1)
                else:
                    amount = re.search(
                        r'\d{1,3}(?:,\d{1,3})+(?:\.\d{2})?\b|\d+\.\d{2}\b',
                        text)
                    if amount:
                        return amount.group(0)
            except Exception as exc:
                print(f"Error : {exc}")
                return None
