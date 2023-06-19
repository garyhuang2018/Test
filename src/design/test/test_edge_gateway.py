# encoding= utf-8
# __author__= gary
from locust import HttpUser, between, task
from matplotlib import pyplot as plt


from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 6)

    @task(4)
    def index(self):
        self.client.get("/dev/housing-struct-list?zoneCode=5588&page=0&size=9999")

    @task(3)
    def search(self):
        self.client.get("/dev/notice-list?zoneCode=5588&page=0&size=30&unitNo=010102")

    @task(2)
    def device_config(self):
        self.client.get("/dev/device-config?zoneCode=5588")

    @task
    def zone_authorizes(self):
        self.client.get("/dev/zone-authorizes?zoneCode = 5588 & devCode = a684ee954489 & devType = 14")
