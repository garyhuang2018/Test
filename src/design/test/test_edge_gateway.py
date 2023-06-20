# encoding= utf-8
# __author__= gary
from locust import HttpUser, between, task
from matplotlib import pyplot as plt


from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(0, 1)

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
        self.client.get("/dev/sync-time?zoneCode=5588")

    @task
    def get_manager(self):
        self.client.get("/dev/dev-list?zoneCode=5588&page=0&size=30&devTypes=1")

    @task
    def get_data_version(self):
        self.client.get("/dev/data-version?zoneCode=5588&version=2")

    @task
    def get_indoor_upgrade(self):
        self.client.get("/dev/upgrade-check?zoneCode=5588&model=64&versionCode=60023053&packageName=com.gemvary.indoor.launcher&devCode=240079914514341d004f")

    @task
    def get_launcher_upgrade(self):
        self.client.get(
            "/dev/upgrade-check?zoneCode=5588&model=64&versionCode=61023152&packageName=com.gemvary.indoor&devCode=240079914514341d004f")