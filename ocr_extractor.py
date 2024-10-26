import re
from typing import Any, Optional

import boto3


class OCRExtractor:
    def __init__(self, file_data: Any):
        self.file_data = file_data
        self.client = boto3.client('textract')

    def process_document(self):
        try:
            # Detect document text using AWS Textract
            result_json = self.client.detect_document_text(
                Document={'Bytes': self.file_data})
            print(f"result_json : {result_json['Blocks']}")
            return result_json["Blocks"]
        except Exception as e:
            print(f"Error processing document: {e}")
            raise

    def get_extracted_data(self) -> dict:
        text_blocks = self.process_document()
        amount = self.extract_amount(text_blocks)
        transaction_id = self.extract_transaction_id(text_blocks)

        return {
            "amount": amount,
            "transaction_id": transaction_id
        }

    def extract_amount(self, text_blocks):
        amount = None
        for block in text_blocks:
            if block["BlockType"] != "WORD":
                continue

            text = block["Text"]
            cleaned_text = str(text).replace(" ", "")

            if "₹" in text:
                amount = self.extract_rupee(cleaned_text)

        if amount is None:
            amount = self.extract_fallback_amount(text_blocks)

        if amount:
            amount = str(amount)

        return amount

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


    def extract_transaction_id(self, text_blocks):
        for block in text_blocks:
            if block["BlockType"] != "WORD":
                continue
            try:
                text = block["Text"]
                cleaned_text = str(text).replace(" ", "")

                pattern = r'^\d{12}$'
                match = re.match(pattern, cleaned_text)

                if match:
                    return match.group(0) if match else None
            except Exception as exc:
                print(f"Error in extract_transaction_id: {exc}")
                return None

    def extract_fallback_amount(self, text_blocks):
        for block in text_blocks:
            if block["BlockType"] not in ("WORD", "LINE"):
                continue

            try:
                text = block["Text"]
                text = str(text).lower()

                amount = re.search(r'amount[\s:]*([\d,]+(?:\.\d{2})?)',
                                   text, re.IGNORECASE)
                if amount:
                    return amount.group(1)

                amount = re.search(
                    r'\d{1,3}(?:,\d{1,3})+(?:\.\d{2})?\b|\d+\.\d{2}\b',
                    text)
                if amount:
                    return amount.group(0)

                '''
                cleaned_text = str(text).replace(" ", "")
                cleaned_text = cleaned_text.replace(",", "")
                if not cleaned_text.replace(".", "", 1).isdigit():
                    continue
                amount = re.search(
                    r"\d{1,3}(?:,\d{1,3})*(?:\.\d{2})?\b|\d+\.\d{2}\b",
                    cleaned_text)
                if amount:
                    return amount.group(0)
                '''
            except Exception as exc:
                print(f"Error : {exc}")
                return None