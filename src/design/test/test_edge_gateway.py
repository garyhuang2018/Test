# encoding= utf-8
# __author__= gary
from locust import HttpUser, between, task
from matplotlib import pyplot as plt


from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 8)

    @task
    def get_unit_status(self):
        self.client.get("/dev/unit-status?zoneCode=5588")

    @task
    def get_house_struct(self):
        self.client.get("/dev/housing-struct-list?zoneCode=5588&page=0&size=9999")

    @task
    def get_notice_list(self):
        self.client.get("/dev/notice-list?zoneCode=5588&page=0&size=30&unitNo=010102")

    @task
    def device_config(self):
        self.client.get("/dev/device-config?zoneCode=5588")

    @task
    def zone_authorizes(self):
        self.client.get("/dev/zone-authorizes?zoneCode=5588&devCode=a684ee954489&devType=14")

    @task
    def dev_reg(self):
        self.client.post("/dev/dev-reg?zoneCode=5588")

    @task
    def sync_time(self):
        self.client.post("/dev/sync-time?zoneCode=5588")

    @task
    def get_manager(self):
        self.client.post("/dev/dev-list?zoneCode=5588&page=0&size=30&devTypes=1")