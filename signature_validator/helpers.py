import hashlib

from cryptography.hazmat.primitives import serialization

from asn1crypto import cms
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from dateutil.parser import parse
from pypdf import PdfReader

from validator.logger import module_logger


logger = module_logger(__name__)


class PdfSignatureValidator:
    """Read from the file and validate the signature of the PDF file."""

    def __init__(self, file_path):
        self.file_path = file_path
        self.pdf_bytes = None
        self.is_signed = False
        self.is_hashes_valid = False
        self.is_signatures_valid = False
        self.validated_data_list = None

    def __dict__(self):
        return {
            'file_path': self.file_path,
            'is_signed': self.is_signed,
            'is_hashes_valid': self.is_hashes_valid,
            'is_signatures_valid': self.is_signatures_valid,
            'validated_data_list': self.validated_data_list
        }

    def get_pdf_bytes(self):
        """Read the PDF file in binary and save bytes in a variable."""
        with open(self.file_path, 'rb') as file:
            self.pdf_bytes = file.read()

    @staticmethod
    def get_public_key_from_certification(certification) -> tuple[rsa.RSAPublicKey, str]:
        """Get the public key from the certification using n and e."""
        n = certification['tbs_certificate']['subject_public_key_info']['public_key']['modulus']
        e = certification['tbs_certificate'][
            'subject_public_key_info']['public_key']['public_exponent']
        public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())

        pem_encoded_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return public_key, pem_encoded_public_key.decode('utf-8')

    def validate(self):
        self.get_pdf_bytes()
        reader = PdfReader(self.file_path)
        fields = reader.get_fields()
        if fields is None:
            logger.warning("Signatures not Found")
            return
        else:
            self.is_signed = True
        validated_data_list = []
        for k, v in fields.items():
            logger.info(f"\nProcessing Signature {k}")
            value = v['/V']
            signing_time = parse(value['/M'][2:].strip("'").replace("'", ":"))
            logger.info(f"Signing time: {signing_time}")
            br = value['/ByteRange']
            logger.info(len(self.pdf_bytes))

            orginal_data_before_signatures, signature_data_in_bytes = (
                self.extract_signature_and_orginal_data_from_byte_range(br)
            )
            verified_data = {
                'signature_name': k,
                'signing_time': signing_time
            }
            try:
                self.verify_hash_integrity(
                    signature_data_in_bytes,
                    orginal_data_before_signatures,
                    verified_data
                )
            except Exception as error:
                logger.info(error)
                logger.info("Invalid Signature")
            validated_data_list.append(verified_data)
        self.validated_data_list = validated_data_list
        self.check_validity_whole_document()

    def check_validity_whole_document(self):
        """Check the validity of the signature."""
        is_valid_hash = False
        for signature in self.validated_data_list:
            # if hash is not valid for any signature, the whole document's hash is not valid
            if 'hash_valid' in signature and signature['hash_valid']:
                is_valid_hash = True
            else:
                is_valid_hash = False
                break
        self.is_hashes_valid = is_valid_hash

        is_valid_signature = False
        # if sign is not valid for any signature, the whole document's signature is not valid
        for signature in self.validated_data_list:
            # if sig is not valid for any signature, the whole document's sigs is not valid
            if 'signature_valid' in signature and signature['signature_valid']:
                is_valid_signature = True
            else:
                is_valid_signature = False
                break
        self.is_signatures_valid = is_valid_signature

    def extract_signature_and_orginal_data_from_byte_range(self, br):
        first_section = self.pdf_bytes[br[0]: br[0] + br[1]]
        second_section = self.pdf_bytes[br[2]: br[2] + br[3]]
        orginal_data_before_signatures = first_section + second_section
        signature_data = self.pdf_bytes[br[1] + 1: br[2] - 1]
        signature_data_in_bytes = bytes.fromhex(signature_data.decode('utf-8'))
        return orginal_data_before_signatures, signature_data_in_bytes

    @staticmethod
    def parse_pkcs7_signatures(signature_data: bytes):
        native_data = cms.ContentInfo.load(signature_data)
        content_info = native_data.native
        if content_info['content_type'] != 'signed_data':
            return None

        content = content_info['content']
        # each PKCS7 / CMS / CADES could have several signatures
        certificates = content['certificates']
        signer_infos = content['signer_infos']
        return signer_infos, native_data, certificates

    def verify_hash_integrity(
            self,
            signature_data_in_bytes: bytes,
            orginal_data_before_signatures,
            verified_data: dict
    ) -> dict:
        """Parse a PKCS7 / CMS / CADES signature"""

        signer_infos, native_data, certificates = self.parse_pkcs7_signatures(
            signature_data_in_bytes
        )
        for signer_info in signer_infos:
            # the sid key should point to the certificates collection

            sid = signer_info['sid']
            digest_algorithm = signer_info['digest_algorithm']['algorithm']
            message_digest = signer_info['signed_attrs'][2]['values'][0]
            hash_valid = self.check_hash_valid(
                orginal_data_before_signatures,
                digest_algorithm,
                message_digest
            )

            signature_algorithm = signer_info['signature_algorithm']['algorithm']
            signature_bytes = signer_info['signature']
            attr = native_data['content']['signer_infos'][0]['signed_attrs'].dump()
            sig_attributes = b'\x31' + attr[1:]

            cert = None
            for certification in certificates:
                if (
                        signer_info['sid']['serial_number'] ==
                        certification['tbs_certificate']['serial_number']
                ):
                    cert = certification
                    break
            public_key_obj, public_key_str = self.get_public_key_from_certification(cert)
            # sig_value_in_bytes = cert['signature_value']
            try:
                public_key_obj.verify(
                    signature_bytes,
                    sig_attributes,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                public_key_obj.recover_data_from_signature(
                    signature_bytes,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                is_valid_signature = True
            except InvalidSignature:
                is_valid_signature = False
            logger.info(f"Signature for {sid['serial_number']} is valid: {is_valid_signature}")
            verified_data.update({
                'serial_number': sid['serial_number'],
                'hash_valid': hash_valid,
                'signature_valid': is_valid_signature,
                'signed_by': sid['issuer']['common_name'],
                'email_of_signer': sid['issuer']['email_address'],
                'signature_algorithm': signature_algorithm,
                'digest_algorithm': digest_algorithm,
                'message_digest': message_digest,
                'public_key': public_key_str
            })
        return verified_data

    @staticmethod
    def check_hash_valid(orginal_data_before_signatures, digest_algorithm, message_digest):
        hash_signature = getattr(hashlib, digest_algorithm)(orginal_data_before_signatures).digest()
        logger.info(f"Calculated Hash and Message Digest are matching -> "
                    f"{hash_signature == message_digest}")
        return hash_signature == message_digest
