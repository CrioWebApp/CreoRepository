import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework.response import Response
from rest_framework.views import APIView, status
from api.serializers import DataRequestSerializer


logger = logging.getLogger(__name__)

class DataValidation(APIView):
    def get_request_ip(self, request_meta):
        logger.info('Start IP validation')
        return request_meta[
            'HTTP_X_REAL_IP' if 'HTTP_X_REAL_IP' in request_meta else 'HTTP_X_CLIENT_IP'
        ]

    def dictfetchall(self, cursor):
        """
        Return all rows from a cursor as a dict.
        Assume the column names are unique.
        """
        columns = [col[0] for col in cursor.description]
        dictfetchall = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return dictfetchall

    def call_procedure(self, cursor, sql_request, params):
        """
        Returns response with requested fields.
        Returns response with http status code taken from server
        if status code greater than 0.
        """
        cursor.execute(sql_request, params)
        while True:
            logger.debug(cursor.description)
            if 'return_status' in cursor.description[0]:
                return_status = cursor.fetchval()
                logger.debug(f'return_status - {return_status}')
                status_code = {
                    403: status.HTTP_403_FORBIDDEN,
                    500: status.HTTP_500_INTERNAL_SERVER_ERROR,
                }
                if return_status:
                    return Response(status=status_code[return_status])
            else:
                result_fields = self.dictfetchall(cursor)
            if not cursor.nextset():
                break
            logger.debug(f'result_fields - {result_fields}')
        return Response(result_fields)

    def post(self, request):
        logger.setLevel(logging.INFO)
        conshandler = logging.StreamHandler()
        conshandler.setLevel(logging.DEBUG)
        fmtstr = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
        fmtdate = '%H:%M:%S'
        formater = logging.Formatter(fmtstr, fmtdate)
        conshandler.setFormatter(formater)
        logger.addHandler(conshandler)
        
        logger.info(f'Data validation has been started')

        try:
            request_ip = self.get_request_ip(request.META)
            logger.info(f'Request IP - {request_ip}')
        except KeyError:
            logger.exception('Meta key error')
            return Response('IP can not be recieved',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = DataRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        parameters = serializer.validated_data['Parameters']
        
        params = (parameters['id'],
                  parameters['phone_number'],
                  parameters['email'],
                  parameters['persons_identity_card1'],
                  parameters['persons_identity_card2'],
                  parameters['application_date'],
                  request_ip,
                  serializer.validated_data['Type'])

        sql_request = '''declare @ret_status int;
                         exec @ret_status=spap_req_verif %s,%s,%s,%s,%s,%s,%s,%s;
                         select 'return_status' = @ret_status;'''
        logger.debug(f'sql_request --- {sql_request}')

        try:
            with connection.cursor() as cursor:
                return self.call_procedure(cursor, sql_request, params)
        except Exception as e:
            logger.exception(e)
            return Response('Procedure_error',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            connection.close()
        
