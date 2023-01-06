""" ping-graph.py: Ping latency on a graph in Python. """

__author__      = "M1sterGlass"
__copyright__   = "Copyright 2023, Planet Earth"
__version__     = "1.0.2"

import argparse
import datetime as dt
import time
import logging
import matplotlib as mpl
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from pythonping import ping
from statistics import mean

# Logging
FORMAT = '%(asctime)s | %(levelname)-8s | %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(level=logging.INFO)
# Mode
GUI_MODE = False

class Pinger:
    TIMEOUT = 2000  # 2000 default timeout (in ms)

    def __init__(self, host: str, timeout: int = TIMEOUT):
        self.host = host
        self.timeout = timeout

    def call(self) -> float:
        try:
            resp = ping(self.host, count=1, timeout=self.timeout/1000)
            rtt = resp.rtt_avg_ms
        except Exception as e:
            rtt = self.timeout

        # if timeout change rtt to 0
        if rtt >= self.timeout:
            rtt = 0
        return rtt

class Plotter:
    # Defaults
    SECONDS = 30
    INTERVAL = 200
    MAXPOINTS = 150

    # Matplotlib Graph configuration
    DARK_COLOR = 'black'
    MEDIUM_COLOR = 'grey'
    LIGHT_COLOR = 'white'
    PRIMARY_COLOR = 'green'
    SECONDARY_COLOR = 'white'
    PRI_LINE_FORMAT = '+-'
    SEC_LINE_FORMAT = ':'
    mpl.rcParams['toolbar'] = 'None'
    mpl.rcParams['figure.figsize'] = [10.0, 5.5]
    mpl.rcParams['font.size'] = '8'
    mpl.rcParams['figure.facecolor'] = DARK_COLOR
    mpl.rcParams['text.color'] = LIGHT_COLOR
    mpl.rcParams['axes.facecolor'] = DARK_COLOR
    mpl.rcParams['axes.labelcolor'] = LIGHT_COLOR
    mpl.rcParams['xtick.color'] = LIGHT_COLOR
    mpl.rcParams['ytick.color'] = LIGHT_COLOR
    mpl.rcParams['grid.color'] = MEDIUM_COLOR
    mpl.rcParams['axes.grid'] = True
    mpl.rcParams['grid.linestyle'] = ':'
    mpl.rcParams['grid.linewidth'] = '0.5'
    mpl.rcParams['lines.linewidth'] = '1'
    mpl.rcParams['legend.loc'] = 'upper left'

    def __init__(self, pinger: Pinger, seconds: int = SECONDS, interval: int = INTERVAL):
        self.pinger = pinger
        self.seconds = seconds
        self.interval = interval
        self.maxpoints = self.MAXPOINTS #int(seconds / (interval / 1000))
        self.timestamps = []
        self.rtts = []
        self.rtts_avg = []
        self.rtts_seconds = 0
        self.rtts_timeouts = 0
        self.fig, self.ax = plt.subplots()
        self.first_run = True

    def wait_for_connection(self):
        # Retry if first run is a timeout
        if self.first_run is True:
            while self.rtt == 0:
                LOGGER.warning("Waiting for connection...")
                time.sleep(1)
                self.rtt = self.pinger.call()
            LOGGER.info("Connection ok")
            self.first_run = False

    def append_list(self, listname, value):
        result = listname.append(value)
        result = listname[-self.maxpoints:]
        return result

    def calculate_runtime(self):
        self.rtts_seconds = (self.timestamps[-1] - self.timestamps[0]).total_seconds()

        # if graph seconds less then argument seconds
        if self.rtts_seconds < self.seconds:
            self.maxpoints = len(self.rtts) + 1
            LOGGER.debug(f'maxpoint adding')
        
        if self.seconds <= self.rtts_seconds <= self.seconds + 1:
            LOGGER.debug(f'maxpoint do nothing')
       
        # if graph seconds exceeds argument seconds+1 
        if self.rtts_seconds > self.seconds + 1:
            if self.maxpoints > self.seconds / 2:
                self.maxpoints = len(self.rtts) - 1
                LOGGER.debug(f'maxpoint subtract')

        LOGGER.debug(f'run {self.rtts_seconds:.2f} sec {self.seconds:.2f} max {self.maxpoints}')

    def update_data(self):
        # Ping target
        self.rtt = self.pinger.call()
        self.wait_for_connection()

        # Add timestamp to list
        self.timestamps = self.append_list(self.timestamps, dt.datetime.now())
        
        # Add rtt to list
        self.rtts = self.append_list(self.rtts, self.rtt)

        # Average from rtts list, excluding timeouts where rtt=0
        self.rtt_avg = round(mean(list(filter(lambda x: x != 0, self.rtts))), 2)
        self.rtts_avg = self.append_list(self.rtts_avg, self.rtt_avg)

        # Runtime is seconds
        self.calculate_runtime()

        # Number of timeouts, count rtts with 0
        self.rtts_timeouts = self.rtts.count(0)

        LOGGER.debug(f'rtt {self.rtt:.2f} avg {self.rtt_avg:.2f} tos {self.rtts_timeouts:.2f} pts {len(self.rtts)}')


    def render_frame(self, i: int):
        self.update_data()
        # Plot clear
        self.ax.clear()

        # Plot rtts
        self.ax.plot_date(
            self.timestamps,
            self.rtts,
            fmt = self.PRI_LINE_FORMAT,
            color = self.PRIMARY_COLOR,
            label = self.pinger.host
        )
        
        # Plot average
        self.ax.plot_date(
            self.timestamps,
            self.rtts_avg,
            fmt = self.SEC_LINE_FORMAT,
            color = self.SECONDARY_COLOR,
            label = "Average"
        )

        # Plot texts
        plt.suptitle(f'[ Average {self.rtt_avg:.2f} ms ] [ Timeouts {self.rtts_timeouts} ]')
        plt.title(f'({self.rtts_seconds:.2f} seconds / {len(self.rtts)} points) ')
        plt.ylabel(f'Round trip (milli-seconds)')
        plt.legend([self.pinger.host, 'Average'])

    def stop(self, handle):
        LOGGER.info(f'Stopped')
        plt.close('all')

    def start(self):
        LOGGER.info(f'Started')
        # Assign to variable to avoid garbage collection.
        a = animation.FuncAnimation(
            fig=self.fig,
            func=self.render_frame,
            interval=self.interval
        )
        # Close all plots on exit
        self.fig.canvas.mpl_connect("close_event", self.stop)
        plt.show()


class ArgumentReader:
   # Init parser and adding arguments
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "-t",
        dest='target',
        default='1.1.1.1', type=str,
        help = "Target hostname or IP address, default is [1.1.1.1]"
    )
    
    parser.add_argument(
        "-s",
        dest='seconds',
        default=10, type=int,
        help = "Number of seconds to display, default is [60] seconds"
    )
    parser.add_argument(
        "-i",
        dest='interval',
        default=200, type=int,
        help = "Ping interval in milli-seconds, default is [200] ms"
    )
    
    parser.add_argument(
        "-v",
        action='version',
        version='%(prog)s {version}'.format(version=__version__),
        help = "Show version"
    )
    
    # Read arguments from commandline
    arguments = parser.parse_args()

    if not arguments.target:
        gui_mode = True

if __name__ == "__main__":
    ar = ArgumentReader()
    pinger = Pinger(ar.arguments.target)
    plotter = Plotter(pinger, seconds=ar.arguments.seconds, interval=ar.arguments.interval)
    plotter.start()
