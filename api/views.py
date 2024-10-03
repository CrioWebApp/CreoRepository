import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import connections
from django.utils.connection import ConnectionDoesNotExist
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
        fethed_data = cursor.fetchall()
        return [dict(zip(columns, row)) for row in fethed_data]

    def call_procedure(self, db_name, params):
        """
        Fetch requested fields and return status
        """
        params_string = ','.join((['%s'] * len(params)))
        sql_request = f'''declare @ret_status int;
                          exec @ret_status=spap_req_verif {params_string};
                          select 'return_status' = @ret_status;'''
        logger.debug(f'sql_request --- {sql_request}')
        result_fields = {}
        cursor.execute(sql_request, params)
        while True:
            logger.debug(cursor.description)
            if 'return_status' in cursor.description[0]:
                return_status = cursor.fetchval()
                logger.debug(f'return_status - {result_fields}')
            else:
                result_fields = self.dictfetchall(cursor)
                logger.debug(f'result_fields - {result_fields}')
            if not cursor.nextset():
                break
        return result_fields, return_status

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
        
        params = (parameters['application_id'],
                  parameters['PhoneNumber'],
                  parameters['Email'],
                  parameters['PersonIdentityCard1'],
                  parameters['PersonIdentityCard'],
                  parameters['PersonIdentityCard2'],
                  parameters['application_date'],
                  request_ip,
                  serializer.validated_data['Type'])

        try:
            with connection.cursor() as cursor:
                proc_response, return_status = self.call_procedure(cursor, params)
                return Response({'results': proc_response},
                                status=return_status if return_status \
                                    else status.HTTP_200_OK)
        except Exception as e:
            logger.exception(e)
            return Response('Procedure_error',
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            connections.close_all()
            return Response(api_response, status=api_status)
