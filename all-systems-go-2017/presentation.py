#!/usr/bin/python

from dede import *
from demo import *

SLIDE_COUNT = 18
SLIDE_WEBUI = "webui"
SLIDE_DEMO1 = "demo1"
SLIDE_DEMO2 = "demo2"
SLIDE_DEMO3 = "demo3"
SLIDE_DEMO4 = "demo4"
SLIDE_DEMO5 = "demo5"
SLIDE_DEMO6 = "demo6"
SLIDE_DEMO7 = "demo7"
SLIDE_TERMINAL = 18


class EmbeddedTerminal(DedeTerminal):
    def __init__(self, dede, presentation):
        DedeTerminal.__init__(self, dede)
        self.presentation = presentation

    def __enter__(self):
        self.dede.driver.switch_to_default_content()
        self.presentation.goto_slide(SLIDE_TERMINAL)
        return self

    def __exit__(self, type, value, traceback):
        self.dede.driver.switch_to_frame(self.dede.driver.find_element_by_id("skydive-webui"))


class Presentation(DedeImpress):

    def __init__(self, demo):
        super(Presentation, self).__init__(demo.dede, SLIDE_COUNT)
        time.sleep(1)
        demo.director = self
        self.demo = demo
        self.driver = demo.dede.driver
        self.scenario = demo.run()
        self.window_handle = self.driver.window_handles[-1]
        self.skydive_tab = None
        self.terminal_manager = demo.dede.terminal_manager()
        self.keyboard_grab = demo.dede.keyboard_grab()
        self.keyboard_grab.install()

    def get_skydive_tab(self):
        if not self.skydive_tab:
            self.skydive_tab = DedeTab(self.dede, handle=None)
            keyboard_grab = self.dede.keyboard_grab()
            keyboard_grab.install()

        return self.skydive_tab

    def on_slide(self, slide):
        if slide.startswith("demo") and self.max_slide == self.current_slide:
            self.next_cut(1)
            with self.get_skydive_tab():
                self.scenario.next()
            self.driver.switch_to_window(self.window_handle)
            self.next_slide()
            time.sleep(1)
            self.on_slide(self.get_current_slide())

    def next_cut(self, duration):
        self.keyboard_grab.show(True)
        self.wait_for_keypress()
        self.keyboard_grab.show(False)

    def get_terminal(self, name, close=False):
        return self.terminal_manager.open_terminal_tab(name, close=close)


if __name__ == '__main__':
    demo = Demo()
    presentation = Presentation(demo)
    presentation.run()
