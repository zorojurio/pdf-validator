from asn1crypto import cms
from accounts.services.pbs_validation_service import ValidatePublicKey
from signature_validator.services.pdf_validation_service import PdfSignatureValidator

from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.hazmat.primitives import serialization


class PublicKeyExtractor:
    def __init__(self, file_name, data):
        self.file_name = file_name
        self.cert_data = data
        self.public_key = None

    def get_public_key_from_cer(self):
        cert = x509.load_der_x509_certificate(self.cert_data, default_backend())
        public_key_bytes = cert.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        public_key_string = public_key_bytes.decode("utf-8")
        self.public_key = public_key_string

    def extract_public_key_from_p7c(self):
        content = cms.ContentInfo.load(self.cert_data).native
        certificate = content["content"]["certificates"][0]
        pbk, pbk_str = PdfSignatureValidator.get_public_key_from_certification(
            certificate
        )
        self.public_key = pbk_str

    def extract_public_key_from_fdf(self):
        n = self.cert_data.find(b"/Certs[")
        start = self.cert_data.find(b"(", n)
        end = self.cert_data.find(b")]/Type/Import>>", start)
        cert_data = self.cert_data[start + 1 : end]
        edited = (
            cert_data.replace(b"\\r", b"\r")
            .replace(b"\\n", b"\n")
            .replace(b"\\\\", b"\\")
            .replace(b"\\\r", b"")
            .replace(b"\\(", b"(")
            .replace(b"\\)", b")")
        )
        cert = x509.load_der_x509_certificate(edited, default_backend())
        public_key_bytes = cert.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        public_key_string = public_key_bytes.decode("utf-8")
        self.public_key = public_key_string

    def get_public_key(self):
        if self.file_name.endswith(".cer"):
            self.get_public_key_from_cer()
        elif self.file_name.endswith(".p7c"):
            self.extract_public_key_from_p7c()
        elif self.file_name.endswith(".fdf"):
            self.extract_public_key_from_fdf()
        else:
            return "Invalid file type"
        validator = ValidatePublicKey(self.public_key)
        validator.trim_key()
        return validator.key
