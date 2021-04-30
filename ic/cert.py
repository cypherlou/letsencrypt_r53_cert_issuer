import os.path
import sewer
import sewer.dns_providers.route53
import sewer.client
import sewer.crypto
import OpenSSL
import ssl
import socket
import datetime
import logging

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class Cert(object):
    def __init__(self, server: str, logger: logging.Logger) -> None:
        self.log: logging.Logger = logger
        self.server: str = server
        self.port: int = 443
        self.expiration_date: datetime.datetime = None
        self.expires_in: int = 0
        self.error: bool = True

    def get_expiration(self, domain: str):

        if not self.server:
            self.server = domain

        context = ssl.create_default_context()
        self.log.info("connecting to {}:{}".format(self.server, self.port))

        self.error = True
        try:
            sock = socket.create_connection((self.server, self.port))
        except Exception as e:
            self.log.error(e)
            return

        self.log.info("getting certificate for {}".format(domain))
        try:
            ssl_socket = context.wrap_socket(sock, server_hostname=domain)
        except Exception as e:
            self.log.error(e)
            return

        der_cert = ssl_socket.getpeercert(True)
        pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)

        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, pem_cert)
        self.expiration_date = datetime.datetime.strptime(
            x509.get_notAfter().decode(), "%Y%m%d%H%M%SZ"
        )
        self.expires_in = (self.expiration_date - datetime.datetime.now()).days
        self.log.info(
            "certificate expires on {}, {} days away".format(
                self.expiration_date, self.expires_in
            )
        )
        self.error = False


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class IssueCert(object):
    def __init__(self, logger: logging.Logger):

        self.log: logging.Logger = logger
        self.domain: str = ""
        self.output_pem: bool = False
        self.key_file: str = ".lets_encrypt.pem"
        self.account_key: str = ""
        self.key_type: str = "rsa3072"
        self.email: str = ""
        self.new_account: bool = True
        self.error: bool = True

    # -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -
    def issue_cert(self, domain: str) -> None:

        if not os.environ.get("AWS_SECRET_ACCESS_KEY") or not os.environ.get(
            "AWS_ACCESS_KEY_ID"
        ):
            self.log.warning(
                "AWS_SECRET_ACCESS_KEY and/or AWS_ACCESS_KEY_ID not set. Sewer uses environment variables to access AWS R53"
            )
            return

        filename, extension = os.path.splitext(self.key_file)
        self.account_key_file = "{}_account{}".format(filename, extension)
        self.certificate_key_file = "{}_certificate{}".format(filename, extension)

        if os.path.exists(self.key_file):
            self.log.info("loading Let's Encrypt account keys")
            self.account = sewer.crypto.AcemAccount.read_pem(self.account_key_file)
            self.certificate = sewer.crypto.read_pem(self.certificate_key_file)
            self.new_account = False
        else:
            self.log.info("creating Let's Encrypt account keys")
            self.account = sewer.crypto.AcmeAccount.create(self.key_type)
            self.certificate = sewer.crypto.AcmeKey.create(self.key_type)

        dns_provider = sewer.dns_providers.route53.Route53Dns()

        if domain[:4] == "www.":
            self.naked_domain = domain[4:]
        else:
            self.naked_domain = domain

        if not self.email:
            self.email = "info@{}".format(self.naked_domain)

        self.log.info("making a cert request for {}".format(self.naked_domain))

        try:
            client = sewer.client.Client(
                domain_name="*.{}".format(self.naked_domain),
                domain_alt_names=[self.naked_domain],
                contact_email=self.email,
                provider=dns_provider,
                # LOG_LEVEL = "DEBUG",
                LOG_LEVEL="INFO",
                account=self.account,
                cert_key=self.certificate,
                is_new_acct=self.new_account,
            )

        except Exception as e:
            self.log.warning(
                "failed to request certificate from Let's Encrypt server: {}".format(e)
            )
            return

        self.log.info("requesting certificate for {}".format(self.naked_domain))
        self.pem = "{}\n{}".format(
            client.get_certificate(), self.certificate.to_pem().decode()
        )

        self.log.info("writing account credentials to {}".format(self.account_key_file))
        self.account.write_pem(self.account_key_file)
        self.log.info("writing certificate key to {}".format(self.certificate_key_file))
        self.certificate.write_pem(self.certificate_key_file)
        self.error = False
