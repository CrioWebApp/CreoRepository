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
        try:
            request_ip=request_meta[
                'HTTP_X_REAL_IP' if 'HTTP_X_REAL_IP' in request_meta else 'HTTP_X_CLIENT_IP'
            ]
        except KeyError:
            logger.exception('Meta key error')
            return Response('IP can not be recieved',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return request_ip

    def dictfetchall(self, cursor):
        """
        Return all rows from a cursor as a dict.
        Assume the column names are unique.
        """
        columns = [col[0] for col in cursor.description]
        print(columns)
        dictfetchall = [dict(zip(columns, row)) for row in cursor.fetchall()]
        print(dictfetchall)
        return dictfetchall

    def call_procedure(self, cursor, sql_request, params):
        """
        Return response with requested fields.
        Return response with exeption 500 if the procedure
        returns status greater than 0.
        """
        cursor.execute(sql_request, params)
        while True:
            print(cursor.description)
            if 'return_status' in cursor.description[0]:
                return_status = cursor.fetchval()
                print(return_status)
                if return_status:
                    return Response(return_status,
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                result_fields = self.dictfetchall(cursor)
            if not cursor.nextset():
                break
            print(cursor.description)
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

        request_ip = self.get_request_ip(request.META)
        logger.info(f'Request IP - {request_ip}')

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
        
        logger.info(f'sql_request --- {sql_request}')

        try:
            with connection.cursor() as cursor:
                return self.call_procedure(cursor, sql_request, params)
        except Exception as e:
            logger.exception(e)
            return Response('Procedure_error',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            connection.close()
        
