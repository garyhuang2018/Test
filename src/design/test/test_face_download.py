# encoding= utf-8
#__author__= gary
import json
from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_faces(self):
        # Make GET request to retrieve face URLs
        response = self.client.get("/dev/face-list?zoneCode=5588&page=10&size=200")
        faces = json.loads(response.content)
        urls = [item['faceUrl'] for item in faces['data']]

        print(len(urls))
        # Iterate through URLs and download face data
        for url in urls:
            self.client.get(url)
