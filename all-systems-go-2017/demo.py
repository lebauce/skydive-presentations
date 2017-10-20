#!/usr/bin/python

import os
import sys
import time
import urlparse

from dede import *

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class Demo:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-infobars")
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.maximize_window()
        driver.set_script_timeout(180)

        dede = Dede("http://localhost:11664", driver, 1)

        self.dede = dede
        self.driver = driver
        self.director = self
        self.terminal_manager = self.dede.terminal_manager()

    def next_cut(self, duration):
        time.sleep(duration)

    def get_terminal(self, name, close=False):
        return self.terminal_manager.open_terminal_tab(name, close=close)

    def run(self):
        driver = self.driver
        director = self.director

        driver.execute_script("document.location = 'http://192.168.50.10:8082';")
        time.sleep(2)

        window_handle = driver.window_handles[-1]

        fake_mouse = self.dede.fake_mouse()
        fake_mouse.install()

        keyboard_grab = self.dede.keyboard_grab()
        keyboard_grab.install()

        # skydive_cli = SkydiveClient("192.168.50.10:8082")
        # skydive_sel = SkydiveSelenium(driver, skydive_cli, fake_mouse)

        with self.dede.chapter(1):

            director.next_cut(1)

            yield

        with self.dede.chapter(2):

            director.next_cut(1)

            with director.get_terminal('agent1', close=False) as agent1_tab:
                time.sleep(2)
                agent1_tab.type_cmd_wait("ssh agent1", "vagrant")
                time.sleep(1)

                agent1_tab.type_cmd_wait(
                    "sudo ip tuntap add dev tap-demo mode tap", "vagrant")

                time.sleep(2)

            director.next_cut(1)

            with director.get_terminal('agent1', close=False) as agent1_tab:
                agent1_tab.type_cmd_wait("sudo ip link set tap-demo up", "vagrant")
                time.sleep(1)

                agent1_tab.type_cmd_wait(
                    "sudo ip addr add 10.0.0.99/32 dev tap-demo", "vagrant")

                time.sleep(2)

            director.next_cut(1)
            yield

        with self.dede.chapter(3):

            director.next_cut(2)
            yield

        with self.dede.chapter(4):

            director.next_cut(2)

            with director.get_terminal('agent1', close=False) as agent1_tab:
                time.sleep(1)
                agent1_tab.type_cmd_wait(
                "docker run --name busybox -d -it busybox", "vagrant")
                time.sleep(2)

            director.next_cut(2)
            yield

        with self.dede.chapter(5):

            director.next_cut(2)

            #
            # open term to setup docker swarn
            #

            with director.get_terminal('init_swarm', close=False) as swarm_tab:
                time.sleep(2)
                swarm_tab.type_cmd(
                    "ssh agent1 \"docker swarm init --listen-addr 192.168.50.20 "
                    "--advertise-addr 192.168.50.20\"")
                time.sleep(2)

                swarm_tab.type_cmd(
                    "token=$( ssh agent1 'docker swarm join-token -q worker' )")
                time.sleep(2)

                swarm_tab.type_cmd(
                    "ssh agent2 \"docker swarm join "
                    "--token $token 192.168.50.20:2377\"")

                time.sleep(2)

            #
            # create an overlay network
            #

            with director.get_terminal('agent1', close=False) as swarm_tab:
                time.sleep(1)
                swarm_tab.type_cmd_wait(
                    "docker network create -d overlay swarmnet", "vagrant")

            director.next_cut(2)

            #
            # create the mysql container
            #

            with director.get_terminal('agent1', close=False) as swarm_tab:

                agent1_tab.type_cmd_wait(
                    "docker service create --name mysql --network swarmnet "
                    "--constraint \"node.hostname==agent1\" --publish 3306:3306 "
                    "--env=\"MYSQL_ROOT_PASSWORD=password\" mysql", "vagrant")

                time.sleep(2)

            director.next_cut(2)

            #
            # create the first wordpress
            #

            with director.get_terminal('agent1', close=False) as agent1_tab:

                agent1_tab.type_cmd_wait(
                    "docker service create --name wordpress1 --network swarmnet "
                    "--constraint \"node.hostname==agent1\" --publish 7070:80  "
                    "-e WORDPRESS_DB_HOST=mysql "
                    "-e WORDPRESS_DB_PASSWORD=password wordpress", "vagrant")

                time.sleep(2)

            director.next_cut(2)

            yield

        with self.dede.chapter(6):

            director.next_cut(2)
            yield

        with self.dede.chapter(7):

            #
            # create the second wordpress
            #

            with director.get_terminal('agent1', close=False) as agent1_tab:

                agent1_tab.type_cmd_wait(
                    "docker service create --name wordpress2 --network swarmnet "
                    "--constraint \"node.hostname==agent2\" --publish 7071:80  "
                    "-e WORDPRESS_DB_HOST=mysql "
                    "-e WORDPRESS_DB_PASSWORD=password wordpress", "vagrant")

                time.sleep(2)

            director.next_cut(2)
            yield

        with self.dede.chapter(8):

            director.next_cut(2)

            with director.get_terminal('analyzer1', close=False) as alert_tab:
                time.sleep(2)
                alert_tab.type_cmd_wait("ssh analyzer1", "vagrant")
                alert_tab.type_cmd_wait("""skydive --conf /etc/skydive/skydive.yml client alert create --action http://localhost:8000 --expression 'g.V().Has("Type", "bridge", "State", "DOWN")'""", "vagrant")
                time.sleep(1)

                with director.get_terminal('nc', close=False) as nc_tab:
                    time.sleep(1)
                    nc_tab.type_cmd_wait("ssh analyzer1", "vagrant")
                    nc_tab.type_cmd("nc -l 8000")
                    time.sleep(2)

                    with director.get_terminal('agent1', close=False) as agent1_tab:
                        time.sleep(1)
                        agent1_tab.type_cmd_wait("sudo ip link set docker0 down", "vagrant")
                        time.sleep(2)

                    director.next_cut(2)

            yield

        with self.dede.chapter(9):

            director.next_cut(2)
            yield


if __name__ == '__main__':
    demo = Demo()
    for step in demo.run():
        pass
