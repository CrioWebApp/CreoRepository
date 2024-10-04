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
        with connections[db_name].cursor() as cursor:
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
                    logger.debug(f'return_status - {return_status}')
                else:
                    result_fields = self.dictfetchall(cursor)
                    logger.debug(f'result_fields - {result_fields}')
                if not cursor.nextset():
                    break
        return result_fields, return_status

    def fetch_db_name_by_ip(self, request_ip):
        with connections['default'].cursor() as cursor:
            sql_request = f'''select db from client_v
                              where ip=%s'''
            logger.debug(f'sql_request --- {sql_request}')
            cursor.execute(sql_request, (request_ip,))
            db_name = cursor.fetchval()
            logger.info(f'db_name - {db_name}')
            if not db_name:
                raise PermissionError()
        return db_name

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
                  parameters['PersonIdentityCard2'],
                  parameters['application_date'],
                  request_ip,
                  serializer.validated_data['Type'],
                  parameters['mode'])

        api_response = {
            'results': list(),
            'errors': list(),
        }
        api_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        try:
            db_name = self.fetch_db_name_by_ip(request_ip)
            api_response['results'], return_status = self.call_procedure(db_name, params)
            api_status = return_status if return_status else status.HTTP_200_OK
        except ConnectionDoesNotExist as error:
            logger.exception(error)
            api_response['errors'].append('DB access error')
        except PermissionError as error:
            logger.exception(error)
            api_response['errors'].append('Wrong IP')
            api_status = status.HTTP_403_FORBIDDEN
        except Exception as error:
            logger.exception(error)
            api_response['errors'].append('Procedure_error')
        finally:
            connections.close_all()
            return Response(api_response, status=api_status)
