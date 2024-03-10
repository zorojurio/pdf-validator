import string

from cryptography.hazmat.primitives import serialization

from validator.logger import module_logger

logger = module_logger(__name__)


class ValidatePublicKey:
    def __init__(self, key):
        self.key = key

    def is_hex(self) -> bool:
        hex_digits = set(string.hexdigits).union({" "})
        # if s is long, then it is faster to check against a set
        return all(c in hex_digits for c in self.key)

    def check_and_get_public_key(self) -> bool:
        try:
            if self.is_hex():
                binary_data = bytes.fromhex(self.key)
                public_key = serialization.load_der_public_key(binary_data)
                public_key_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                self.key = public_key_pem.decode()
                logger.info(f"Public key: {self.key} is a valid hex public key.")
                is_valid_pk = True
            else:
                is_valid_pk = self.is_valid_pem_public_key()
            self.trim_key()
            return is_valid_pk
        except Exception as e:
            logger.error(f"Error while validating public key: {e}")
            return False

    def is_valid_pem_public_key(self):
        try:
            # Load the PEM public key
            serialization.load_pem_public_key(self.key.encode())
            logger.info(f"Public key: {self.key} is a valid pem public key.")
            return True
        except ValueError:
            logger.info(f"Public key: {self.key} is invalid pem public key.")
            return False

    def trim_key(self):
        self.key = (
            self.key.replace("-----BEGIN PUBLIC KEY-----", "")
            .replace("-----END PUBLIC KEY-----", "")
            .replace("\n", "")
            .strip()
        )
