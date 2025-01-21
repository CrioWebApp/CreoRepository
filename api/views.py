import logging
from http import HTTPStatus

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

    def fetch_db_params_by_ip(self, request_ip):
        with connections['default'].cursor() as cursor:
            sql_request = f'''select top 1 db,proc_name,profile_id
                              from dbo.client_v
                              where IP=%s'''
            logger.debug(f'sql_request --- {sql_request}')
            cursor.execute(sql_request, (request_ip,))
            result = cursor.fetchall()
            db_name, proc_name, profile_id = result[0]
            logger.info(f'''db_name - {db_name},
                            proc_name - {proc_name}, 
                            profile_id - {profile_id}''')
            db_name = db_name if db_name else 'default'
            return db_name, proc_name, profile_id

    def search_status(self, number):
        for status in HTTPStatus:
            description = 'No description'
            if status.value == number:
                description = f'{number} {status.description}'
                break
        return description

    def get_status_and_message(self, is_entry, api_status):
        if not api_status == 200:
            return 'ERROR', self.search_status(api_status)
        elif is_entry:
            return 'HIT', 'data found'
        return 'NO_HIT', 'data not found'

    def get_api_response(self, profile_id, proc_response, api_status,
                         conn_errors, method_name):
        if profile_id == 1:
            return {
                'results': proc_response,
                'errors': conn_errors,
            }
        elif profile_id == 2:
            status, message = self.get_status_and_message(len(proc_response), api_status)
            results = proc_response[0] if len(proc_response) == 1 else proc_response
            if status == 'ERROR':
                results = None
            return {
                "methodName": method_name,
                "status": status,
                "message": message,
                "results": results,
            }
        else:
            conn_errors.append('No profile_id')
            return {
                'results': [],
                'errors': conn_errors,
            }

    def make_low_letters_keys(self, request_data):
        lower_request_data = {key.lower(): value\
            for key, value in request_data.items()}
        lower_request_data['parameters'] = {key.lower(): value\
            for key, value in lower_request_data['parameters'].items()}
        return lower_request_data

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

        request_data = self.make_low_letters_keys(request.data)

        serializer = DataRequestSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        print(serializer.validated_data)

        parameters = serializer.validated_data['parameters']
        method_name = serializer.validated_data['methodname']
        
        params = (parameters['application_id'],
                  parameters['phonenumber'],
                  parameters['phonenumber1'],
                  parameters['phonenumber2'],
                  parameters['email'],
                  parameters['personidentitycard1'],
                  parameters['personidentitycard'],
                  parameters['personidentitycard2'],
                  parameters['surname'],
                  parameters['firstname'],
                  parameters['borndate'],
                  parameters['application_date'],
                  request_ip,
                  serializer.validated_data['type'],
                  parameters['mode'],
                  method_name,
                  request_token)

        logger.debug(f'params - {params}')

        conn_errors = list()
        api_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        profile_id = 0
        proc_response = []
        try:
            db_name, proc_name, profile_id = self.fetch_db_params_by_ip(request_ip)
            proc_response, proc_status = self.call_procedure(proc_name,
                                                             db_name,
                                                             params)
            api_status = proc_status if proc_status else status.HTTP_200_OK
        except ConnectionDoesNotExist as error:
            logger.exception(error)
            conn_errors.append('DB access error')
        except PermissionError as error:
            logger.exception(error)
            conn_errors.append('Wrong IP')
            api_status = status.HTTP_403_FORBIDDEN
        except Exception as error:
            logger.exception(error)
            conn_errors.append('Procedure_error')
        finally:
            connections.close_all()
            api_response = self.get_api_response(profile_id,
                                                 proc_response,
                                                 api_status,
                                                 conn_errors,
                                                 method_name)
            return Response(api_response, status=api_status)
