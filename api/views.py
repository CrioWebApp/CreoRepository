import logging

from django.conf import settings
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

    def call_procedure(self, proc_name, db_name, params):
        """
        Fetch requested fields and return status
        """
        with connections[db_name].cursor() as cursor:
            params_string = ','.join((['%s'] * len(params)))
            sql_request = f'''DECLARE @ret_status int;
                              EXEC @ret_status={proc_name} {params_string};
                              SELECT 'return_status' = @ret_status;'''
            logger.debug(f'sql_request --- {sql_request % params}')
            result_fields = {}
            cursor.execute(sql_request, params)
            while True:
                logger.debug(f'cursor_descr ---- {cursor.description}')
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
        return db_name if db_name else 'default'

    def post(self, request):
        logger.info(f'Data validation has been started')

        api_response = {
            'results': list(),
            'errors': list(),
        }
        api_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        try:
            request_ip = self.get_request_ip(request.META)
            logger.info(f'Request IP - {request_ip}')
            request_token = request.META['HTTP_AUTHORIZATION'].split()[-1]
            logger.debug(f'Request token - {request_token}')
        except KeyError as error:
            logger.exception(error)
            api_response['errors'].append('Meta key error')
            return Response(api_response, status=api_status)

        serializer = DataRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        parameters = serializer.validated_data['Parameters']
        
        params = (parameters['application_id'],
                  parameters['PhoneNumber'],
                  parameters['PhoneNumber1'],
                  parameters['PhoneNumber2'],
                  parameters['Email'],
                  parameters['PersonIdentityCard1'],
                  parameters['PersonIdentityCard'],
                  parameters['PersonIdentityCard2'],
                  parameters['Surname'],
                  parameters['FirstName'],
                  parameters['BornDate'],
                  parameters['application_date'],
                  request_ip,
                  serializer.validated_data['Type'],
                  parameters['mode'],
                  serializer.validated_data['MethodName'],
                  request_token)

        api_response = {
            'results': list(),
            'errors': list(),
        }
        api_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        try:
            db_name = self.fetch_db_name_by_ip(request_ip)
            proc_response, proc_status = self.call_procedure(settings.SQL_PROCEDURE,
                                                             db_name,
                                                             params)
            api_response['results'] = proc_response
            api_status = proc_status if proc_status else status.HTTP_200_OK
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
