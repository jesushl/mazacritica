from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

class LocalFrontendCorsTests(APITestCase):
    @override_settings(DEBUG=True)
    def test_local_vite_origin_can_read_the_api(self):
        response = self.client.options(
            '/notes/',
            HTTP_ORIGIN='http://127.0.0.1:5173',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='authorization,content-type',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response['Access-Control-Allow-Origin'], 'http://127.0.0.1:5173')
        self.assertIn('authorization', response['Access-Control-Allow-Headers'])

    @override_settings(DEBUG=False)
    def test_cors_stays_off_outside_local_debug(self):
        response = self.client.get('/notes/', HTTP_ORIGIN='http://127.0.0.1:5173')
        self.assertNotIn('Access-Control-Allow-Origin', response)
