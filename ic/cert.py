import os.path
import sewer
import sewer.dns_providers.route53
import sewer.client
import sewer.crypto
import OpenSSL
import ssl
import socket
import datetime

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class Cert( object ):
    def __init__( self, server:str, logger )->None:
        self.log = logger
        self.server = server
        self.port = 443
        self.expiration_date = None
        self.expires_in = 0

    def get_expiration( self, domain:str ):

        if not self.server:
            self.server = domain

        context = ssl.create_default_context()
        self.log.info( "connecting to {}:{}".format( self.server, self.port) )
        with socket.create_connection((self.server, self.port)) as sock:
            self.log.info( "getting certificate for {}".format( domain ) )
            with context.wrap_socket(sock, server_hostname=domain) as sslsock:

                der_cert = sslsock.getpeercert(True)
                pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)

                x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, pem_cert)
                self.expiration_date = datetime.datetime.strptime( x509.get_notAfter().decode(), '%Y%m%d%H%M%SZ' )
                self.expires_in = (self.expiration_date - datetime.datetime.now()).days
                self.log.info( "certificate expires on {}, {} days away".format( self.expiration_date, self.expires_in ) )

    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class IssueCert( object ):

    def __init__( self, logger ):

        self.log = logger
        self.domain = None
        self.output_pem = False
        self.key_file = '.lets_encrypt.pem'
        self.account_key = None
        self.key_type='rsa3072'
        self.email = ''
        self.new_account = True

    # -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -
    def issue_cert( self, domain:str ) -> None:

        if not os.environ.get( 'AWS_SECRET_ACCESS_KEY' ) or not os.environ.get( 'AWS_ACCESS_KEY_ID' ):
            self.log.warning( "AWS_SECRET_ACCESS_KEY and/or AWS_ACCESS_KEY_ID not set. Sewer uses environment variables to access AWS R53" )
            return

        filename, extension = os.path.splitext( self.key_file )
        self.account_key_file = "{}_account{}".format( filename, extension )
        self.certificate_key_file = "{}_certificate{}".format( filename, extension )
        
        if os.path.exists( self.key_file ):
            self.log.info( "loading Let's Encrypt account keys" )
            self.account = sewer.crypto.AcemAccount.read_pem(self.account_key_file)
            self.certificate = sewer.crypto.read_pem(self.certificate_key_file)
            self.new_account = False
        else:
            self.log.info( "creating Let's Encrypt account keys" )
            self.account = sewer.crypto.AcmeAccount.create(self.key_type)
            self.certificate = sewer.crypto.AcmeKey.create(self.key_type)

        dns_provider = sewer.dns_providers.route53.Route53Dns()

        if domain[:4] == 'www.':
            self.naked_domain = domain[4:]
        else:
            self.naked_domain = domain

        if not self.email:
            self.email = "info@{}".format( self.naked_domain )
            
        self.log.info( "making a cert request for {}".format( self.naked_domain ) )

        try:
            client = sewer.client.Client(
                domain_name = "*.{}".format( self.naked_domain ),
                domain_alt_names=[ self.naked_domain ],
                contact_email = self.email,
                provider = dns_provider,
                # LOG_LEVEL = "DEBUG",
                LOG_LEVEL = "INFO",
                account=self.account,
                cert_key=self.certificate,
                is_new_acct = self.new_account,
            )

        except Exception as e:
            self.log.warning( "failed to request certificate from Let's Encrypt server: {}".format( e ) )
            return

        self.log.info("requesting certificate for {}".format(self.naked_domain) )
        self.pem = client.get_certificate()

        self.log.info( "writing account credentials to {}".format( self.account_key_file) )
        self.account.write_pem( self.account_key_file )
        self.log.info( "writing certificate key to {}".format( self.certificate_key_file ) )
        self.certificate.write_pem( self.certificate_key_file )
