import re
from csv import excel_tab
from typing import Any, Optional

import boto3


class OCRExtractor:
    def __init__(self, file_data: Any):
        self.file_data = file_data
        self.client = boto3.client('textract')
        self.text_blocks = []
        self.results = {
            "amount": None,
            "transaction_id": None
        }

    def process_document(self):
        try:
            # Detect document text using AWS Textract
            result_json = self.client.detect_document_text(
                Document={'Bytes': self.file_data})
            self.text_blocks = result_json["Blocks"]
            print(f"text_blocks : {self.text_blocks}")
        except Exception as e:
            print(f"Error processing document: {e}")
            raise

    def extract_results(self):
        """Iterating words to find required vals"""
        self.iterate_words_to_extract_fields()

        if self.results["amount"] is None:
            self.results["amount"] = self.extract_amount()

        return self.results

    def iterate_words_to_extract_fields(self):
        for block in self.text_blocks:
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

    def extract_amount(self):
        for block in self.text_blocks:
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
                        r'\d{1,3}(?:,\d{1,3})+(?:\.\d{2})?\b|\d+\.\d{2}\b', text)
                    if amount:
                        return amount.group(0)
            except Exception as exc:
                print(f"Error : {exc}")
                return None